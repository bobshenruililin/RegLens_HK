from __future__ import annotations

from pathlib import Path

from reglens_worker.sources.adapters.mchk import MchkAdapter

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "source_html" / "mchk"
BASE_URL = "https://www.mchk.org.hk/english/complaint/disciplinary.php?type=j"


def test_mchk_adapter_parses_year_page_and_multi_value_fields() -> None:
    adapter = MchkAdapter()
    root_html = (FIXTURE_DIR / "index_root.synthetic.html").read_text(encoding="utf-8")

    def fetch_html(url: str) -> str:
        assert url.endswith("year_page.synthetic.html")
        return (FIXTURE_DIR / "year_page.synthetic.html").read_text(encoding="utf-8")

    items = list(adapter.discover(root_html, base_url=BASE_URL, fetch_html=fetch_html))

    assert len(items) == 2
    first = items[0]
    assert first.source_id == "mchk_judgments"
    assert first.source_item_key == "syn-src-mchk-001"
    assert first.case_refs == ("SYN-SRC-MCHK-001", "SYN-SRC-MCHK-001A")
    assert first.inquiry_dates == ("2026-01-05", "2026-01-06")
    assert first.judgment_date == "2026-02-01"
    assert first.document_url == "https://www.mchk.org.hk/english/complaint/SYN-SRC-MCHK-001.pdf"


def test_mchk_adapter_does_not_invent_judgment_date_from_inquiry_date() -> None:
    adapter = MchkAdapter()
    html = (FIXTURE_DIR / "year_page.synthetic.html").read_text(encoding="utf-8")
    items = list(
        adapter.discover(
            html,
            base_url="https://www.mchk.org.hk/english/complaint/year_page.synthetic.html",
        )
    )

    second = items[1]
    assert second.case_refs == ("SYN-SRC-MCHK-002",)
    assert second.inquiry_dates == ("2026-03-10",)
    assert second.judgment_date is None
