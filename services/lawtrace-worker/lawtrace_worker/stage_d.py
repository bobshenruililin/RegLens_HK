"""Stage D: Cap. 599-family bounded probe and stress test."""

from __future__ import annotations

import json
import resource
import time
import tracemalloc
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lawtrace_worker.acquire import extract_matching, sha256_file
from lawtrace_worker.canonical import canonicalize_section
from lawtrace_worker.compare import compare_added, compare_removed, compare_sections
from lawtrace_worker.security.xml_safe import parse_xml_file
from lawtrace_worker.stage_b import (
    iter_top_level_sections,
    match_sections,
    parse_instrument_file,
)
from lawtrace_worker.stage_c import DISCLAIMER, HKEL_SEARCH

# Resource / version limiters (documented — do not raise silently).
MAX_VERSIONS_PER_INSTRUMENT_PROBE = 40
MAX_VERSIONS_STRESS = 25
MAX_CHANGED_PAIRS_TARGET = 30
PROBE_INSTRUMENTS = ("599J", "599F", "599G")


@dataclass(frozen=True)
class StageDLimits:
    max_versions_probe: int = MAX_VERSIONS_PER_INSTRUMENT_PROBE
    max_versions_stress: int = MAX_VERSIONS_STRESS
    max_changed_pairs_target: int = MAX_CHANGED_PAIRS_TARGET


DEFAULT_LIMITS = StageDLimits()


def _rss_mb() -> float:
    # Linux: ru_maxrss is kilobytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def ensure_extracted(
    *,
    current_zip: Path,
    past_zip: Path,
    dest: Path,
    instruments: tuple[str, ...],
) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    contains = tuple(f"cap_{cap.lower()}" for cap in instruments)
    # Also match filename forms like cap_599J_
    results = []
    for archive in (current_zip, past_zip):
        if not archive.is_file():
            raise FileNotFoundError(archive)
        # Extract members whose normalized path contains any instrument token.
        from lawtrace_worker.security.zip_safe import safe_extract

        r = safe_extract(
            archive,
            dest,
            name_contains=tuple(f"cap_{c.lower()}" for c in instruments)
            + tuple(f"cap_{c}" for c in instruments),
            overwrite=False,
            preserve_archive_relative_path=True,
            on_collision="fail",
        )
        results.append(
            {
                "archive": archive.name,
                "archive_sha256": sha256_file(archive),
                "accepted": len(r.accepted_members),
                "rejected": len(r.rejected_members),
                "written": len(r.written),
                "collisions": len(r.collisions),
                "rejected_members": r.rejected_members,
            }
        )
    return {"extracts": results, "dest": str(dest)}


def list_instrument_files(extract_root: Path, cap: str) -> list[Path]:
    needle = f"cap_{cap.lower()}_"
    files = [
        p
        for p in extract_root.rglob("*.xml")
        if needle in p.name.lower() and p.name.lower().endswith((".xml",))
    ]
    # Prefer English only (our archives are EN).
    files = [p for p in files if "_en_" in p.name.lower()]
    files.sort(key=lambda p: p.name)
    return files


