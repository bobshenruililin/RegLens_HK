from __future__ import annotations

from pathlib import Path

from reglens_worker.sources.adapters.health import check_parser_health
from reglens_worker.sources.adapters.mchk import MchkAdapter
from reglens_worker.sources.http_client import RequestBudgetExceededError
from reglens_worker.sources.sync import _required_markers

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


def test_mchk_adapter_parses_live_shaped_year_tables() -> None:
    adapter = MchkAdapter()
    root_html = (FIXTURE_DIR / "index_root.live_shape.synthetic.html").read_text(
        encoding="utf-8"
    )
    year_html = (FIXTURE_DIR / "year_page.live_shape.synthetic.html").read_text(
        encoding="utf-8"
    )
    fetched: list[str] = []

    def fetch_html(url: str) -> str:
        fetched.append(url)
        assert "year=" in url or url.endswith("2018_judgments.htm")
        return year_html

    items = list(adapter.discover(root_html, base_url=BASE_URL, fetch_html=fetch_html))

    assert fetched
    assert len(items) == 3
    first = items[0]
    assert first.case_refs == ("MC 99/001",)
    assert first.inquiry_dates == ("23 January 2024",)
    assert first.judgment_date is None
    assert first.title == "MCHK judgment MC 99/001"
    assert first.document_url.endswith("/PDF/SYN_LIVE_SHAPE_001.pdf")

    second = items[1]
    assert second.case_refs == ("MC 99/002",)
    assert second.inquiry_dates == ("17 April 2023", "9 March 2024")
    assert second.judgment_date is None

    third = items[2]
    assert third.inquiry_dates == (
        "5 November 2024",
        "7 November 2024",
        "4 February 2025",
    )

    health = check_parser_health(
        root_html,
        items,
        required_markers=_required_markers("mchk_judgments"),
    )
    assert health.ok is True
    assert health.case_ref_ratio == 1.0


def test_mchk_adapter_stops_year_fetches_when_request_budget_exceeded() -> None:
    adapter = MchkAdapter()
    root_html = (FIXTURE_DIR / "index_root.live_shape.synthetic.html").read_text(
        encoding="utf-8"
    )
    year_html = (FIXTURE_DIR / "year_page.live_shape.synthetic.html").read_text(
        encoding="utf-8"
    )
    calls = {"n": 0}

    def fetch_html(url: str) -> str:
        calls["n"] += 1
        if calls["n"] > 1:
            raise RequestBudgetExceededError("budget exhausted")
        return year_html

    items = list(adapter.discover(root_html, base_url=BASE_URL, fetch_html=fetch_html))
    assert calls["n"] == 2
    assert len(items) == 3
