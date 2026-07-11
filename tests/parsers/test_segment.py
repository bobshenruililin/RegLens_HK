from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.segment import segment_html  # noqa: E402


def test_form_feed_split(tmp_path: Path):
    p = tmp_path / "x.html"
    p.write_text(
        "<html><body><p>Page one charge</p>\f<p>Page two finding</p></body></html>",
        encoding="utf-8",
    )
    spans = segment_html(p)
    assert len(spans) == 2
    assert spans[0].page_no == 1
    assert "Page one" in spans[0].text
