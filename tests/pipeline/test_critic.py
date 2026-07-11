from __future__ import annotations

import pytest

from reglens_worker.hashutil import sha256_text
from reglens_worker.pipeline.bounded import CriticResult, critique_extraction, reconcile
from reglens_worker.segment import PageSpan


def test_critic_marks_unsupported_when_quote_not_in_spans():
    spans = [_span(1, "The charge is proved.")]
    extraction = {
        "propositions": [
            {
                "client_ref": "finding-1",
                "evidence": [{"page_no": 1, "quote": "The charge is not proved."}],
            }
        ]
    }

    outputs = critique_extraction(extraction, spans=spans)

    assert outputs[0]["result"] == CriticResult.UNSUPPORTED.value
    assert outputs[0]["reasons"] == ("quote_not_found_in_spans",)
    assert outputs[0]["evidence"][0]["supported"] is False


def test_critic_marks_partially_supported_for_mixed_evidence():
    spans = [_span(1, "Charge proved. Sanction imposed.")]
    extraction = {
        "propositions": [
            {
                "client_ref": "sanction-1",
                "evidence": [
                    {"page_no": 1, "quote": "Sanction imposed."},
                    {"page_no": 1, "quote": "Missing quote."},
                ],
            }
        ]
    }

    outputs = critique_extraction(extraction, spans=spans)

    assert outputs[0]["result"] == CriticResult.PARTIALLY_SUPPORTED.value


def test_critic_output_is_immutable_data_structure():
    spans = [_span(1, "The charge is proved.")]
    extraction = {
        "propositions": [
            {
                "client_ref": "finding-1",
                "evidence": [{"page_no": 1, "quote": "The charge is proved."}],
            }
        ]
    }

    outputs = critique_extraction(extraction, spans=spans)
    with pytest.raises(TypeError):
        outputs[0]["result"] = CriticResult.UNSUPPORTED.value
    with pytest.raises(TypeError):
        outputs[0]["evidence"][0]["supported"] = False


def test_reconcile_never_auto_accepts_supported_outputs():
    spans = [_span(1, "The charge is proved.")]
    outputs = critique_extraction(
        {
            "propositions": [
                {
                    "client_ref": "finding-1",
                    "evidence": [{"page_no": 1, "quote": "The charge is proved."}],
                }
            ]
        },
        spans=spans,
    )

    result = reconcile(outputs)

    assert result["auto_accept"] is False
    assert result["requires_human_review"] is True
    assert result["accepted_client_refs"] == ()


def _span(page_no: int, text: str) -> PageSpan:
    return PageSpan(
        page_no=page_no,
        span_type="page",
        text=text,
        char_start=0,
        char_end=len(text),
        text_hash=sha256_text(text),
        source_page_no=page_no,
    )
