from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from reglens_worker.determinism import span_stable_id
from reglens_worker.llm import LLMProvider, MockLLMProvider
from reglens_worker.segment import PageSpan


class CriticResult(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    NO_EVIDENCE = "no_evidence"
    INVALID_EVIDENCE = "invalid_evidence"


@dataclass(frozen=True)
class BoundedPipelineRun:
    sections: tuple[Mapping[str, object], ...]
    extraction: Mapping[str, Any]
    critic_outputs: tuple[Mapping[str, object], ...]
    reconciliation: Mapping[str, object]


def run_bounded_pipeline(
    *,
    document_sha256: str,
    regulator_code: str,
    spans: Sequence[PageSpan],
    metadata: dict[str, Any] | None = None,
    provider: LLMProvider | None = None,
) -> BoundedPipelineRun:
    section_labels = classify_sections(spans)
    extractor = provider or MockLLMProvider()
    extracted = extractor.extract(
        document_sha256=document_sha256,
        regulator_code=regulator_code,
        spans=list(spans),
        metadata=metadata,
    )
    resolved = resolve_evidence(extracted, spans=spans, document_sha256=document_sha256)
    critic_outputs = critique_extraction(resolved, spans=spans)
    reconciliation = reconcile(critic_outputs)
    return BoundedPipelineRun(
        sections=section_labels,
        extraction=_freeze_json(resolved),
        critic_outputs=critic_outputs,
        reconciliation=reconciliation,
    )


def classify_sections(spans: Sequence[PageSpan]) -> tuple[Mapping[str, object], ...]:
    labels: list[Mapping[str, object]] = []
    for span in spans:
        found: list[str] = []
        text = span.text.lower()
        for label, keywords in _SECTION_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                found.append(label)
        labels.append(
            _freeze_json(
                {
                    "page_no": span.page_no,
                    "span_type": span.span_type,
                    "labels": tuple(found or ["unclassified"]),
                }
            )
        )
    return tuple(labels)


def resolve_evidence(
    extraction: Mapping[str, Any],
    *,
    spans: Sequence[PageSpan],
    document_sha256: str,
) -> dict[str, Any]:
    resolved = copy.deepcopy(dict(extraction))
    page_to_span = {span.page_no: span for span in spans}
    for prop in resolved.get("propositions", []):
        if not isinstance(prop, dict):
            continue
        for evidence in prop.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            span = page_to_span.get(evidence.get("page_no"))
            if span is None:
                continue
            evidence.setdefault("span_id", span_stable_id(document_sha256, span))
            quote = evidence.get("quote")
            if not isinstance(quote, str) or not quote:
                continue
            idx = span.text.find(quote)
            if idx >= 0:
                evidence["char_start"] = idx
                evidence["char_end"] = idx + len(quote)
            else:
                evidence.setdefault("char_start", None)
                evidence.setdefault("char_end", None)
    return resolved


def critique_extraction(
    extraction: Mapping[str, Any],
    *,
    spans: Sequence[PageSpan],
) -> tuple[Mapping[str, object], ...]:
    page_to_span = {span.page_no: span for span in spans}
    outputs: list[Mapping[str, object]] = []
    propositions = extraction.get("propositions", [])
    if not isinstance(propositions, list):
        return (
            _freeze_json(
                {
                    "client_ref": None,
                    "result": CriticResult.INVALID_EVIDENCE.value,
                    "reasons": ("propositions_not_list",),
                    "evidence": (),
                }
            ),
        )

    for prop in propositions:
        if not isinstance(prop, Mapping):
            continue
        client_ref = prop.get("client_ref")
        evidence_items = prop.get("evidence", [])
        if not isinstance(evidence_items, list) or not evidence_items:
            outputs.append(
                _freeze_json(
                    {
                        "client_ref": client_ref,
                        "result": CriticResult.NO_EVIDENCE.value,
                        "reasons": ("no_evidence",),
                        "evidence": (),
                    }
                )
            )
            continue

        evidence_results = [_critique_evidence(ev, page_to_span) for ev in evidence_items]
        supported_count = sum(1 for item in evidence_results if item["supported"] is True)
        if supported_count == len(evidence_results):
            result = CriticResult.SUPPORTED
            reasons: tuple[str, ...] = ()
        elif supported_count > 0:
            result = CriticResult.PARTIALLY_SUPPORTED
            reasons = ("some_quotes_not_found_in_spans",)
        else:
            result = CriticResult.UNSUPPORTED
            reasons = ("quote_not_found_in_spans",)
        outputs.append(
            _freeze_json(
                {
                    "client_ref": client_ref,
                    "result": result.value,
                    "reasons": reasons,
                    "evidence": tuple(evidence_results),
                }
            )
        )
    return tuple(outputs)


def reconcile(critic_outputs: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    blocking = tuple(
        output.get("client_ref")
        for output in critic_outputs
        if output.get("result") != CriticResult.SUPPORTED.value
    )
    return _freeze_json(
        {
            "auto_accept": False,
            "requires_human_review": True,
            "accepted_client_refs": (),
            "blocking_client_refs": blocking,
            "reason": "bounded_pipeline_never_auto_accepts",
        }
    )


def _critique_evidence(
    evidence: object,
    page_to_span: Mapping[int, PageSpan],
) -> Mapping[str, object]:
    if not isinstance(evidence, Mapping):
        return _freeze_json(
            {"page_no": None, "quote": None, "supported": False, "reason": "invalid_evidence"}
        )
    page_no = evidence.get("page_no")
    quote = evidence.get("quote")
    if not isinstance(page_no, int) or not isinstance(quote, str) or not quote:
        return _freeze_json(
            {"page_no": page_no, "quote": quote, "supported": False, "reason": "invalid_evidence"}
        )
    span = page_to_span.get(page_no)
    if span is None:
        return _freeze_json(
            {"page_no": page_no, "quote": quote, "supported": False, "reason": "page_not_found"}
        )
    supported = quote in span.text or _collapse_ws(quote) in _collapse_ws(span.text)
    return _freeze_json(
        {
            "page_no": page_no,
            "quote": quote,
            "supported": supported,
            "reason": "supported" if supported else "quote_not_found",
        }
    )


def _collapse_ws(text: str) -> str:
    return " ".join(text.split())


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(val) for key, val in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze_json(item) for item in value)
    return value


_SECTION_KEYWORDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "charge": ("charge", "allegation"),
        "finding": ("finding", "proved", "guilty"),
        "sanction": ("order", "sanction", "warning letter", "removed from"),
        "factor": ("mitigating", "aggravating", "remorse", "disciplinary record"),
        "authority": (" v. ", "authority", "cited"),
    }
)
