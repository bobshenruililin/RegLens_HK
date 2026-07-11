"""Medical Council of Hong Kong source adapter for synthetic RC3 fixtures."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .base import BaseSourceAdapter, FetchHtml, SourceItem

_SPLIT_RE = re.compile(r"\s*(?:;|\||\n|,|\s/\s)\s*")
_SPACE_RE = re.compile(r"\s+")


class MchkAdapter(BaseSourceAdapter):
    """Parse MCHK judgment index HTML into normalized source items."""

    source_id = "mchk_judgments"
    adapter_id = "mchk_html_index"
    adapter_version = "1.0.0"

    def discover(
        self,
        html: str,
        *,
        base_url: str,
        fetch_html: FetchHtml | None = None,
    ) -> Sequence[SourceItem]:
        soup = BeautifulSoup(html, "lxml")
        pages: list[tuple[str, str]] = [(base_url, html)]
        if fetch_html is not None:
            for href in _year_links(soup):
                page_url = urljoin(base_url, href)
                pages.append((page_url, fetch_html(page_url)))

        items: list[SourceItem] = []
        seen: set[str] = set()
        for page_url, page_html in pages:
            page_soup = BeautifulSoup(page_html, "lxml")
            for row in _judgment_rows(page_soup):
                item = self.normalize_item(_raw_row(row, page_url))
                if item.source_item_key in seen:
                    continue
                seen.add(item.source_item_key)
                items.append(item)
        return items

    def normalize_item(self, raw: Mapping[str, Any]) -> SourceItem:
        case_refs = tuple(_split_values(str(raw.get("case_refs") or "")))
        inquiry_dates = tuple(_split_values(str(raw.get("inquiry_dates") or "")))
        first_ref = case_refs[0] if case_refs else str(raw.get("source_item_key") or "")
        source_item_key = _key(first_ref)
        metadata = {
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "regulator_code": "MCHK",
        }
        if raw.get("metadata"):
            metadata.update(dict(raw["metadata"]))

        return SourceItem(
            source_id=self.source_id,
            source_item_key=source_item_key,
            title=_clean(raw.get("title")),
            source_url=_clean(raw.get("source_url")),
            document_url=_clean(raw.get("document_url")),
            case_refs=case_refs,
            inquiry_dates=inquiry_dates,
            judgment_date=_clean(raw.get("judgment_date")),
            published_date=_clean(raw.get("published_date")),
            metadata=metadata,
            caveats=tuple(raw.get("caveats", ())),
        )


def _year_links(soup: BeautifulSoup) -> list[str]:
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        classes = set(anchor.get("class", []))
        href = str(anchor["href"])
        text = anchor.get_text(" ", strip=True)
        if "year-link" in classes or anchor.get("data-year") or re.search(r"\b20\d{2}\b", text):
            links.append(href)
    return links


def _judgment_rows(soup: BeautifulSoup) -> list[Tag]:
    rows: list[Tag] = []
    for row in soup.select("[data-judgment-row], tr.judgment-row, table#judgments tbody tr"):
        if isinstance(row, Tag):
            rows.append(row)
    return rows


def _raw_row(row: Tag, page_url: str) -> dict[str, Any]:
    pdf_link = _first_link(row, ".pdf-link")
    if pdf_link is None:
        pdf_link = _first_pdf_link(row)
    detail_link = _first_link(row, ".detail-link")
    case_refs = row.get("data-case-refs") or _text(row, ".case-refs") or _cell_text(row, 0)

    return {
        "source_item_key": case_refs,
        "title": _text(row, ".title") or _cell_text(row, 1),
        "source_url": urljoin(page_url, detail_link) if detail_link else page_url,
        "document_url": urljoin(page_url, pdf_link) if pdf_link else None,
        "case_refs": case_refs,
        "inquiry_dates": row.get("data-inquiry-dates") or _text(row, ".inquiry-dates"),
        "judgment_date": row.get("data-judgment-date") or _text(row, ".judgment-date"),
        "published_date": row.get("data-published-date") or _text(row, ".published-date"),
        "metadata": {"source_page_url": page_url},
    }


def _first_link(row: Tag, selector: str) -> str | None:
    anchor = row.select_one(f"a{selector}[href]")
    if isinstance(anchor, Tag):
        return str(anchor["href"])
    return None


def _first_pdf_link(row: Tag) -> str | None:
    for anchor in row.find_all("a", href=True):
        href = str(anchor["href"])
        if href.lower().split("?", 1)[0].endswith(".pdf"):
            return href
    return None


def _text(row: Tag, selector: str) -> str | None:
    element = row.select_one(selector)
    if element is None:
        return None
    return element.get_text(" ", strip=True)


def _cell_text(row: Tag, index: int) -> str | None:
    cells = row.find_all(["td", "th"])
    if index >= len(cells):
        return None
    return cells[index].get_text(" ", strip=True)


def _split_values(value: str) -> list[str]:
    out: list[str] = []
    for part in _SPLIT_RE.split(value):
        cleaned = _clean(part)
        if cleaned:
            out.append(cleaned)
    return out


def _clean(value: object) -> str | None:
    if value is None:
        return None
    cleaned = _SPACE_RE.sub(" ", str(value).replace("\xa0", " ")).strip()
    return cleaned or None


def _key(value: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise ValueError("MCHK source row is missing a case reference")
    return re.sub(r"[^A-Za-z0-9._-]+", "-", cleaned).strip("-").lower()
