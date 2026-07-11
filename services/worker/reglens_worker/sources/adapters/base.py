"""Shared adapter interfaces and source item models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class SourceItem:
    """Normalized metadata for one regulator source item."""

    source_id: str
    source_item_key: str
    title: str | None
    source_url: str | None
    document_url: str | None
    case_refs: tuple[str, ...] = ()
    inquiry_dates: tuple[str, ...] = ()
    judgment_date: str | None = None
    published_date: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    caveats: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdapterAcquisition:
    """Adapter-level acquisition request/result metadata."""

    item: SourceItem
    fetch_result: Any


FetchHtml = Callable[[str], str]


@runtime_checkable
class SourceAdapter(Protocol):
    """Protocol implemented by source-specific discovery/acquisition adapters."""

    source_id: str
    adapter_id: str
    adapter_version: str

    def discover(
        self,
        html: str,
        *,
        base_url: str,
        fetch_html: FetchHtml | None = None,
    ) -> Sequence[SourceItem]:
        """Parse index HTML and return normalized source items."""

    def normalize_item(self, raw: Mapping[str, Any]) -> SourceItem:
        """Normalize parser-specific raw fields into a stable SourceItem."""

    def acquire(self, item: SourceItem, http_client: Any) -> Any:
        """Acquire document bytes for `item` with a policy-aware HTTP client."""


class BaseSourceAdapter(ABC):
    """Small ABC for adapters that prefer inheritance over structural typing."""

    source_id: str
    adapter_id: str
    adapter_version: str

    @abstractmethod
    def discover(
        self,
        html: str,
        *,
        base_url: str,
        fetch_html: FetchHtml | None = None,
    ) -> Sequence[SourceItem]:
        """Parse index HTML and return normalized source items."""

    @abstractmethod
    def normalize_item(self, raw: Mapping[str, Any]) -> SourceItem:
        """Normalize parser-specific raw fields into a stable SourceItem."""

    def acquire(self, item: SourceItem, http_client: Any) -> Any:
        """Acquire the item's linked document, if any."""
        if not item.document_url:
            raise ValueError(f"source item has no document_url: {item.source_item_key}")
        return http_client.fetch(item.document_url, purpose="document")
