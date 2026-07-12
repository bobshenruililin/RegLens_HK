"""CLI entry for Stage D Cap. 599-family probe + stress."""

from __future__ import annotations

import json
from pathlib import Path

from lawtrace_worker.acquire import sha256_file
from lawtrace_worker.stage_d import (
    DEFAULT_LIMITS,
    PROBE_INSTRUMENTS,
    ensure_extracted,
    list_instrument_files,
    probe_instrument,
    score_candidate,
    stress_test_instrument,
    write_examples,
)


def main() -> None:
    raw = Path("data/lawtrace/raw")
    current_zip = raw / "hkel_c_leg_cap_301_cap_600_en.zip"
    past_zip = raw / "hkel_p_leg_cap_401_cap_600_en.zip"
    dest = Path("data/lawtrace/extracted/cap599_probe")
    reports = Path("reports/lawtrace")
    reports.mkdir(parents=True, exist_ok=True)

    extract_meta = ensure_extracted(
        current_zip=current_zip,
        past_zip=past_zip,
        dest=dest,
        instruments=PROBE_INSTRUMENTS,
    )
    archive_sha = {
        "current": sha256_file(current_zip),
        "past": sha256_file(past_zip),
    }

    probes: dict[str, dict] = {}
    matrix_rows = []
    for cap in PROBE_INSTRUMENTS:
        files = list_instrument_files(dest, cap)
        print(f"probe {cap}: {len(files)} files", flush=True)
        probe = probe_instrument(files, archive_sha_by_class=archive_sha)
        # Drop bulky comparisons from probe summary stored in matrix
        summary = {k: v for k, v in probe.items() if k != "comparisons"}
        score = score_candidate(probe)
        summary["score"] = score
        probes[cap] = {"summary": summary, "comparisons": probe["comparisons"]}
        matrix_rows.append(
            {
                "instrument": f"cap:{cap}",
                "files_available": summary["version_files_available"],
                "versions_evaluated": summary["versions_evaluated"],
                "coverage": summary["stable_id_successor_coverage"],
                "changed_pairs": summary["changed_section_pairs"],
                "ambiguous": summary["ambiguous_events"],
                "recon_rate": summary["reconstruction_success_rate"],
                "renderability": summary["renderability"],
                "unsupported": summary["unsupported_structures"],
                "elapsed_s": summary["elapsed_seconds"],
                "peak_mb": summary["tracemalloc_peak_mb"],
                "score_total": score["total"],
                "scores": score["scores"],
                "limiter": summary["limiter"],
            }
        )
        write_examples(
            probe["comparisons"],
            reports / f"stage_d_examples_cap_{cap}.md",
            f"Cap. {cap} probe examples (algorithm-generated)",
        )

    # Selection
    ranked = sorted(matrix_rows, key=lambda r: r["score_total"], reverse=True)
    # Prefer high identity+recon+fidelity for showcase; highest churn among trustworthy for stress
    trustworthy = [
        r
        for r in ranked
        if (r["coverage"] or 0) >= 0.99
        and (r["recon_rate"] or 0) >= 1.0
        and r["ambiguous"] == 0
    ]
    showcase = trustworthy[0] if trustworthy else ranked[0]
    # Stress: among trustworthy, maximize changed_pairs * versions but keep manageable
    stress_pool = trustworthy or ranked
    stress = max(
        stress_pool,
        key=lambda r: (r["changed_pairs"], r["versions_evaluated"], r["score_total"]),
    )

    # Full stress on selected instrument
    stress_cap = showcase["instrument"].split(":")[1]  # may override below
    stress_cap = stress["instrument"].split(":")[1]
    showcase_cap = showcase["instrument"].split(":")[1]
    files = list_instrument_files(dest, stress_cap)
    print(f"stress {stress_cap}: available={len(files)}", flush=True)
    stress_result = stress_test_instrument(files, archive_sha_by_class=archive_sha)
    stress_summary = {k: v for k, v in stress_result.items() if k != "comparisons"}

    # If showcase differs, also note
    selection = {
        "technical_stress_test_instrument": stress["instrument"],
        "recommended_public_showcase_instrument": showcase["instrument"],
        "same_instrument": stress["instrument"] == showcase["instrument"],
        "rationale": {
            "showcase": "Highest composite score among instruments with ≥99% @id coverage, 100% reconstruction, zero ambiguous events.",
            "stress": "Among trustworthy probes, maximize changed-section pairs and version span under documented limiters.",
            "not_selected_by_version_count_alone": True,
        },
    }

    out = {
        "disclaimer": (
            "LawTrace output is a transformation of official open data and is not a verified copy."
        ),
        "extract_meta": extract_meta,
        "limits": {
            "max_versions_probe": DEFAULT_LIMITS.max_versions_probe,
            "max_versions_stress": DEFAULT_LIMITS.max_versions_stress,
            "max_changed_pairs_target": DEFAULT_LIMITS.max_changed_pairs_target,
        },
        "candidate_matrix": matrix_rows,
        "selection": selection,
        "stress_summary": stress_summary,
        "gold_note": "No Cap. 599 comparisons are human-confirmed gold; algorithm-generated only.",
    }
    (reports / "stage_d_result.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports / "stage_d_stress_comparisons.jsonl").write_text(
        "".join(
            json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n"
            for c in stress_result["comparisons"]
        ),
        encoding="utf-8",
    )
    # Matrix markdown
    md = [
        "# Stage D — Cap. 599-family candidate matrix",
        "",
        out["disclaimer"],
        "",
        "## Limiters",
        "",
        f"- Probe max versions/instrument: {DEFAULT_LIMITS.max_versions_probe}",
        f"- Stress max versions: {DEFAULT_LIMITS.max_versions_stress}",
        f"- Changed-pair target: ≥{DEFAULT_LIMITS.max_changed_pairs_target} if available",
        "",
        "## Matrix",
        "",
        "| Instrument | Files | Eval versions | @id coverage | Changed | Ambiguous | Recon | Score |",
        "|------------|------:|--------------:|-------------:|--------:|----------:|------:|------:|",
    ]
    for r in ranked:
        md.append(
            f"| {r['instrument']} | {r['files_available']} | {r['versions_evaluated']} | "
            f"{r['coverage']:.4f} | {r['changed_pairs']} | {r['ambiguous']} | "
            f"{r['recon_rate']} | {r['score_total']} |"
        )
    md += [
        "",
        "## Selection",
        "",
        f"- Technical stress-test: **{selection['technical_stress_test_instrument']}**",
        f"- Recommended showcase: **{selection['recommended_public_showcase_instrument']}**",
        f"- Stress pass: **{stress_summary.get('stress_pass')}**",
        f"- Stress changed pairs: {stress_summary.get('evaluation_set', {}).get('changed_pairs')}",
        f"- Stress reconstruction: {stress_summary.get('reconstruction_ok')}/{stress_summary.get('reconstruction_total')}",
        "",
        "Comparisons are algorithm-generated / not human-confirmed gold.",
        "",
    ]
    (reports / "stage_d_result.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    write_examples(
        stress_result["comparisons"],
        reports / "stage_d_stress_examples.md",
        f"Stress examples — {selection['technical_stress_test_instrument']}",
    )
    print(json.dumps({k: out[k] for k in out if k != "extract_meta"}, indent=2)[:4000])


if __name__ == "__main__":
    main()
