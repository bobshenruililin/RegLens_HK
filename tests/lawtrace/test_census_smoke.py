from __future__ import annotations

from pathlib import Path

from lawtrace_worker.census import census_directory, parse_filename


def test_parse_filename_cap614() -> None:
    meta = parse_filename("cap_614_20260601000000_en_c.xml")
    assert meta is not None
    assert meta["cap"] == "614"
    assert meta["lang"] == "en"
    assert meta["cp"] == "c"


def test_census_smoke_on_fixtures() -> None:
    fixture = Path("fixtures/lawtrace/cap_614")
    if not fixture.exists() or not list(fixture.glob("*.xml")):
        return  # acquisition may populate in Stage A scripts
    rows = census_directory(fixture, languages={"en"})
    assert "cap:614:en" in rows
    assert rows["cap:614:en"].current_files + rows["cap:614:en"].past_files >= 1
