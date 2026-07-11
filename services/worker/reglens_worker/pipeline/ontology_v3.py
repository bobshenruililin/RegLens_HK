from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Literal

StructuredValue = str | int | float | bool | None | tuple["StructuredValue", ...]


@dataclass(frozen=True)
class ChargeFields:
    charge_text: str
    instrument: str | None = None
    particulars: tuple[str, ...] = ()

    def to_structured(self) -> Mapping[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class FindingFields:
    outcome: Literal["proved", "not_proved", "partly_proved", "stated"]
    finding_text: str | None = None
    charge_ref: str | None = None
    reasons: tuple[str, ...] = ()

    def to_structured(self) -> Mapping[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class SanctionFields:
    order_text: str
    sanction_type: str | None = None
    duration: str | None = None
    suspended: bool | None = None
    effective_date: str | None = None

    def to_structured(self) -> Mapping[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class FactorFields:
    polarity: Literal["mitigating", "aggravating"]
    factor_text: str
    category: str | None = None
    weight: Literal["low", "medium", "high"] | None = None

    def to_structured(self) -> Mapping[str, Any]:
        return _clean(asdict(self))


@dataclass(frozen=True)
class AuthorityFields:
    citation: str
    proposition: str | None = None
    court: str | None = None
    neutral_citation: str | None = None

    def to_structured(self) -> Mapping[str, Any]:
        return _clean(asdict(self))


def _clean(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: val
        for key, val in value.items()
        if val is not None and val != () and val != [] and val != {}
    }
