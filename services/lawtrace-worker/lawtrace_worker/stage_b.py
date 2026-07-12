"""Stage B: Cap. 614 top-level section parse, identity, date semantics."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, tostring

from lawtrace_worker import NORMALIZATION_VERSION, PARSER_VERSION
from lawtrace_worker.census import (
    extract_title,
    parse_filename,
    structure_flags,
)
from lawtrace_worker.security.xml_safe import local_name, parse_xml_file

FILENAME_TS_RE = re.compile(r"_([0-9]{14}|-{14})_")


@dataclass
class DateFieldFinding:
    field_name: str
    value: str | None
    source_locator: str | None
    applies_to: str  # instrument | provision | acquisition | unknown
    explicit: bool
    confidence: str  # high | medium | low | none
    may_use_in_ui: bool
    notes: str


@dataclass
class SectionVersionRecord:
    instrument_id: str
    language: str
    source_file: str
    source_file_sha256: str
    source_archive_sha256: str | None
    source_version_datetime: str | None
    version_class: str
    element_id: str | None
    temporal_id: str | None
    num: str | None
    heading: str | None
    canonical_xpath: str
    xml_fragment_sha256: str
    extracted_text_sha256: str
    parser_version: str
    normalization_version: str
    renderability: str
    status: str | None
    reason: str | None
    partial: str | None
    renderability_reasons: list[str] = field(default_factory=list)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def normalize_operative_text(elem: Element) -> str:
    """Deterministic text extraction preserving structure markers lightly.

    Does not drop sup/sub content; includes their text. Tables/images flagged
    via renderability rather than discarded here.
    """
    parts: list[str] = []

    def walk(el: Element, depth: int = 0) -> None:
        ln = local_name(el.tag)
        if ln in {"editorialNote"}:
            return
        if el.text and el.text.strip():
            parts.append(re.sub(r"[ \t]+", " ", el.text.strip()))
        for child in el:
            walk(child, depth + 1)
            if child.tail and child.tail.strip():
                parts.append(re.sub(r"[ \t]+", " ", child.tail.strip()))

    walk(elem)
    text = "\n".join(p for p in parts if p)
    # NFC
    import unicodedata

    return unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")


def classify_renderability(elem: Element) -> tuple[str, list[str]]:
    flags = structure_flags(elem)
    reasons: list[str] = []
    # Walk only within this section subtree
    has_table = has_img = has_form = has_sup_sub = False
    for el in elem.iter():
        ln = local_name(el.tag)
        if ln in {"layout", "header", "row", "column"}:
            has_table = True
        elif ln == "img":
            has_img = True
        elif ln in {"fillIn", "checkBox"}:
            has_form = True
        elif ln in {"sup", "sub"}:
            has_sup_sub = True
    if has_img:
        reasons.append("img")
    if has_form:
        reasons.append("form_controls")
    if has_table:
        reasons.append("table_or_layout")
    if has_sup_sub:
        reasons.append("sup_or_sub_present")
    if has_img or has_form:
        return "unsupported", reasons
    if has_table:
        return "potentially_lossy", reasons
    if has_sup_sub:
        return "complete_with_nontext_metadata", reasons
    _ = flags
    return "complete", reasons


def build_parent_map(root: Element) -> dict[Element, Element]:
    return {c: p for p in root.iter() for c in p}


def xpath_for(elem: Element, root: Element, parent_map: dict[Element, Element]) -> str:
    parts: list[str] = []
    cur: Element | None = elem
    while cur is not None:
        ln = local_name(cur.tag)
        parent = parent_map.get(cur)
        if parent is None:
            parts.append(ln)
            break
        siblings = [c for c in parent if local_name(c.tag) == ln]
        if len(siblings) == 1:
            parts.append(ln)
        else:
            idx = siblings.index(cur) + 1
            parts.append(f"{ln}[{idx}]")
        cur = parent
    return "/" + "/".join(reversed(parts))


def iter_top_level_sections(root: Element) -> list[Element]:
    parent_map = build_parent_map(root)
    out: list[Element] = []
    for el in root.iter():
        if local_name(el.tag) != "section":
            continue
        p = parent_map.get(el)
        nested = False
        while p is not None:
            if local_name(p.tag) == "section":
                nested = True
                break
            p = parent_map.get(p)
        if not nested:
            out.append(el)
    return out


def child_text(el: Element, name: str) -> str | None:
    for c in el:
        if local_name(c.tag) == name:
            t = "".join(c.itertext()).strip()
            return t or None
    return None


def extract_meta_properties(root: Element) -> dict[str, str]:
    props: dict[str, str] = {}
    for el in root.iter():
        if local_name(el.tag) != "property":
            continue
        name = el.attrib.get("name") or el.attrib.get("Name")
        val = el.attrib.get("value")
        if val is None:
            val = "".join(el.itertext()).strip()
        if name:
            props[str(name)] = str(val) if val is not None else ""
    # Also docStatus / dublin-core style elements
    for el in root.iter():
        ln = local_name(el.tag)
        if ln in {
            "docStatus",
            "docNumber",
            "docType",
            "docTitle",
            "shortTitle",
            "docName",
            "date",
            "identifier",
        }:
            key = f"element:{ln}"
            # Disambiguate Dublin Core date
            if "purl.org/dc" in el.tag or el.tag.startswith("{http://purl.org/dc"):
                key = f"element:dc:{ln}"
            props[key] = "".join(el.itertext()).strip()
            for ak, av in el.attrib.items():
                props[f"{key}@{ak}"] = av
    return props


def parse_instrument_file(
    path: Path,
    *,
    archive_sha256: str | None,
    file_sha256: str | None = None,
) -> dict[str, Any]:
    meta = parse_filename(path.name)
    if not meta:
        raise ValueError(f"unrecognized filename: {path.name}")
    raw = path.read_bytes()
    file_sha = file_sha256 or sha256_bytes(raw)
    root = parse_xml_file(path)
    parent_map = build_parent_map(root)
    props = extract_meta_properties(root)
    sections = []
    for sec in iter_top_level_sections(root):
        frag = tostring(sec, encoding="utf-8")
        text = normalize_operative_text(sec)
        rend, reasons = classify_renderability(sec)
        rec = SectionVersionRecord(
            instrument_id=f"cap:{meta['cap']}",
            language=meta["lang"],
            source_file=path.name,
            source_file_sha256=file_sha,
            source_archive_sha256=archive_sha256,
            source_version_datetime=None if meta["ver"].startswith("-") else meta["ver"],
            version_class="current" if meta["cp"].lower() == "c" else "past",
            element_id=sec.attrib.get("id"),
            temporal_id=sec.attrib.get("temporalId"),
            num=child_text(sec, "num"),
            heading=child_text(sec, "heading"),
            canonical_xpath=xpath_for(sec, root, parent_map),
            xml_fragment_sha256=sha256_bytes(frag),
            extracted_text_sha256=sha256_text(text),
            parser_version=PARSER_VERSION,
            normalization_version=NORMALIZATION_VERSION,
            renderability=rend,
            status=sec.attrib.get("status"),
            reason=sec.attrib.get("reason"),
            partial=sec.attrib.get("partial"),
            renderability_reasons=reasons,
        )
        row = asdict(rec)
        # Preserve explicit temporal attributes without relabeling them as effective dates.
        row["start_period"] = sec.attrib.get("startPeriod")
        row["end_period"] = sec.attrib.get("endPeriod")
        sections.append(row)
    schedules = sum(1 for el in root.iter() if local_name(el.tag) == "schedule")
    return {
        "file": path.name,
        "file_sha256": file_sha,
        "archive_sha256": archive_sha256,
        "filename_meta": meta,
        "title": extract_title(root),
        "top_level_section_count": len(sections),
        "schedule_count_experimental": schedules,
        "doc_properties": props,
        "structure_flags": structure_flags(root),
        "sections": sections,
    }


def match_sections(older: list[dict[str, Any]], newer: list[dict[str, Any]]) -> dict[str, Any]:
    """Match top-level sections between consecutive versions. No fuzzy/LLM."""
    used_new: set[int] = set()
    edges: list[dict[str, Any]] = []
    unmatched_old: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []

    def index_by(key: str, rows: list[dict[str, Any]]) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {}
        for i, r in enumerate(rows):
            v = r.get(key)
            if v:
                out.setdefault(str(v), []).append(i)
        return out

    new_by_id = index_by("element_id", newer)
    new_by_tid = index_by("temporal_id", newer)
    new_by_num = index_by("num", newer)

    for o in older:
        method = None
        candidates: list[int] = []
        if o.get("element_id") and o["element_id"] in new_by_id:
            candidates = [i for i in new_by_id[o["element_id"]] if i not in used_new]
            method = "id"
        elif o.get("temporal_id") and o["temporal_id"] in new_by_tid:
            candidates = [i for i in new_by_tid[o["temporal_id"]] if i not in used_new]
            method = "temporalId"
        elif o.get("num") and o["num"] in new_by_num:
            candidates = [i for i in new_by_num[o["num"]] if i not in used_new]
            method = "unique_num"
        if not candidates:
            unmatched_old.append(o)
            edges.append(
                {
                    "match_method": "unmatched",
                    "change_class": "removed_or_unmatched",
                    "older": o,
                    "newer": None,
                }
            )
            continue
        if len(candidates) != 1:
            ambiguous.append({"older": o, "candidate_indexes": candidates, "method": method})
            edges.append(
                {
                    "match_method": "unmatched",
                    "change_class": "ambiguous",
                    "older": o,
                    "newer": None,
                    "reason": f"ambiguous_{method}",
                }
            )
            continue
        ni = candidates[0]
        used_new.add(ni)
        n = newer[ni]
        change = "unchanged"
        if o["extracted_text_sha256"] != n["extracted_text_sha256"]:
            change = "text_changed"
        if (o.get("status"), o.get("reason"), o.get("partial")) != (
            n.get("status"),
            n.get("reason"),
            n.get("partial"),
        ):
            change = "status_changed" if change == "unchanged" else "text_and_status_changed"
        if (o.get("num") or "") != (n.get("num") or "") and method == "id":
            change = "renumber_candidate"
        edges.append(
            {
                "match_method": method,
                "change_class": change,
                "older": o,
                "newer": n,
            }
        )

    added = []
    for i, n in enumerate(newer):
        if i not in used_new:
            added.append(n)
            edges.append(
                {
                    "match_method": "unmatched",
                    "change_class": "added",
                    "older": None,
                    "newer": n,
                }
            )

    accepted = [e for e in edges if e["match_method"] in {"id", "temporalId", "unique_num"}]
    return {
        "edges": edges,
        "accepted_edges": accepted,
        "ambiguous": ambiguous,
        "added": added,
        "removed_or_unmatched_old": unmatched_old,
        "counts": {
            "matched_by_id": sum(1 for e in accepted if e["match_method"] == "id"),
            "matched_by_temporalId": sum(1 for e in accepted if e["match_method"] == "temporalId"),
            "matched_by_unique_num": sum(1 for e in accepted if e["match_method"] == "unique_num"),
            "added": len(added),
            "ambiguous": len(ambiguous),
            "unmatched_old": len(unmatched_old),
            "text_changed": sum(1 for e in accepted if "text" in e["change_class"]),
            "status_changed": sum(1 for e in accepted if "status" in e["change_class"]),
            "renumber_candidate": sum(
                1 for e in accepted if e["change_class"] == "renumber_candidate"
            ),
        },
    }


def investigate_date_semantics(parsed_files: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[DateFieldFinding] = []
    # download datetime is acquisition-side — not in XML
    findings.append(
        DateFieldFinding(
            field_name="download_datetime",
            value=None,
            source_locator="import_run / source_registry.download_timestamp",
            applies_to="acquisition",
            explicit=True,
            confidence="high",
            may_use_in_ui=True,
            notes="Acquisition timestamp only; never a legal version date.",
        )
    )
    # filename version
    sample = parsed_files[0] if parsed_files else None
    fn_ver = sample["filename_meta"]["ver"] if sample else None
    findings.append(
        DateFieldFinding(
            field_name="source_version_datetime",
            value=fn_ver,
            source_locator="filename pattern ..._[yyyymmddhhmiss]_[lang]_[c|p].xml",
            applies_to="instrument",
            explicit=True,
            confidence="high",
            may_use_in_ui=True,
            notes=(
                "Official data dictionary documents this as Version date for the XML resource. "
                "It is a whole-file version timestamp, not proven as provision commencement."
            ),
        )
    )
    findings.append(
        DateFieldFinding(
            field_name="whole_instrument_version_date",
            value=fn_ver,
            source_locator="same as filename version date unless a distinct meta property is found",
            applies_to="instrument",
            explicit=True,
            confidence="medium",
            may_use_in_ui=True,
            notes=(
                "Treated as equivalent to source_version_datetime for these fixtures unless "
                "meta properties provide a different instrument version date."
            ),
        )
    )

    # Scan properties across files for effective/commencement-like keys
    prop_keys: set[str] = set()
    for pf in parsed_files:
        prop_keys.update(pf.get("doc_properties", {}).keys())
    interesting = sorted(
        k for k in prop_keys if re.search(r"date|effect|commenc|version|status|update", k, re.I)
    )
    # Provision-level effective/commencement: look at section attributes across samples
    section_attr_keys: set[str] = set()
    provision_dates_found = False
    for pf in parsed_files:
        for sec in pf["sections"]:
            for k in ("status", "reason", "partial"):
                if sec.get(k):
                    section_attr_keys.add(k)
            # no dedicated effective date fields observed in records constructed above
    # Re-scan raw properties including Dublin Core date and section periods.
    dc_values = []
    start_periods = []
    for pf in parsed_files:
        for k, v in pf.get("doc_properties", {}).items():
            if k.endswith("date") or k.endswith("}date") or k == "element:dc:date":
                if v:
                    dc_values.append(v)
        for sec in pf["sections"]:
            if sec.get("start_period"):
                start_periods.append(sec["start_period"])
                section_attr_keys.add("startPeriod")
            if sec.get("end_period"):
                section_attr_keys.add("endPeriod")
            if sec.get("start_period") or sec.get("end_period"):
                provision_dates_found = True

    findings.append(
        DateFieldFinding(
            field_name="dc_date_instrument_meta",
            value=dc_values[0] if dc_values else None,
            source_locator="meta/dc:date (Dublin Core) in instrument XML",
            applies_to="instrument",
            explicit=True,
            confidence="high",
            may_use_in_ui=True,
            notes=(
                "Observed to align with filename version date (YYYY-MM-DD vs yyyymmddhhmiss). "
                "Treat as instrument snapshot/version date metadata, not provision commencement."
            ),
        )
    )
    findings.append(
        DateFieldFinding(
            field_name="provision_start_period",
            value=sorted(set(start_periods))[0] if start_periods else None,
            source_locator="section/@startPeriod (and optionally @endPeriod)",
            applies_to="provision",
            explicit=True,
            confidence="medium",
            may_use_in_ui=False,
            notes=(
                "Explicit attribute present on many Cap. 614 sections. Attribute name is "
                "startPeriod, not effective_date or commencement_date. Without an authoritative "
                "mapping from the data dictionary/XSD semantics into a user-facing "
                "'law in force on date X' promise, do not use this field for that claim in Stage B."
            ),
        )
    )
    findings.append(
        DateFieldFinding(
            field_name="provision_last_updated_date",
            value=None,
            source_locator="no dedicated last-updated field distinct from startPeriod observed",
            applies_to="provision",
            explicit=False,
            confidence="none",
            may_use_in_ui=False,
            notes="Do not infer from instrument version date or startPeriod.",
        )
    )
    findings.append(
        DateFieldFinding(
            field_name="effective_date",
            value=None,
            source_locator="no attribute literally named effective date on Cap. 614 sections",
            applies_to="provision",
            explicit=False,
            confidence="none",
            may_use_in_ui=False,
            notes=(
                "Must not relabel filename version date or startPeriod as effective_date "
                "without source documentation proving equivalence."
            ),
        )
    )
    findings.append(
        DateFieldFinding(
            field_name="commencement_date",
            value=None,
            source_locator="commencementNote narrative (e.g. '[30 June 2011]') at instrument level",
            applies_to="instrument",
            explicit=True,
            confidence="medium",
            may_use_in_ui=False,
            notes=(
                "Narrative commencementNote exists for Cap. 614 but is not a structured "
                "per-section commencement date suitable for as-at queries in Stage B."
            ),
        )
    )

    # Conclusion: narrowest supported promise
    # startPeriod exists but is insufficiently documented here for as-at promise.
    conclusion = "VERSION_TO_VERSION_COMPARATOR_ONLY"
    rationale = (
        "Filename version datetime and meta/dc:date reliably identify the whole-instrument "
        "open-data XML snapshot. Section @startPeriod is explicit but not safely mapped in "
        "this spike to a user-facing 'law in force on date X' promise. Narrative "
        "commencementNote is instrument-level only. Therefore the supported product promise "
        "is a version-to-version comparator (optionally labeled with source_version_datetime), "
        "not an as-at-date force-of-law query."
    )
    return {
        "conclusion": conclusion,
        "rationale": rationale,
        "findings": [asdict(f) for f in findings],
        "observed_doc_property_keys_matching_date_patterns": interesting,
        "observed_section_status_attributes": sorted(section_attr_keys),
        "provision_structured_effective_dates_found": provision_dates_found,
    }
