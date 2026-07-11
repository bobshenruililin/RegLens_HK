from __future__ import annotations

from reglens_worker.hashutil import sha256_text
from reglens_worker.pipeline.bounded import CriticResult, run_bounded_pipeline
from reglens_worker.pipeline.ontology_v3 import (
    AuthorityFields,
    ChargeFields,
    FactorFields,
    FindingFields,
    SanctionFields,
)
from reglens_worker.segment import PageSpan


def test_bounded_pipeline_runs_mock_extract_and_never_auto_accepts():
    text = (
        "Case No: SYN-MCHK-BOUNDED-001\n"
        "Charge: The Defendant failed to keep adequate records.\n"
        "Medical Registration Ordinance, Cap. 161\n"
        "Finding: the charge is proved.\n"
        "Order: The Defendant be served with a warning letter.\n"
    )
    spans = [_span(1, text)]

    run = run_bounded_pipeline(
        document_sha256="a" * 64,
        regulator_code="MCHK",
        spans=spans,
    )

    assert run.extraction["extractor"]["model_provider"] == "mock"
    assert run.sections[0]["labels"] == ("charge", "finding", "sanction")
    assert {item["result"] for item in run.critic_outputs} == {CriticResult.SUPPORTED.value}
    assert run.reconciliation["auto_accept"] is False
    assert run.reconciliation["requires_human_review"] is True
    assert run.reconciliation["accepted_client_refs"] == ()


def test_ontology_v3_helpers_drop_empty_fields():
    assert ChargeFields("A charge", particulars=("one",)).to_structured() == {
        "charge_text": "A charge",
        "particulars": ("one",),
    }
    assert FindingFields("proved", charge_ref="charge-1").to_structured() == {
        "outcome": "proved",
        "charge_ref": "charge-1",
    }
    assert SanctionFields("warning letter", suspended=False).to_structured() == {
        "order_text": "warning letter",
        "suspended": False,
    }
    assert FactorFields("mitigating", "clear record").to_structured() == {
        "polarity": "mitigating",
        "factor_text": "clear record",
    }
    assert AuthorityFields("Dr X v Medical Council").to_structured() == {
        "citation": "Dr X v Medical Council"
    }


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
