"""Deterministic LawTrace web-data export (MVP).

Writes chunked JSON under a target directory for the read-only app.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lawtrace_worker import NORMALIZATION_VERSION, PARSER_VERSION
from lawtrace_worker.canonical import canonicalize_section
from lawtrace_worker.compare import COMPARATOR_VERSION, compare_sections, highlight_ops
from lawtrace_worker.security.xml_safe import parse_xml_file
from lawtrace_worker.stage_b import (
    iter_top_level_sections,
    match_sections,
    parse_instrument_file,
)
from lawtrace_worker.stage_c import DISCLAIMER, HKEL_SEARCH

EXPORT_SCHEMA_VERSION = "lawtrace-web/1.0.0"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump_json(path: Path, obj: Any, *, deterministic: bool = True) -> str:
    """Write JSON; return content hash excluding generation_timestamp fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    if deterministic:
        scrubbed = _strip_timestamps(obj)
        return sha256_text(
            json.dumps(scrubbed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    return sha256_text(text)


def _strip_timestamps(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: _strip_timestamps(v)
            for k, v in obj.items()
            if k not in {"generation_timestamp", "generated_at"}
        }
    if isinstance(obj, list):
        return [_strip_timestamps(x) for x in obj]
    return obj


def format_snapshot_label(ver: str) -> str:
    """Official open-data snapshot dated YYYY-MM-DD (from yyyymmddhhmiss)."""
    if not ver or ver.startswith("-") or len(ver) < 8:
        return "Official open-data snapshot (undated)"
    y, m, d = ver[0:4], ver[4:6], ver[6:8]
    return f"Official open-data snapshot dated {y}-{m}-{d}"


def _section_el(path: Path, element_id: str):
    root = parse_xml_file(path)
    for sec in iter_top_level_sections(root):
        if sec.attrib.get("id") == element_id:
            return sec
    return None


def _plain_text_from_canon(tokens: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for t in tokens:
        kind = t["kind"]
        text = t.get("text") or ""
        if kind.endswith("_OPEN") or kind.endswith("_CLOSE") or kind in {
            "SECTION_OPEN",
            "SECTION_CLOSE",
        }:
            continue
        if text:
            parts.append(text)
    return "\n".join(parts)


def export_instrument(
    *,
    instrument_id: str,
    title: str,
    fixture_or_extract_dir: Path,
    out_dir: Path,
    dataset_mode: str,
    archive_sha256: str | None,
    sampling: dict[str, Any] | None = None,
    max_versions: int | None = None,
) -> dict[str, Any]:
    paths = sorted(
        p
        for p in fixture_or_extract_dir.rglob("*.xml")
        if instrument_id.replace("cap:", "cap_").lower() in p.name.lower()
        and "_en_" in p.name.lower()
    )
    # Cap. 614 fixtures live flat without nested dirs matching
    if not paths and fixture_or_extract_dir.is_dir():
        paths = sorted(fixture_or_extract_dir.glob("*.xml"))

    total_available = len(paths)
    sampling_info = {
        "complete": True,
        "total_available_versions": total_available,
        "versions_included": total_available,
        "strategy": "all",
        "limiter": None,
    }
    if max_versions is not None and total_available > max_versions:
        idxs = sorted({int(i * (total_available - 1) / (max_versions - 1)) for i in range(max_versions)})
        paths = [paths[i] for i in idxs]
        sampling_info = {
            "complete": False,
            "total_available_versions": total_available,
            "versions_included": len(paths),
            "strategy": "even_span_including_ends",
            "limiter": {"max_versions": max_versions},
        }
    if sampling:
        sampling_info.update(sampling)

    parsed = [parse_instrument_file(p, archive_sha256=archive_sha256) for p in paths]
    parsed.sort(key=lambda x: x["filename_meta"]["ver"])
    path_by_name = {p.name: p for p in paths}

    versions = []
    for pf in parsed:
        ver = pf["filename_meta"]["ver"]
        versions.append(
            {
                "version_id": pf["file"],
                "source_version_datetime": ver,
                "snapshot_label": format_snapshot_label(ver),
                "version_class": pf["filename_meta"]["cp"],
                "file_sha256": pf["file_sha256"],
                "archive_sha256": pf.get("archive_sha256"),
                "top_level_section_count": pf["top_level_section_count"],
                "title": pf.get("title"),
            }
        )

    # Section registry across versions
    sections_index: dict[str, dict[str, Any]] = {}
    section_text_by_version: dict[str, dict[str, Any]] = defaultdict(dict)
    renderability_counter: Counter[str] = Counter()

    for pf in parsed:
        path = path_by_name[pf["file"]]
        root = parse_xml_file(path)
        el_by_id = {s.attrib.get("id"): s for s in iter_top_level_sections(root) if s.attrib.get("id")}
        for sec in pf["sections"]:
            sid = sec.get("element_id")
            if not sid:
                continue
            el = el_by_id.get(sid)
            if el is None:
                continue
            canon = canonicalize_section(el)
            renderability_counter[canon.renderability] += 1
            plain = _plain_text_from_canon(canon.to_dict()["tokens"])
            entry = sections_index.setdefault(
                sid,
                {
                    "section_id": sid,
                    "temporal_ids": set(),
                    "nums_seen": set(),
                    "headings_seen": set(),
                    "first_version": pf["file"],
                    "last_version": pf["file"],
                    "appearances": 0,
                },
            )
            entry["temporal_ids"].add(sec.get("temporal_id"))
            entry["nums_seen"].add(sec.get("num"))
            entry["headings_seen"].add(sec.get("heading"))
            entry["last_version"] = pf["file"]
            entry["appearances"] += 1
            section_text_by_version[sid][pf["file"]] = {
                "num": canon.section_num,
                "heading": canon.heading,
                "plain_text": plain,
                "canonical_sha256": canon.sha256(),
                "renderability": canon.renderability,
                "status": canon.status,
                "reason": canon.reason,
                "partial": canon.partial,
                "tokens": canon.to_dict()["tokens"],
                "provenance": {
                    "source_file": pf["file"],
                    "source_file_sha256": pf["file_sha256"],
                    "source_archive_sha256": pf.get("archive_sha256"),
                    "source_version_datetime": pf["filename_meta"]["ver"],
                    "element_id": sid,
                    "temporal_id": sec.get("temporal_id"),
                    "canonical_xpath": sec.get("canonical_xpath"),
                    "parser_version": PARSER_VERSION,
                    "normalization_version": NORMALIZATION_VERSION,
                    "comparator_version": COMPARATOR_VERSION,
                    "official_portal": HKEL_SEARCH,
                },
            }

    # Transitions
    transitions_meta: list[dict[str, Any]] = []
    relationship_totals: Counter[str] = Counter()
    change_freq: Counter[str] = Counter()
    section_change_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    token_additions = 0
    token_deletions = 0
    recon_ok = 0
    recon_total = 0
    transitions_dir = out_dir / "transitions"
    transitions_dir.mkdir(parents=True, exist_ok=True)

    for older, newer in zip(parsed, parsed[1:], strict=False):
        tid = f"{older['file']}__to__{newer['file']}"
        m = match_sections(older["sections"], newer["sections"])
        items: list[dict[str, Any]] = []
        counts: Counter[str] = Counter()
        from_label = format_snapshot_label(older["filename_meta"]["ver"])
        to_label = format_snapshot_label(newer["filename_meta"]["ver"])

        for edge in m["edges"]:
            if edge["match_method"] == "id" and edge.get("older") and edge.get("newer"):
                o, n = edge["older"], edge["newer"]
                o_el = _section_el(path_by_name[older["file"]], o["element_id"])
                n_el = _section_el(path_by_name[newer["file"]], n["element_id"])
                if o_el is None or n_el is None:
                    continue
                ca, cb = canonicalize_section(o_el), canonicalize_section(n_el)
                cmp = compare_sections(
                    instrument=instrument_id,
                    version_a_id=older["file"],
                    version_b_id=newer["file"],
                    canon_a=ca,
                    canon_b=cb,
                    provenance_a=section_text_by_version[o["element_id"]][older["file"]]["provenance"],
                    provenance_b=section_text_by_version[n["element_id"]][newer["file"]]["provenance"],
                )
                recon_total += 1
                if cmp.reconstruction_ok:
                    recon_ok += 1
                relationship_totals[cmp.relationship] += 1
                counts[cmp.relationship] += 1
                if cmp.relationship != "unchanged":
                    change_freq[o["element_id"]] += 1
                    section_change_events[o["element_id"]].append(
                        {
                            "from_version": older["file"],
                            "to_version": newer["file"],
                            "from_label": from_label,
                            "to_label": to_label,
                            "relationship": cmp.relationship,
                            "section_num_a": cmp.section_num_a,
                            "section_num_b": cmp.section_num_b,
                        }
                    )
                for op in cmp.legal_text_diff["operations"]:
                    if op.get("op") == "insert":
                        token_additions += len(op.get("b_tokens") or [])
                    elif op.get("op") == "delete":
                        token_deletions += len(op.get("a_tokens") or [])
                    elif op.get("op") == "replace":
                        token_deletions += len(op.get("a_tokens") or [])
                        token_additions += len(op.get("b_tokens") or [])
                item = {
                    "section_id": cmp.section_id,
                    "relationship": cmp.relationship,
                    "section_num_a": cmp.section_num_a,
                    "section_num_b": cmp.section_num_b,
                    "ordinary_redline_supported": cmp.ordinary_redline_supported,
                    "limitation": cmp.limitation,
                    "reconstruction_ok": cmp.reconstruction_ok,
                    "renderability_a": cmp.renderability_a,
                    "renderability_b": cmp.renderability_b,
                    "legal_text_ops": cmp.legal_text_diff["operations"],
                    "structural_ops": cmp.structural_diff["operations"],
                    "metadata_ops": cmp.metadata_diff["operations"],
                    "highlight_legal_text": highlight_ops(cmp.legal_text_diff["operations"], limit=200),
                    "canonical_a_sha256": ca.sha256(),
                    "canonical_b_sha256": cb.sha256(),
                    "plain_text_a": _plain_text_from_canon(ca.to_dict()["tokens"]),
                    "plain_text_b": _plain_text_from_canon(cb.to_dict()["tokens"]),
                    "tokens_a": ca.to_dict()["tokens"],
                    "tokens_b": cb.to_dict()["tokens"],
                    "provenance_a": cmp.provenance_a,
                    "provenance_b": cmp.provenance_b,
                    "comparator_version": COMPARATOR_VERSION,
                    "normalization_version": NORMALIZATION_VERSION,
                    "match_method": "id",
                }
                items.append(item)
            elif edge["change_class"] == "added" and edge.get("newer"):
                n = edge["newer"]
                relationship_totals["added"] += 1
                counts["added"] += 1
                snap = section_text_by_version.get(n["element_id"], {}).get(newer["file"])
                section_change_events[n["element_id"]].append(
                    {
                        "from_version": older["file"],
                        "to_version": newer["file"],
                        "from_label": from_label,
                        "to_label": to_label,
                        "relationship": "added",
                        "section_num_a": None,
                        "section_num_b": n.get("num"),
                    }
                )
                items.append(
                    {
                        "section_id": n["element_id"],
                        "relationship": "added",
                        "section_num_a": None,
                        "section_num_b": n.get("num"),
                        "plain_text_b": (snap or {}).get("plain_text"),
                        "heading": n.get("heading"),
                        "match_method": "unmatched",
                        "reconstruction_ok": True,
                        "ordinary_redline_supported": True,
                    }
                )
            elif edge["change_class"] in {"removed_or_unmatched"} and edge.get("older"):
                o = edge["older"]
                relationship_totals["removed"] += 1
                counts["removed"] += 1
                snap = section_text_by_version.get(o["element_id"], {}).get(older["file"])
                section_change_events[o["element_id"]].append(
                    {
                        "from_version": older["file"],
                        "to_version": newer["file"],
                        "from_label": from_label,
                        "to_label": to_label,
                        "relationship": "removed",
                        "section_num_a": o.get("num"),
                        "section_num_b": None,
                    }
                )
                items.append(
                    {
                        "section_id": o["element_id"],
                        "relationship": "removed",
                        "section_num_a": o.get("num"),
                        "section_num_b": None,
                        "plain_text_a": (snap or {}).get("plain_text"),
                        "heading": o.get("heading"),
                        "match_method": "unmatched",
                        "reconstruction_ok": True,
                        "ordinary_redline_supported": True,
                    }
                )

        # Ambiguous must not be silently accepted — record separately
        ambiguous = m.get("ambiguous") or []

        t_payload = {
            "schema_version": EXPORT_SCHEMA_VERSION,
            "instrument_id": instrument_id,
            "transition_id": tid,
            "from_version": older["file"],
            "to_version": newer["file"],
            "from_label": from_label,
            "to_label": to_label,
            "counts": dict(counts),
            "unchanged_count": counts.get("unchanged", 0),
            "ambiguous_count": len(ambiguous),
            "ambiguous_events": [
                {"older_id": a["older"].get("element_id"), "reason": a.get("method")}
                for a in ambiguous
            ],
            "items": items,
            "dataset_mode": dataset_mode,
            "generation_timestamp": utc_now(),
            "comparator_version": COMPARATOR_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "parser_version": PARSER_VERSION,
        }
        content_hash = dump_json(transitions_dir / f"{tid}.json", t_payload)
        transitions_meta.append(
            {
                "transition_id": tid,
                "from_version": older["file"],
                "to_version": newer["file"],
                "from_label": t_payload["from_label"],
                "to_label": t_payload["to_label"],
                "counts": dict(counts),
                "unchanged_count": counts.get("unchanged", 0),
                "changed_count": sum(v for k, v in counts.items() if k != "unchanged"),
                "ambiguous_count": len(ambiguous),
                "content_hash": content_hash,
            }
        )

    # Serialize section index
    sections_out = []
    for sid, meta in sorted(sections_index.items(), key=lambda kv: (list(kv[1]["nums_seen"]) or [""])[0] or ""):
        history = []
        for ver in versions:
            snap = section_text_by_version.get(sid, {}).get(ver["version_id"])
            if not snap:
                continue
            history.append(
                {
                    "version_id": ver["version_id"],
                    "snapshot_label": ver["snapshot_label"],
                    "num": snap["num"],
                    "heading": snap["heading"],
                    "status": snap["status"],
                    "canonical_sha256": snap["canonical_sha256"],
                    "renderability": snap["renderability"],
                }
            )
        # transitions touching this section are recorded in section_change_events
        sections_out.append(
            {
                "section_id": sid,
                "nums_seen": sorted(x for x in meta["nums_seen"] if x),
                "headings_seen": sorted(x for x in meta["headings_seen"] if x),
                "temporal_ids": sorted(x for x in meta["temporal_ids"] if x),
                "first_version": meta["first_version"],
                "last_version": meta["last_version"],
                "appearances": meta["appearances"],
                "descriptive_change_count": change_freq.get(sid, 0),
                "history": history,
                "latest_heading": history[-1]["heading"] if history else None,
                "latest_num": history[-1]["num"] if history else None,
            }
        )

    # Per-section detail files (chunked text + precomputed change history)
    sections_dir = out_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    histories_index: dict[str, Any] = {}
    for sid, by_ver in section_text_by_version.items():
        change_events = section_change_events.get(sid, [])
        payload = {
            "schema_version": EXPORT_SCHEMA_VERSION,
            "instrument_id": instrument_id,
            "section_id": sid,
            "snapshots": by_ver,
            "change_events": change_events,
            "descriptive_change_count": change_freq.get(sid, 0),
            "frequency_disclaimer": (
                "Change frequency is a descriptive corpus measure for this dataset, "
                "not a measure of legal importance."
            ),
            "dataset_mode": dataset_mode,
            "generation_timestamp": utc_now(),
        }
        # Sanitize filename
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", sid)
        dump_json(sections_dir / f"{safe}.json", payload)
        histories_index[sid] = {
            "section_id": sid,
            "descriptive_change_count": change_freq.get(sid, 0),
            "change_events": change_events,
            "appearance_count": len(by_ver),
        }
    dump_json(
        out_dir / "section-histories.json",
        {
            "instrument_id": instrument_id,
            "sections": histories_index,
            "frequency_disclaimer": (
                "Change frequency is a descriptive corpus measure for this dataset, "
                "not a measure of legal importance."
            ),
            "dataset_mode": dataset_mode,
            "generation_timestamp": utc_now(),
        },
    )

    insights = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "instrument_id": instrument_id,
        "disclaimer": DISCLAIMER,
        "notes": [
            "All metrics are descriptive corpus measures derived from exported comparisons.",
            "Change frequency is not a measure of legal importance.",
            "No normative claims about legislative intent or public-health effect are made.",
        ],
        "relationship_totals": dict(relationship_totals),
        "transitions": [
            {
                "transition_id": t["transition_id"],
                "from_label": t["from_label"],
                "to_label": t["to_label"],
                "changed_count": t["changed_count"],
                "counts": t["counts"],
            }
            for t in transitions_meta
        ],
        "sections_changed_most_frequently": [
            {
                "section_id": sid,
                "descriptive_change_count": cnt,
                "latest_num": next(
                    (s["latest_num"] for s in sections_out if s["section_id"] == sid), None
                ),
                "latest_heading": next(
                    (s["latest_heading"] for s in sections_out if s["section_id"] == sid),
                    None,
                ),
            }
            for sid, cnt in change_freq.most_common(20)
        ],
        "renderability_distribution": dict(renderability_counter),
        "textual_vs_status": {
            "text_changed_events": relationship_totals.get("text_changed", 0)
            + relationship_totals.get("text_and_status_changed", 0),
            "status_only_events": relationship_totals.get("status_changed", 0),
            "added": relationship_totals.get("added", 0),
            "removed": relationship_totals.get("removed", 0),
        },
        "token_flow": {
            "legal_text_token_additions": token_additions,
            "legal_text_token_deletions": token_deletions,
        },
        "stable_id_coverage_note": (
            "Coverage reflects consecutive same-@id matches over included snapshots; "
            "additions/removals reduce matched/old-slot ratios without implying ambiguity."
        ),
        "reconstruction": {
            "ok": recon_ok,
            "total": recon_total,
            "rate": (recon_ok / recon_total) if recon_total else None,
        },
        "sampling": sampling_info,
        "dataset_mode": dataset_mode,
        "generation_timestamp": utc_now(),
        "comparator_version": COMPARATOR_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
    }

    # Example comparison for landing: first text_changed
    example = None
    for tm in transitions_meta:
        tpath = transitions_dir / f"{tm['transition_id']}.json"
        data = json.loads(tpath.read_text(encoding="utf-8"))
        for item in data["items"]:
            if item["relationship"] in {"text_changed", "text_and_status_changed"}:
                example = {
                    "instrument_id": instrument_id,
                    "transition_id": tm["transition_id"],
                    "section_id": item["section_id"],
                    "from_version": tm["from_version"],
                    "to_version": tm["to_version"],
                    "relationship": item["relationship"],
                    "heading": item.get("section_num_b") or item.get("section_num_a"),
                }
                break
        if example:
            break

    manifest = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "instrument_id": instrument_id,
        "title": title,
        "language": "en",
        "dataset_mode": dataset_mode,
        "sampling": sampling_info,
        "version_count": len(versions),
        "section_count": len(sections_out),
        "transition_count": len(transitions_meta),
        "relationship_totals": dict(relationship_totals),
        "reconstruction": insights["reconstruction"],
        "renderability_distribution": dict(renderability_counter),
        "example_comparison": example,
        "paths": {
            "versions": "versions.json",
            "sections": "sections.json",
            "insights": "insights.json",
            "transitions": "transitions.json",
            "section_histories": "section-histories.json",
            "transitions_dir": "transitions/",
            "section_detail_dir": "sections/",
        },
        "disclaimer": DISCLAIMER,
        "attribution_path": "fixtures/lawtrace/ATTRIBUTION.md",
        "generation_timestamp": utc_now(),
        "comparator_version": COMPARATOR_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "parser_version": PARSER_VERSION,
        "official_portal": HKEL_SEARCH,
    }

    dump_json(out_dir / "manifest.json", manifest)
    dump_json(out_dir / "versions.json", {"instrument_id": instrument_id, "versions": versions})
    dump_json(out_dir / "sections.json", {"instrument_id": instrument_id, "sections": sections_out})
    dump_json(out_dir / "insights.json", insights)
    dump_json(out_dir / "transitions.json", {"instrument_id": instrument_id, "transitions": transitions_meta})

    return manifest


def write_root_manifest(
    out_root: Path,
    instruments: list[dict[str, Any]],
    *,
    dataset_mode: str,
) -> None:
    methodology = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "product_promise": (
            "Compare two official open-data versions of a Hong Kong legislative section "
            "and inspect what changed."
        ),
        "disclaimer": DISCLAIMER,
        "date_semantics": "VERSION_TO_VERSION_COMPARATOR_ONLY",
        "identity": "top-level section @id only; nested nodes lack independent MVP identity",
        "supported_relationships": [
            "unchanged",
            "text_changed",
            "status_changed",
            "text_and_status_changed",
            "added",
            "removed",
            "section_number_changed",
        ],
        "unsupported_or_candidate": [
            "split",
            "consolidation",
            "id_changed",
            "ambiguous_renumbering",
            "fuzzy_similarity",
        ],
        "review_status_policy": (
            "Algorithm-generated comparisons are not human-confirmed gold unless an "
            "exported human review is deliberately imported."
        ),
        "attribution": {
            "source": "Department of Justice / HKeL via DATA.GOV.HK",
            "terms": "DATA.GOV.HK Terms of Use Version 1.2",
            "file": "fixtures/lawtrace/ATTRIBUTION.md",
        },
        "corrections_contact_placeholder": "corrections@example.invalid (placeholder — replace before public launch)",
        "generation_timestamp": utc_now(),
    }
    dump_json(out_root / "methodology.json", methodology)
    root = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "dataset_mode": dataset_mode,
        "product_promise": methodology["product_promise"],
        "disclaimer": DISCLAIMER,
        "instruments": instruments,
        "paths": {"methodology": "methodology.json"},
        "generation_timestamp": utc_now(),
        "comparator_version": COMPARATOR_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "parser_version": PARSER_VERSION,
    }
    dump_json(out_root / "manifest.json", root)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Export LawTrace web artifacts")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("apps/lawtrace/public/data"),
        help="Output root for web JSON",
    )
    ap.add_argument(
        "--mode",
        choices=["demo", "local"],
        default="demo",
        help="demo=Cap.614 only (CI); local=also Cap.599G from extracts",
    )
    ap.add_argument(
        "--cap599g-dir",
        type=Path,
        default=Path("data/lawtrace/extracted/cap599g"),
        help="Directory containing Cap. 599G EN XML extracts",
    )
    ap.add_argument(
        "--cap599g-max-versions",
        type=int,
        default=None,
        help="Optional even-span limiter for Cap. 599G (omit = all available)",
    )
    args = ap.parse_args(argv)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    instruments_meta: list[dict[str, Any]] = []

    # Cap. 614 — always
    cap614 = export_instrument(
        instrument_id="cap:614",
        title="Legislation Publication Ordinance (Cap. 614)",
        fixture_or_extract_dir=Path("fixtures/lawtrace/cap_614"),
        out_dir=out / "instruments" / "cap-614",
        dataset_mode=args.mode,
        archive_sha256="3b1348f1678c5ebb6ef7c4fa99b4aaba2691575d2a7695751ae7466f9e21c064",
    )
    instruments_meta.append(
        {
            "instrument_id": "cap:614",
            "slug": "cap-614",
            "title": cap614["title"],
            "available": True,
            "dataset_mode": args.mode,
            "sampling": cap614["sampling"],
            "version_count": cap614["version_count"],
            "section_count": cap614["section_count"],
            "path": "instruments/cap-614/manifest.json",
            "example_comparison": cap614.get("example_comparison"),
        }
    )

    if args.mode == "local":
        if not args.cap599g_dir.exists() or not any(args.cap599g_dir.rglob("*.xml")):
            instruments_meta.append(
                {
                    "instrument_id": "cap:599G",
                    "slug": "cap-599g",
                    "title": "Prevention and Control of Disease (Requirements and Directions) "
                    "(Business and Premises) Regulation (Cap. 599G)",
                    "available": False,
                    "dataset_mode": "local",
                    "missing_reason": (
                        f"Cap. 599G extracts absent at {args.cap599g_dir}. "
                        "Download official EN Cap. 301–600 ZIPs into data/lawtrace/raw/, "
                        "extract cap_599G members into that directory, then re-run "
                        "`make lawtrace-web-data-local`. See docs/LAWTRACE_MVP.md."
                    ),
                    "path": "instruments/cap-599g/manifest.json",
                }
            )
        else:
            cap599g = export_instrument(
                instrument_id="cap:599G",
                title="Prevention and Control of Disease (Requirements and Directions) "
                "(Business and Premises) Regulation (Cap. 599G)",
                fixture_or_extract_dir=args.cap599g_dir,
                out_dir=out / "instruments" / "cap-599g",
                dataset_mode="local",
                archive_sha256=None,
                max_versions=args.cap599g_max_versions,
            )
            instruments_meta.append(
                {
                    "instrument_id": "cap:599G",
                    "slug": "cap-599g",
                    "title": cap599g["title"],
                    "available": True,
                    "dataset_mode": "local",
                    "sampling": cap599g["sampling"],
                    "version_count": cap599g["version_count"],
                    "section_count": cap599g["section_count"],
                    "path": "instruments/cap-599g/manifest.json",
                    "example_comparison": cap599g.get("example_comparison"),
                }
            )
    else:
        instruments_meta.append(
            {
                "instrument_id": "cap:599G",
                "slug": "cap-599g",
                "title": "Prevention and Control of Disease (Requirements and Directions) "
                "(Business and Premises) Regulation (Cap. 599G)",
                "available": False,
                "dataset_mode": "demo",
                "missing_reason": (
                    "Cap. 599G local-real artifacts are gitignored. Run "
                    "`make lawtrace-web-data-local` after acquiring official extracts."
                ),
                "path": "instruments/cap-599g/manifest.json",
            }
        )

    write_root_manifest(out, instruments_meta, dataset_mode=args.mode)
    print(json.dumps({"out": str(out), "instruments": instruments_meta}, indent=2))


if __name__ == "__main__":
    main()
