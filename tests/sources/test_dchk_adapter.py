from __future__ import annotations

from pathlib import Path

from reglens_worker.sources.adapters.dchk import DCHK_JULY_2018_CAVEAT, DchkAdapter

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "source_html"
    / "dchk"
    / "judgments_table.synthetic.html"
)
BASE_URL = "https://www.dchk.org.hk/en/complaints_disciplinary/judgments.html"


def test_dchk_adapter_parses_table_rows_and_caveat() -> None:
    adapter = DchkAdapter()
    html = FIXTURE.read_text(encoding="utf-8")
    items = list(adapter.discover(html, base_url=BASE_URL))

    assert len(items) == 2
    assert items[0].source_item_key == "syn-src-dchk-001"
    assert items[0].case_refs == ("SYN-SRC-DCHK-001",)
    assert items[0].judgment_date == "2026-05-02"
    assert DCHK_JULY_2018_CAVEAT in items[0].caveats

    assert items[1].case_refs == ("SYN-SRC-DCHK-002", "SYN-SRC-DCHK-002A")
    assert items[1].inquiry_dates == ("2026-06-01", "2026-06-03")
