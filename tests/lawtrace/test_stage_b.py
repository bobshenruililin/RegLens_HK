from __future__ import annotations

from pathlib import Path

from lawtrace_worker.stage_b import (
    investigate_date_semantics,
    match_sections,
    parse_instrument_file,
)


def test_section_identity_scope_no_nested_identities() -> None:
    fixture = Path("fixtures/lawtrace/cap_614/cap_614_20260601000000_en_c.xml")
    parsed = parse_instrument_file(fixture, archive_sha256="test")
    # Only top-level sections are returned
    assert parsed["top_level_section_count"] == len(parsed["sections"])
    assert parsed["top_level_section_count"] >= 1
    # Nested content exists inside sections but is not separate identities
    assert all(s.get("element_id") for s in parsed["sections"])


def test_date_semantics_fields_remain_distinct() -> None:
    fixture_dir = Path("fixtures/lawtrace/cap_614")
    files = sorted(fixture_dir.glob("*.xml"))[:2]
    parsed = [parse_instrument_file(p, archive_sha256="test") for p in files]
    report = investigate_date_semantics(parsed)
    names = {f["field_name"] for f in report["findings"]}
    assert "download_datetime" in names
    assert "source_version_datetime" in names
    assert "effective_date" in names
    assert "commencement_date" in names
    assert report["conclusion"] == "VERSION_TO_VERSION_COMPARATOR_ONLY"
    # Ensure we did not promote effective_date to usable UI claim
    eff = next(f for f in report["findings"] if f["field_name"] == "effective_date")
    assert eff["may_use_in_ui"] is False


def test_cap_614_id_matching_precision_and_coverage() -> None:
    fixture_dir = Path("fixtures/lawtrace/cap_614")
    parsed = [
        parse_instrument_file(p, archive_sha256="test") for p in sorted(fixture_dir.glob("*.xml"))
    ]
    parsed.sort(key=lambda x: x["filename_meta"]["ver"])
    slots = 0
    matched = 0
    for older, newer in zip(parsed, parsed[1:], strict=False):
        m = match_sections(older["sections"], newer["sections"])
        slots += len(older["sections"])
        matched += len(m["accepted_edges"])
        assert m["counts"]["ambiguous"] == 0
        for e in m["accepted_edges"]:
            if e["match_method"] == "id":
                assert e["older"]["element_id"] == e["newer"]["element_id"]
    assert slots > 0
    assert matched / slots == 1.0
