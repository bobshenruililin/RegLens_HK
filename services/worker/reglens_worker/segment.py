from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .hashutil import sha256_text


@dataclass(frozen=True)
class PageSpan:
    page_no: int
    span_type: str
    text: str
    char_start: int | None
    char_end: int | None
    text_hash: str


_FORM_FEED = "\f"


def _normalize_ws(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def segment_pdf(path: Path) -> list[PageSpan]:
    reader = PdfReader(str(path))
    spans: list[PageSpan] = []
    for i, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        text = _normalize_ws(raw)
        spans.append(
            PageSpan(
                page_no=i,
                span_type="page",
                text=text,
                char_start=0 if text else None,
                char_end=len(text) if text else None,
                text_hash=sha256_text(text),
            )
        )
    return spans


def _html_fragment_text(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body = soup.body or soup
    return _normalize_ws(body.get_text("\n", strip=True))


def segment_html(path: Path) -> list[PageSpan]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Explicit page markers take priority (fixture-friendly).
    marked = soup.select("[data-page]")
    if marked:
        spans: list[PageSpan] = []
        for node in marked:
            page_no = int(node.get("data-page", "1"))
            text = _normalize_ws(node.get_text("\n", strip=True))
            spans.append(
                PageSpan(
                    page_no=page_no,
                    span_type="page",
                    text=text,
                    char_start=0 if text else None,
                    char_end=len(text) if text else None,
                    text_hash=sha256_text(text),
                )
            )
        return spans

    # Form-feed page breaks are often stripped by HTML parsers; split raw source first.
    if _FORM_FEED in html:
        parts = html.split(_FORM_FEED)
        spans = []
        for i, part in enumerate(parts, start=1):
            text = _html_fragment_text(part)
            if not text:
                continue
            spans.append(
                PageSpan(
                    page_no=len(spans) + 1,
                    span_type="page",
                    text=text,
                    char_start=0,
                    char_end=len(text),
                    text_hash=sha256_text(text),
                )
            )
        if spans:
            return spans

    body = soup.body or soup
    full = _normalize_ws(body.get_text("\n", strip=True))
    return [
        PageSpan(
            page_no=1,
            span_type="page",
            text=full,
            char_start=0 if full else None,
            char_end=len(full) if full else None,
            text_hash=sha256_text(full),
        )
    ]


def segment_document(path: Path) -> list[PageSpan]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return segment_pdf(path)
    if suffix in {".html", ".htm"}:
        return segment_html(path)
    raise ValueError(f"Unsupported fixture type: {suffix}")


def text_quality(spans: list[PageSpan]) -> str:
    if not spans:
        return "empty"
    nonempty = [s for s in spans if s.text.strip()]
    if not nonempty:
        return "needs_ocr"
    avg = sum(len(s.text) for s in nonempty) / len(nonempty)
    if avg < 40:
        return "low"
    return "good"
