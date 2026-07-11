from __future__ import annotations

import pytest

from reglens_worker.ocr import OCRConfigurationError, ocr_document
from reglens_worker.ocr.tesseract import _spans_from_stdout


def test_ocr_provider_none_returns_no_spans(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("embedded source text", encoding="utf-8")
    monkeypatch.setenv("OCR_PROVIDER", "none")

    report = ocr_document(source)

    assert report.provider == "none"
    assert report.spans == ()
    assert report.warnings == ("ocr_disabled",)
    assert source.read_text(encoding="utf-8") == "embedded source text"


def test_missing_tesseract_only_fails_when_selected(tmp_path):
    source = tmp_path / "scan.png"
    source.write_bytes(b"not a real image")

    report = ocr_document(source, provider="none", tesseract_bin="definitely-missing-tesseract")
    assert report.spans == ()

    with pytest.raises(OCRConfigurationError, match="requires the tesseract binary"):
        ocr_document(source, provider="tesseract", tesseract_bin="definitely-missing-tesseract")


def test_ocr_stdout_page_limit_enforced():
    with pytest.raises(OCRConfigurationError, match="page count"):
        _spans_from_stdout("one\ftwo", provider="tesseract", max_pages=1)


def test_ocr_stdout_builds_separate_spans():
    spans = _spans_from_stdout("first page\fsecond page", provider="tesseract", max_pages=2)

    assert [s.page_no for s in spans] == [1, 2]
    assert {s.span_type for s in spans} == {"ocr_page"}
    assert all(s.provider == "tesseract" for s in spans)