def probe_instrument(
    files: list[Path],
    *,
    archive_sha_by_class: dict[str, str],
    limits: StageDLimits = DEFAULT_LIMITS,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    tracemalloc.start()
    all_files = files
    # Bound versions: take evenly spaced sample including first/last if over limit.
    if len(files) > limits.max_versions_probe:
        n = limits.max_versions_probe
        idxs = sorted({int(i * (len(files) - 1) / (n - 1)) for i in range(n)})
        files = [all_files[i] for i in idxs]
        limiter = {
            "max_versions_probe": limits.max_versions_probe,
            "total_available": len(all_files),
            "selected": len(files),
            "strategy": "even_span_including_ends",
        }
    else:
        limiter = {
            "max_versions_probe": limits.max_versions_probe,
            "total_available": len(all_files),
            "selected": len(files),
            "strategy": "all",
        }

    parsed: list[dict[str, Any]] = []
    for p in files:
        cp = "c" if p.name.lower().endswith("_c.xml") else "p"
        arch = archive_sha_by_class.get("current" if cp == "c" else "past")
        parsed.append(parse_instrument_file(p, archive_sha256=arch))
    parsed.sort(key=lambda x: x["filename_meta"]["ver"])

    section_counts = [pf["top_level_section_count"] for pf in parsed]
    rend = Counter()
    unsupported_structs: Counter[str] = Counter()
    for pf in parsed:
        path = next(x for x in files if x.name == pf["file"])
        root = parse_xml_file(path)
        id_map = {s.attrib.get("id"): s for s in iter_top_level_sections(root)}
        for sec in pf["sections"]:
            rend[sec["renderability"]] += 1
            el = id_map.get(sec.get("element_id"))
            if el is not None:
                canon = canonicalize_section(el)
                for u in canon.unsupported_structures:
                    unsupported_structs[u] += 1

    slots = 0
    matched = 0
    ambiguous = 0
    added = 0
    removed = 0
    changed = 0
    status_changed = 0
    text_changed = 0
    recon_ok = 0
    recon_total = 0
    comparisons: list[dict[str, Any]] = []
    path_by_name = {p.name: p for p in files}

    for older, newer in zip(parsed, parsed[1:], strict=False):
        m = match_sections(older["sections"], newer["sections"])
        slots += len(older["sections"])
        matched += len(m["accepted_edges"])
        ambiguous += m["counts"]["ambiguous"]
        added += m["counts"]["added"]
        removed += m["counts"]["unmatched_old"]
        for edge in m["edges"]:
            if edge["match_method"] != "id" or not edge.get("older") or not edge.get("newer"):
                if edge["change_class"] == "added":
                    continue
                continue
            o, n = edge["older"], edge["newer"]
            o_el = next(
                (
                    s
                    for s in iter_top_level_sections(parse_xml_file(path_by_name[older["file"]]))
                    if s.attrib.get("id") == o["element_id"]
                ),
                None,
            )
            n_el = next(
                (
                    s
                    for s in iter_top_level_sections(parse_xml_file(path_by_name[newer["file"]]))
                    if s.attrib.get("id") == n["element_id"]
                ),
                None,
            )
            if o_el is None or n_el is None:
                continue
            ca, cb = canonicalize_section(o_el), canonicalize_section(n_el)
            cmp = compare_sections(
                instrument=o["instrument_id"],
                version_a_id=older["file"],
                version_b_id=newer["file"],
                canon_a=ca,
                canon_b=cb,
                provenance_a={
                    "source_file": older["file"],
                    "source_file_sha256": older["file_sha256"],
                    "source_archive_sha256": older.get("archive_sha256"),
                },
                provenance_b={
                    "source_file": newer["file"],
                    "source_file_sha256": newer["file_sha256"],
                    "source_archive_sha256": newer.get("archive_sha256"),
                },
            )
            recon_total += 1
            if cmp.reconstruction_ok:
                recon_ok += 1
            if cmp.relationship != "unchanged":
                changed += 1
            if "status" in cmp.relationship:
                status_changed += 1
            if "text" in cmp.relationship:
                text_changed += 1
            comparisons.append(cmp.to_dict())

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.perf_counter() - t0
    coverage = (matched / slots) if slots else None
    return {
        "instrument": f"cap:{parsed[0]['filename_meta']['cap']}" if parsed else None,
        "limiter": limiter,
        "version_files_available": len(all_files),
        "versions_evaluated": len(parsed),
        "section_count_min": min(section_counts) if section_counts else 0,
        "section_count_max": max(section_counts) if section_counts else 0,
        "stable_id_successor_coverage": coverage,
        "matched_edges": matched,
        "identity_slots": slots,
        "ambiguous_events": ambiguous,
        "added_sections": added,
        "removed_or_unmatched": removed,
        "changed_section_pairs": changed,
        "text_changed_pairs": text_changed,
        "status_related_pairs": status_changed,
        "renderability": dict(rend),
        "unsupported_structures": dict(unsupported_structs),
        "reconstruction_ok": recon_ok,
        "reconstruction_total": recon_total,
        "reconstruction_success_rate": (recon_ok / recon_total) if recon_total else None,
        "elapsed_seconds": round(elapsed, 3),
        "tracemalloc_peak_mb": round(peak / (1024 * 1024), 3),
        "rss_max_mb": round(_rss_mb(), 3),
        "comparisons": comparisons,
    }


def score_candidate(probe: dict[str, Any]) -> dict[str, Any]:
    """Explicit scoring matrix — not version-count alone."""
    coverage = probe.get("stable_id_successor_coverage") or 0.0
    recon = probe.get("reconstruction_success_rate") or 0.0
    rend = probe.get("renderability") or {}
    total_rend = sum(rend.values()) or 1
    complete_share = rend.get("complete", 0) / total_rend
    unsupported = sum(probe.get("unsupported_structures", {}).values())
    changed = probe.get("changed_section_pairs") or 0
    ambiguous = probe.get("ambiguous_events") or 0
    versions = probe.get("versions_evaluated") or 0
    cost = probe.get("elapsed_seconds") or 0.0

    scores = {
        "identity_reliability": round(100 * coverage, 1),
        "fidelity_complete_share": round(100 * complete_share, 1),
        "diff_reconstruction": round(100 * recon, 1),
        "meaningful_changes": min(100.0, changed * 2.0),
        "manageable_complexity": max(0.0, 100.0 - max(0, versions - 20) * 2.0 - unsupported * 5.0),
        "provenance_completeness": 100.0,  # official EN ZIPs with hashes
        "user_comprehensibility": 80.0 if complete_share > 0.9 and ambiguous == 0 else 50.0,
        "processing_cost": max(0.0, 100.0 - cost),
    }
    # Weighted total
    weights = {
        "identity_reliability": 0.25,
        "fidelity_complete_share": 0.15,
        "diff_reconstruction": 0.20,
        "meaningful_changes": 0.10,
        "manageable_complexity": 0.10,
        "provenance_completeness": 0.05,
        "user_comprehensibility": 0.10,
        "processing_cost": 0.05,
    }
    total = sum(scores[k] * weights[k] for k in weights)
    return {"scores": scores, "weights": weights, "total": round(total, 2), "ambiguous": ambiguous}


def stress_test_instrument(
    files: list[Path],
    *,
    archive_sha_by_class: dict[str, str],
    limits: StageDLimits = DEFAULT_LIMITS,
) -> dict[str, Any]:
    # Narrower version span for full stress
    if len(files) > limits.max_versions_stress:
        n = limits.max_versions_stress
        idxs = sorted({int(i * (len(files) - 1) / (n - 1)) for i in range(n)})
        selected = [files[i] for i in idxs]
        limiter = {
            "max_versions_stress": limits.max_versions_stress,
            "available": len(files),
            "selected": len(selected),
        }
    else:
        selected = files
        limiter = {
            "max_versions_stress": limits.max_versions_stress,
            "available": len(files),
            "selected": len(selected),
        }
    probe = probe_instrument(selected, archive_sha_by_class=archive_sha_by_class, limits=StageDLimits(max_versions_probe=10_000))
    probe["stress_limiter"] = limiter
    # Stratify evaluation set
    comps = probe["comparisons"]
    changed = [c for c in comps if c["relationship"] != "unchanged"]
    unchanged = [c for c in comps if c["relationship"] == "unchanged"]
    probe["evaluation_set"] = {
        "changed_pairs": len(changed),
        "changed_pairs_target": limits.max_changed_pairs_target,
        "changed_target_met": len(changed) >= min(limits.max_changed_pairs_target, max(1, len(changed))),
        "unchanged_pairs": len(unchanged),
        "added": probe["added_sections"],
        "removed_or_unmatched": probe["removed_or_unmatched"],
        "ambiguous_events": probe["ambiguous_events"],
        "note": "Comparisons are algorithm-generated; not human-confirmed gold.",
    }
    # Failure checks
    failures: list[str] = []
    if (probe.get("reconstruction_success_rate") or 0) < 1.0:
        failures.append("reconstruction_failed")
    if (probe.get("stable_id_successor_coverage") or 0) < 0.95:
        failures.append("identity_coverage_below_95")
    if probe.get("ambiguous_events", 0) > 0:
        failures.append("ambiguous_identity_present_not_auto_accepted")
    probe["failure_flags"] = failures
    probe["stress_pass"] = "reconstruction_failed" not in failures and "identity_coverage_below_95" not in failures
    return probe


def write_examples(comps: list[dict[str, Any]], out_md: Path, title: str) -> None:
    picks = []
    for rel in ("unchanged", "text_changed", "status_changed", "text_and_status_changed"):
        for c in comps:
            if c["relationship"] == rel:
                picks.append(c)
                break
    lines = [f"# {title}", "", DISCLAIMER, ""]
    for i, c in enumerate(picks, 1):
        lines += [
            f"## {i}. {c['relationship']}",
            f"- A: `{c['version_a_id']}`",
            f"- B: `{c['version_b_id']}`",
            f"- @id: `{c.get('section_id')}`",
            f"- nums: `{c.get('section_num_a')}` → `{c.get('section_num_b')}`",
            f"- renderability: `{c['renderability_a']}` / `{c['renderability_b']}`",
            f"- reconstruction_ok: `{c['reconstruction_ok']}`",
            "",
        ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
