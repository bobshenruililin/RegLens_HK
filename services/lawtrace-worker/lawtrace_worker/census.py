"""Corpus census over extracted LawTrace XML fixtures."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from lawtrace_worker.security.xml_safe import XmlSecurityError, local_name, parse_xml_file

FILENAME_RE = re.compile(
    r"^(?P<kind>cap|a)_(?P<cap>[0-9]+[A-Z]*)_(?P<ver>[0-9]{14}|-{14})_"
    r"(?P<lang>en|zh-Hant|zh-Hans)_(?P<cp>[cp])\.xml$",
    re.I,
)


@dataclass
class InstrumentCensus:
    instrument_id: str
    kind: str
    language: str
    title: str | None = None
    current_files: int = 0
    past_files: int = 0
    version_timestamps: list[str] = field(default_factory=list)
    total_bytes: int = 0
    files: list[str] = field(default_factory=list)
    top_level_section_counts: list[int] = field(default_factory=list)
    has_schedule: bool = False
    has_table: bool = False
    has_img: bool = False
    has_form: bool = False
    has_sup_sub: bool = False
    parse_errors: list[str] = field(default_factory=list)
    renderability_concerns: list[str] = field(default_factory=list)
    xml_validation_status: str = "not_validated_no_local_xsd"


def parse_filename(name: str) -> dict | None:
    m = FILENAME_RE.match(Path(name).name)
    if not m:
        return None
    return m.groupdict()


def _text(el) -> str:
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def extract_title(root) -> str | None:
    for el in root.iter():
        if local_name(el.tag) in {"shortTitle", "docTitle", "docName"}:
            t = "".join(el.itertext()).strip()
            if t:
                return t
    return None


def count_top_level_sections(root) -> int:
    """Count section elements that are not nested inside another section."""
    count = 0
    parent_map = {c: p for p in root.iter() for c in p}
    for el in root.iter():
        if local_name(el.tag) != "section":
            continue
        p = parent_map.get(el)
        # Climb until non-wrapper or section ancestor found
        nested = False
        while p is not None:
            ln = local_name(p.tag)
            if ln == "section":
                nested = True
                break
            p = parent_map.get(p)
        if not nested:
            count += 1
    return count


def structure_flags(root) -> dict[str, bool]:
    flags = {
        "has_schedule": False,
        "has_table": False,
        "has_img": False,
        "has_form": False,
        "has_sup_sub": False,
    }
    for el in root.iter():
        ln = local_name(el.tag)
        if ln == "schedule":
            flags["has_schedule"] = True
        elif ln in {"layout", "header", "row", "column"}:
            flags["has_table"] = True
        elif ln == "img":
            flags["has_img"] = True
        elif ln in {"fillIn", "checkBox"}:
            flags["has_form"] = True
        elif ln in {"sup", "sub"}:
            flags["has_sup_sub"] = True
    return flags


def census_directory(
    dir_path: Path, languages: set[str] | None = None
) -> dict[str, InstrumentCensus]:
    languages = languages or {"en"}
    by_key: dict[str, InstrumentCensus] = {}
    for path in sorted(dir_path.glob("*.xml")):
        meta = parse_filename(path.name)
        if not meta:
            continue
        if meta["lang"] not in languages:
            continue
        instrument_id = f"{meta['kind']}:{meta['cap']}"
        key = f"{instrument_id}:{meta['lang']}"
        row = by_key.get(key)
        if row is None:
            row = InstrumentCensus(
                instrument_id=instrument_id,
                kind=meta["kind"],
                language=meta["lang"],
            )
            by_key[key] = row
        row.files.append(path.name)
        row.total_bytes += path.stat().st_size
        row.version_timestamps.append(meta["ver"])
        if meta["cp"].lower() == "c":
            row.current_files += 1
        else:
            row.past_files += 1
        try:
            root = parse_xml_file(path)
            if row.title is None:
                row.title = extract_title(root)
            row.top_level_section_counts.append(count_top_level_sections(root))
            flags = structure_flags(root)
            row.has_schedule = row.has_schedule or flags["has_schedule"]
            row.has_table = row.has_table or flags["has_table"]
            row.has_img = row.has_img or flags["has_img"]
            row.has_form = row.has_form or flags["has_form"]
            row.has_sup_sub = row.has_sup_sub or flags["has_sup_sub"]
            concerns = []
            if flags["has_table"]:
                concerns.append("tables")
            if flags["has_img"]:
                concerns.append("images")
            if flags["has_form"]:
                concerns.append("forms")
            if flags["has_sup_sub"]:
                concerns.append("sup_sub")
            for c in concerns:
                if c not in row.renderability_concerns:
                    row.renderability_concerns.append(c)
        except XmlSecurityError as exc:
            row.parse_errors.append(f"{path.name}: {exc}")
    return by_key


def census_to_jsonable(rows: dict[str, InstrumentCensus]) -> list[dict]:
    out = []
    for key, row in sorted(rows.items()):
        d = asdict(row)
        d["census_key"] = key
        d["unique_versions"] = len(set(row.version_timestamps))
        d["max_top_level_sections"] = (
            max(row.top_level_section_counts) if row.top_level_section_counts else 0
        )
        out.append(d)
    return out


def rank_cap599_family(rows: list[dict]) -> list[dict]:
    """Rank Cap. 599-family instruments by churn/complexity evidence (no selection yet)."""
    ranked = []
    for r in rows:
        if not r["instrument_id"].startswith("cap:599"):
            continue
        score = (
            r.get("unique_versions", 0) * 10
            + r.get("past_files", 0) * 2
            + r.get("max_top_level_sections", 0)
            + (5 if r.get("has_table") else 0)
            + (5 if r.get("has_img") else 0)
            + (3 if r.get("has_form") else 0)
        )
        ranked.append({**r, "rank_score": score})
    ranked.sort(key=lambda x: (-x["rank_score"], x["instrument_id"]))
    return ranked
