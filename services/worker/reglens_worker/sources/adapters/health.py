"""Parser health checks for source adapters."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup

from .base import SourceItem


@dataclass(frozen=True)
class ParserHealthReport:
    """Summary of source parser output quality."""

    ok: bool
    item_count: int
    case_ref_ratio: float
    layout_markers_found: tuple[str, ...]
    problems: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "ok": self.ok,
            "item_count": self.item_count,
            "case_ref_ratio": self.case_ref_ratio,
            "layout_markers_found": list(self.layout_markers_found),
            "problems": list(self.problems),
        }


def check_parser_health(
    html: str,
    items: Sequence[SourceItem],
    *,
    required_markers: Iterable[str],
    min_case_ref_ratio: float = 0.8,
) -> ParserHealthReport:
    """Check nonzero output, case-ref coverage, and expected layout markers."""
    soup = BeautifulSoup(html, "lxml")
    markers_found = tuple(selector for selector in required_markers if soup.select_one(selector))
    problems: list[str] = []
    item_count = len(items)
    if item_count == 0:
        problems.append("parser returned zero items")

    with_case_ref = sum(1 for item in items if item.case_refs)
    case_ref_ratio = with_case_ref / item_count if item_count else 0.0
    if item_count and case_ref_ratio < min_case_ref_ratio:
        problems.append(
            f"case_ref_ratio {case_ref_ratio:.2f} below minimum {min_case_ref_ratio:.2f}"
        )

    required = tuple(required_markers)
    if required and not markers_found:
        problems.append("no expected layout markers found")

    return ParserHealthReport(
        ok=not problems,
        item_count=item_count,
        case_ref_ratio=case_ref_ratio,
        layout_markers_found=markers_found,
        problems=tuple(problems),
    )


def assert_parser_health(report: ParserHealthReport) -> ParserHealthReport:
    """Raise ValueError when parser health does not meet RC3 safeguards."""
    if not report.ok:
        raise ValueError("; ".join(report.problems))
    return report
