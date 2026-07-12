"""Stage C runner: Cap. 614 consecutive same-ID comparisons + evidence packet."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from lawtrace_worker.canonical import canonicalize_section
from lawtrace_worker.compare import (
    COMPARATOR_VERSION,
    compare_added,
    compare_removed,
    compare_sections,
    highlight_ops,
)
from lawtrace_worker.security.xml_safe import parse_xml_file
from lawtrace_worker.stage_b import (
    iter_top_level_sections,
    match_sections,
    parse_instrument_file,
    sha256_bytes,
)

DISCLAIMER = (
    "LawTrace displays transformations of open data obtained through DATA.GOV.HK. "
    "This comparison shows differences between two official open-data XML versions "
    "of a legislative section. It does not claim that displayed text was the law in "
    "force on a selected date, that version dates are commencement or effective dates, "
    "that LawTrace output is a verified copy, or that an automatically matched "
    "structural event is legally conclusive. For an official verified copy, consult "
    "Hong Kong e-Legislation (HKeL)."
)

HKEL_SEARCH = "https://www.elegislation.gov.hk/"


def _load_versions(fixture_dir: Path, archive_sha256: str | None) -> list[dict[str, Any]]:
    paths = sorted(fixture_dir.glob("*.xml"))
    parsed = [parse_instrument_file(p, archive_sha256=archive_sha256) for p in paths]
    parsed.sort(key=lambda x: x["filename_meta"]["ver"])
    return parsed


def _section_element_by_id(path: Path, element_id: str):
    root = parse_xml_file(path)
    for sec in iter_top_level_sections(root):
        if sec.attrib.get("id") == element_id:
            return sec
    return None


def _provenance(parsed: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": parsed["file"],
        "source_file_sha256": parsed["file_sha256"],
        "source_archive_sha256": parsed.get("archive_sha256"),
        "source_version_datetime": section.get("source_version_datetime")
        or parsed["filename_meta"]["ver"],
        "element_id": section.get("element_id"),
        "temporal_id": section.get("temporal_id"),
        "canonical_xpath": section.get("canonical_xpath"),
        "xml_fragment_sha256": section.get("xml_fragment_sha256"),
        "parser_version": section.get("parser_version"),
        "normalization_version": section.get("normalization_version"),
        "official_portal": HKEL_SEARCH,
        "dataset_note": "DATA.GOV.HK HKeL legislation XML (English)",
    }


def evaluate_cap_614(
    fixture_dir: Path,
    *,
    archive_sha256: str | None = "fixture-local",
) -> dict[str, Any]:
    t0 = time.perf_counter()
    versions = _load_versions(fixture_dir, archive_sha256)
    comparisons: list[dict[str, Any]] = []
    relationship_counts: Counter[str] = Counter()
    renderability: Counter[str] = Counter()
    reconstruction_failures: list[dict[str, Any]] = []
    supported_pairs = 0
    supported_ok = 0

    path_by_name = {p.name: p for p in fixture_dir.glob("*.xml")}

    for older, newer in zip(versions, versions[1:], strict=False):
        matched = match_sections(older["sections"], newer["sections"])
        # Same-ID accepted edges
        for edge in matched["edges"]:
            cls = edge["change_class"]
            if edge["match_method"] == "id" and edge.get("older") and edge.get("newer"):
                o, n = edge["older"], edge["newer"]
                o_el = _section_element_by_id(path_by_name[older["file"]], o["element_id"])
                n_el = _section_element_by_id(path_by_name[newer["file"]], n["element_id"])
                if o_el is None or n_el is None:
                    reconstruction_failures.append(
                        {
                            "reason": "section_element_not_found",
                            "older": older["file"],
                            "newer": newer["file"],
                            "id": o.get("element_id"),
                        }
                    )
                    continue
                ca = canonicalize_section(o_el)
                cb = canonicalize_section(n_el)
                renderability[ca.renderability] += 1
                renderability[cb.renderability] += 1
                cmp = compare_sections(
                    instrument=o["instrument_id"],
                    version_a_id=older["file"],
                    version_b_id=newer["file"],
                    canon_a=ca,
                    canon_b=cb,
                    provenance_a=_provenance(older, o),
                    provenance_b=_provenance(newer, n),
                )
                row = cmp.to_dict()
                row["artifact_sha256"] = cmp.artifact_sha256()
                row["stage_b_change_class"] = cls
                row["match_method"] = edge["match_method"]
                comparisons.append(row)
                relationship_counts[cmp.relationship] += 1
                if cmp.relationship_supported and cmp.ordinary_redline_supported:
                    supported_pairs += 1
                    if cmp.reconstruction_ok:
                        supported_ok += 1
                    else:
                        reconstruction_failures.append(
                            {
                                "reason": "reconstruction_mismatch",
                                "id": cmp.section_id,
                                "a": older["file"],
                                "b": newer["file"],
                            }
                        )
                elif cmp.relationship_supported:
                    # Still require reconstruction for supported relationships even if
                    # ordinary redline is limited.
                    supported_pairs += 1
                    if cmp.reconstruction_ok:
                        supported_ok += 1
                    else:
                        reconstruction_failures.append(
                            {
                                "reason": "reconstruction_mismatch_limited",
                                "id": cmp.section_id,
                                "a": older["file"],
                                "b": newer["file"],
                            }
                        )
            elif cls == "added" and edge.get("newer"):
                n = edge["newer"]
                n_el = _section_element_by_id(path_by_name[newer["file"]], n["element_id"])
                if n_el is None:
                    continue
                cb = canonicalize_section(n_el)
                cmp = compare_added(
                    instrument=n["instrument_id"],
                    version_a_id=older["file"],
                    version_b_id=newer["file"],
                    canon_b=cb,
                    provenance_b=_provenance(newer, n),
                )
                row = cmp.to_dict()
                row["artifact_sha256"] = cmp.artifact_sha256()
                row["stage_b_change_class"] = cls
                row["match_method"] = edge["match_method"]
                comparisons.append(row)
                relationship_counts[cmp.relationship] += 1
            elif cls in {"removed_or_unmatched"} and edge.get("older"):
                o = edge["older"]
                o_el = _section_element_by_id(path_by_name[older["file"]], o["element_id"])
                if o_el is None:
                    continue
                ca = canonicalize_section(o_el)
                cmp = compare_removed(
                    instrument=o["instrument_id"],
                    version_a_id=older["file"],
                    version_b_id=newer["file"],
                    canon_a=ca,
                    provenance_a=_provenance(older, o),
                )
                row = cmp.to_dict()
                row["artifact_sha256"] = cmp.artifact_sha256()
                row["stage_b_change_class"] = cls
                row["match_method"] = edge["match_method"]
                comparisons.append(row)
                relationship_counts[cmp.relationship] += 1

    elapsed = time.perf_counter() - t0
    gate_pass = (
        supported_pairs > 0
        and supported_ok == supported_pairs
        and len(reconstruction_failures) == 0
    )
    return {
        "instrument": "cap:614",
        "comparator_version": COMPARATOR_VERSION,
        "version_count": len(versions),
        "comparison_count": len(comparisons),
        "relationship_counts": dict(relationship_counts),
        "renderability_counts": dict(renderability),
        "supported_pairs": supported_pairs,
        "supported_reconstruction_ok": supported_ok,
        "reconstruction_success_rate": (
            supported_ok / supported_pairs if supported_pairs else None
        ),
        "reconstruction_failures": reconstruction_failures,
        "gate_pass": gate_pass,
        "elapsed_seconds": round(elapsed, 3),
        "comparisons": comparisons,
        "disclaimer": DISCLAIMER,
    }


def determinism_check(fixture_dir: Path) -> dict[str, Any]:
    run1 = evaluate_cap_614(fixture_dir)
    run2 = evaluate_cap_614(fixture_dir)
    keys = [
        "relationship_counts",
        "renderability_counts",
        "supported_pairs",
        "supported_reconstruction_ok",
        "gate_pass",
    ]
    summary_equal = all(run1[k] == run2[k] for k in keys)
    hashes1 = [c["artifact_sha256"] for c in run1["comparisons"]]
    hashes2 = [c["artifact_sha256"] for c in run2["comparisons"]]
    canon_hashes1 = [
        (c["canonical_a"]["canonical_sha256"], c["canonical_b"]["canonical_sha256"])
        for c in run1["comparisons"]
        if c["relationship"] not in {"added", "removed"}
    ]
    canon_hashes2 = [
        (c["canonical_a"]["canonical_sha256"], c["canonical_b"]["canonical_sha256"])
        for c in run2["comparisons"]
        if c["relationship"] not in {"added", "removed"}
    ]
    ops1 = [c["full_token_diff"]["operations"] for c in run1["comparisons"]]
    ops2 = [c["full_token_diff"]["operations"] for c in run2["comparisons"]]
    return {
        "summary_equal": summary_equal,
        "artifact_hashes_equal": hashes1 == hashes2,
        "canonical_hashes_equal": canon_hashes1 == canon_hashes2,
        "diff_ops_equal": ops1 == ops2,
        "classifications_equal": [c["relationship"] for c in run1["comparisons"]]
        == [c["relationship"] for c in run2["comparisons"]],
        "pass": summary_equal
        and hashes1 == hashes2
        and canon_hashes1 == canon_hashes2
        and ops1 == ops2,
        "comparison_count": len(hashes1),
    }


def _pick_examples(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def first(rel: str, n: int = 1) -> list[dict[str, Any]]:
        return [c for c in comparisons if c["relationship"] == rel][:n]

    picks: list[dict[str, Any]] = []
    picks.extend(first("unchanged", 1))
    picks.extend(first("text_changed", 5))
    picks.extend(first("status_changed", 1))
    picks.extend(first("text_and_status_changed", 1))
    picks.extend(first("added", 1))
    # limitation example if any
    limited = [c for c in comparisons if c.get("limitation") and c["relationship"] != "unchanged"]
    if limited:
        picks.append(limited[0])
    elif any(c["renderability_a"] != "complete" or c["renderability_b"] != "complete" for c in comparisons):
        picks.append(
            next(
                c
                for c in comparisons
                if c["renderability_a"] != "complete" or c["renderability_b"] != "complete"
            )
        )
    # de-dupe by artifact hash
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for p in picks:
        h = p["artifact_sha256"]
        if h not in seen:
            seen.add(h)
            unique.append(p)
    return unique


def write_evidence_packet(result: dict[str, Any], out_md: Path, out_html: Path) -> None:
    examples = _pick_examples(result["comparisons"])
    lines: list[str] = []
    lines.append("# Cap. 614 Stage C comparison evidence packet")
    lines.append("")
    lines.append(f"**Status:** Local non-production evidence for Stage C. {DISCLAIMER}")
    lines.append("")
    lines.append(f"- Comparator: `{COMPARATOR_VERSION}`")
    lines.append(f"- Comparisons evaluated: {result['comparison_count']}")
    lines.append(f"- Supported reconstruction: {result['supported_reconstruction_ok']}/{result['supported_pairs']}")
    lines.append(f"- Gate pass: **{result['gate_pass']}**")
    lines.append("")
    for i, ex in enumerate(examples, 1):
        lines.append(f"## Example {i}: `{ex['relationship']}`")
        lines.append("")
        lines.append(f"- Instrument: `{ex['instrument']}`")
        lines.append(f"- Version A: `{ex['version_a_id']}`")
        lines.append(f"- Version B: `{ex['version_b_id']}`")
        lines.append(f"- Section @id: `{ex.get('section_id')}`")
        lines.append(f"- Section number A→B: `{ex.get('section_num_a')}` → `{ex.get('section_num_b')}`")
        lines.append(f"- Renderability A/B: `{ex['renderability_a']}` / `{ex['renderability_b']}`")
        lines.append(f"- Ordinary redline supported: `{ex['ordinary_redline_supported']}`")
        lines.append(f"- Limitation: `{ex.get('limitation')}`")
        lines.append(f"- Reconstruction OK: `{ex['reconstruction_ok']}`")
        lines.append(f"- Provenance A file sha256: `{ex['provenance_a'].get('source_file_sha256')}`")
        lines.append(f"- Provenance B file sha256: `{ex['provenance_b'].get('source_file_sha256')}`")
        lines.append(f"- Official portal: {HKEL_SEARCH}")
        lines.append("")
        lines.append("### Canonical A (token preview)")
        lines.append("")
        lines.append("```")
        for t in ex["canonical_a"]["tokens"][:80]:
            lines.append(f"{t['kind']}|{t.get('text','')[:200]}")
        if len(ex["canonical_a"]["tokens"]) > 80:
            lines.append("...")
        lines.append("```")
        lines.append("")
        lines.append("### Canonical B (token preview)")
        lines.append("")
        lines.append("```")
        for t in ex["canonical_b"]["tokens"][:80]:
            lines.append(f"{t['kind']}|{t.get('text','')[:200]}")
        if len(ex["canonical_b"]["tokens"]) > 80:
            lines.append("...")
        lines.append("```")
        lines.append("")
        lines.append("### Highlighted legal-text changes")
        lines.append("")
        lines.append("```diff")
        for hl in highlight_ops(ex["legal_text_diff"]["operations"]):
            lines.append(hl)
        if not ex["legal_text_diff"]["operations"]:
            lines.append("(no legal-text token operations)")
        lines.append("```")
        lines.append("")
        lines.append("### Metadata/status channel")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(ex["metadata_diff"]["operations"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    out_md.write_text(text, encoding="utf-8")
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<title>Cap. 614 Stage C Evidence</title>"
        "<style>body{font-family:Georgia,serif;max-width:980px;margin:2rem auto;padding:0 1rem;}"
        ".banner{background:#fff3cd;border:1px solid #ffecb5;padding:.75rem;margin-bottom:1rem;}"
        "pre{white-space:pre-wrap;background:#f7f7f7;padding:.75rem;}</style></head><body>"
        f"<div class='banner'><strong>Informational only.</strong> {DISCLAIMER}</div>"
        f"<pre>{_html_escape(text)}</pre></body></html>"
    )
    out_html.write_text(html, encoding="utf-8")


def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_stage_c_reports(result: dict[str, Any], det: dict[str, Any], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in result.items() if k != "comparisons"}
    slim["determinism"] = det
    (reports_dir / "stage_c_result.json").write_text(
        json.dumps(slim, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Full comparisons (may be large)
    (reports_dir / "stage_c_comparisons.jsonl").write_text(
        "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in result["comparisons"]),
        encoding="utf-8",
    )
    md = [
        "# Stage C result — Cap. 614 deterministic section comparison",
        "",
        f"**Gate:** {'PASS' if result['gate_pass'] and det['pass'] else 'FAIL'}",
        "",
        DISCLAIMER,
        "",
        "## Metrics",
        "",
        f"- Versions: {result['version_count']}",
        f"- Comparisons: {result['comparison_count']}",
        f"- Relationships: `{json.dumps(result['relationship_counts'])}`",
        f"- Renderability observations: `{json.dumps(result['renderability_counts'])}`",
        f"- Supported reconstruction: {result['supported_reconstruction_ok']}/{result['supported_pairs']} ({result['reconstruction_success_rate']})",
        f"- Determinism pass: {det['pass']}",
        f"- Elapsed seconds: {result['elapsed_seconds']}",
        f"- Comparator: `{COMPARATOR_VERSION}`",
        "",
        "## Product claim (locked)",
        "",
        "> Compare two official open-data versions of a Hong Kong legislative section and inspect what changed.",
        "",
        "## Evidence packet",
        "",
        "- `reports/lawtrace/stage_c_evidence_packet.md`",
        "- `reports/lawtrace/stage_c_evidence_packet.html`",
        "",
    ]
    (reports_dir / "stage_c_result.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    write_evidence_packet(
        result,
        reports_dir / "stage_c_evidence_packet.md",
        reports_dir / "stage_c_evidence_packet.html",
    )


def main() -> None:
    fixture = Path("fixtures/lawtrace/cap_614")
    reports = Path("reports/lawtrace")
    result = evaluate_cap_614(fixture)
    det = determinism_check(fixture)
    write_stage_c_reports(result, det, reports)
    print(json.dumps({k: result[k] for k in result if k != "comparisons"} | {"determinism": det}, indent=2))


if __name__ == "__main__":
    main()
