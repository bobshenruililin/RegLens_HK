"""Stage C canonicalization, reconstruction, and determinism tests."""

from __future__ import annotations

from pathlib import Path

from lawtrace_worker.canonical import canonicalize_section
from lawtrace_worker.security.xml_safe import parse_xml_file
from lawtrace_worker.stage_b import iter_top_level_sections, match_sections, parse_instrument_file
from lawtrace_worker.stage_c import determinism_check, evaluate_cap_614


def test_canonical_preserves_boundaries_and_is_deterministic() -> None:
    path = Path("fixtures/lawtrace/cap_614/cap_614_20120116000000_en_p.xml")
    root = parse_xml_file(path)
    sec = iter_top_level_sections(root)[0]
    a = canonicalize_section(sec)
    b = canonicalize_section(sec)
    assert a.sha256() == b.sha256()
    kinds = [t.kind for t in a.tokens]
    assert "SECTION_OPEN" in kinds and "SECTION_CLOSE" in kinds
    assert "NUM" in kinds and "HEADING" in kinds
    assert any(k.startswith("SUBSECTION_") for k in kinds)


def test_reconstruction_invariant_all_cap_614_same_id_pairs() -> None:
    result = evaluate_cap_614(Path("fixtures/lawtrace/cap_614"))
    assert result["supported_pairs"] > 0
    assert result["supported_reconstruction_ok"] == result["supported_pairs"]
    assert result["reconstruction_failures"] == []
    assert result["gate_pass"] is True
    for c in result["comparisons"]:
        if c["relationship"] in {"added", "removed"}:
            continue
        assert c["reconstruction_ok"] is True
        assert c["full_token_diff"]["a_hash"]
        assert c["section_id"]
        # Identity displayed matches source @id on both sides for same-ID pairs
        assert c["canonical_a"]["element_id"] == c["canonical_b"]["element_id"] == c["section_id"]


def test_status_only_not_represented_as_textual_amendment() -> None:
    result = evaluate_cap_614(Path("fixtures/lawtrace/cap_614"))
    status_only = [c for c in result["comparisons"] if c["relationship"] == "status_changed"]
    assert status_only, "expected Cap. 614 status-only examples"
    for c in status_only:
        assert c["legal_text_diff"]["equal"] is True
        assert c["metadata_diff"]["equal"] is False


def test_determinism_two_runs() -> None:
    det = determinism_check(Path("fixtures/lawtrace/cap_614"))
    assert det["pass"] is True


def test_no_nested_identity_assignment_in_canonical() -> None:
    """Nested subsection/paragraph markers exist, but matching remains top-level @id only."""
    fixture_dir = Path("fixtures/lawtrace/cap_614")
    paths = sorted(fixture_dir.glob("*.xml"))
    parsed = [parse_instrument_file(p, archive_sha256="t") for p in paths]
    parsed.sort(key=lambda x: x["filename_meta"]["ver"])
    m = match_sections(parsed[0]["sections"], parsed[1]["sections"])
    assert all(e["match_method"] in {"id", "unmatched"} for e in m["edges"])
