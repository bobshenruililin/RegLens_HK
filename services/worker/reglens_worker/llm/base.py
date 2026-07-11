from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..segment import PageSpan


class LLMProvider(ABC):
    """Replaceable extraction provider. Milestone 1 uses MockLLMProvider only."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_version(self) -> str: ...

    @property
    @abstractmethod
    def prompt_version(self) -> str: ...

    @abstractmethod
    def extract(
        self,
        *,
        document_sha256: str,
        regulator_code: str,
        spans: list[PageSpan],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a dict conforming to extraction_result.v1.json (pre-validation)."""
