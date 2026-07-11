from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .hashutil import sha256_text

DEFAULT_MAX_BYTES = int(os.environ.get("REGLENS_MAX_INPUT_BYTES", str(25 * 1024 * 1024)))
DEFAULT_MAX_PDF_PAGES = int(os.environ.get("REGLENS_MAX_PDF_PAGES", "200"))


@dataclass(frozen=True)
class PageSpan:
    page_no: int
    span_type: str
    text: str
    char_start: int | None
    char_end: int | None
    text_hash: str
    source_page_no: int
    printed_page_label: str | None = None
    quality: str = "good"


@dataclass
class SegmentationReport:
    spans: list[PageSpan]
    warnings: list[str] = field(default_factory=list)
    empty_page_ratio: float = 0.0
    overall_quality: str = "good"


_FORM_FEED = "\f"


class ParserSafetyError(ValueError):
    pass


def _normalize_ws(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _page_quality(text: str) -> str:
    if not text.strip():
        return "empty"
    if len(text.strip()) < 40:
        return "low"
    return "good"


def segment_pdf(
    path: Path,
    *,
    max_pages: int = DEFAULT_MAX_PDF_PAGES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> SegmentationReport:
    size = path.stat().st_size
    if size > max_bytes:
        raise ParserSafetyError(f"PDF exceeds max size {max_bytes} bytes: {size}")
    reader = PdfReader(str(path))
    if len(reader.pages) > max_pages:
        raise ParserSafetyError(f"PDF exceeds max page count {max_pages}: {len(reader.pages)}")
    spans: list[PageSpan] = []
    warnings: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        text = _normalize_ws(raw)
        quality = _page_quality(text)
        if quality == "empty":
            warnings.append(f"pdf_page_{i}_empty")
        spans.append(
            PageSpan(
                page_no=i,
                span_type="page",
                text=text,
                char_start=0 if text else None,
                char_end=len(text) if text else None,
                text_hash=sha256_text(text),
                source_page_no=i,
                printed_page_label=None,
                quality=quality,
            )
        )
    return _report(spans, warnings)


def _html_fragment_text(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body = soup.body or soup
    return _normalize_ws(body.get_text("\n", strip=True))


def segment_html(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> SegmentationReport:
    size = path.stat().st_size
    if size > max_bytes:
        raise ParserSafetyError(f"HTML exceeds max size {max_bytes} bytes: {size}")
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    marked = soup.select("[data-page]")
    if marked:
        seen: set[int] = set()
        spans: list[PageSpan] = []
        warnings: list[str] = []
        for node in marked:
            raw_val = node.get("data-page")
            try:
                page_no = int(raw_val)  # type: ignore[arg-type]
            except (TypeError, ValueError) as exc:
                raise ParserSafetyError(f"invalid data-page value: {raw_val!r}") from exc
            if page_no < 1:
                raise ParserSafetyError(f"invalid data-page value: {page_no}")
            if page_no in seen:
                raise ParserSafetyError(f"duplicate data-page value: {page_no}")
            seen.add(page_no)
            text = _normalize_ws(node.get_text("\n", strip=True))
            label = node.get("data-printed-page")
            quality = _page_quality(text)
            if quality == "empty":
                warnings.append(f"html_page_{page_no}_empty")
            spans.append(
                PageSpan(
                    page_no=page_no,
                    span_type="page",
                    text=text,
                    char_start=0 if text else None,
                    char_end=len(text) if text else None,
                    text_hash=sha256_text(text),
                    source_page_no=page_no,
                    printed_page_label=str(label) if label is not None else None,
                    quality=quality,
                )
            )
        spans.sort(key=lambda s: s.page_no)
        return _report(spans, warnings)

    ff_warnings: list[str] = []
    if _FORM_FEED in html:
        parts = html.split(_FORM_FEED)
        spans = []
        for i, part in enumerate(parts, start=1):
            text = _html_fragment_text(part)
            if not text:
                ff_warnings.append(f"html_formfeed_part_{i}_empty")
                continue
            spans.append(
                PageSpan(
                    page_no=len(spans) + 1,
                    span_type="page",
                    text=text,
                    char_start=0,
                    char_end=len(text),
                    text_hash=sha256_text(text),
                    source_page_no=len(spans) + 1,
                    quality=_page_quality(text),
                )
            )
        if spans:
            return _report(spans, ff_warnings)

    body = soup.body or soup
    full = _normalize_ws(body.get_text("\n", strip=True))
    return _report(
        [
            PageSpan(
                page_no=1,
                span_type="page",
                text=full,
                char_start=0 if full else None,
                char_end=len(full) if full else None,
                text_hash=sha256_text(full),
                source_page_no=1,
                quality=_page_quality(full),
            )
        ],
        ff_warnings,
    )


def _report(spans: list[PageSpan], warnings: list[str]) -> SegmentationReport:
    if not spans:
        return SegmentationReport(
            spans=[],
            warnings=warnings + ["no_spans"],
            empty_page_ratio=1.0,
            overall_quality="empty",
        )
    empty = sum(1 for s in spans if s.quality == "empty")
    ratio = empty / len(spans)
    nonempty = [s for s in spans if s.quality != "empty"]
    if not nonempty:
        overall = "needs_ocr"
    elif any(s.quality == "low" for s in nonempty) or ratio > 0.25:
        overall = "low"
    else:
        overall = "good"
    if ratio > 0:
        warnings.append(f"empty_page_ratio={ratio:.2f}")
    return SegmentationReport(
        spans=spans,
        warnings=warnings,
        empty_page_ratio=ratio,
        overall_quality=overall,
    )


def segment_document(
    path: Path,
    *,
    max_pages: int = DEFAULT_MAX_PDF_PAGES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[PageSpan]:
    return segment_document_report(path, max_pages=max_pages, max_bytes=max_bytes).spans


def segment_document_report(
    path: Path,
    *,
    max_pages: int = DEFAULT_MAX_PDF_PAGES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> SegmentationReport:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return segment_pdf(path, max_pages=max_pages, max_bytes=max_bytes)
    if suffix in {".html", ".htm"}:
        return segment_html(path, max_bytes=max_bytes)
    raise ValueError(f"Unsupported fixture type: {suffix}")


def text_quality(spans: list[PageSpan]) -> str:
    return _report(spans, []).overall_quality
