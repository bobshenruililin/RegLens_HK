from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.hashutil import sha256_bytes, sha256_file  # noqa: E402
from reglens_worker.ingest import ingest_fixture, load_manifest  # noqa: E402
from reglens_worker.llm import MockLLMProvider  # noqa: E402
from reglens_worker.schema_validate import (  # noqa: E402
    assert_valid_extraction,
    evidence_quotes_supported,
    validate_extraction,
)
from reglens_worker.segment import segment_document  # noqa: E402
from reglens_worker.store import LocalArtifactStore  # noqa: E402


FIXTURES = ROOT / "fixtures"


def test_sha256_stable():
    assert sha256_bytes(b"reglens") == sha256_bytes(b"reglens")
    assert len(sha256_bytes(b"x")) == 64


def test_segment_html_pages():
    path = FIXTURES / "raw/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    assert len(spans) == 3
    assert spans[0].page_no == 1
    assert "Charge:" in spans[0].text
    assert "Finding:" in spans[1].text
    assert spans[0].text_hash != spans[1].text_hash


def test_segment_pdf_pages():
    path = FIXTURES / "raw/mchk/SYN-MCHK-PDF-001.pdf"
    spans = segment_document(path)
    assert len(spans) >= 1
    assert "SYNTHETIC FIXTURE PDF" in spans[0].text or "Charge" in spans[0].text


def test_mock_extraction_schema_and_evidence():
    path = FIXTURES / "raw/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    digest = sha256_file(path)
    payload = MockLLMProvider().extract(
        document_sha256=digest,
        regulator_code="MCHK",
        spans=spans,
    )
    errors = validate_extraction(payload)
    assert errors == [], errors
    assert_valid_extraction(payload)
    page_texts = {s.page_no: s.text for s in spans}
    assert evidence_quotes_supported(payload, page_texts) == []
    assert any(p["prop_type"] == "charge" for p in payload["propositions"])
    legal = [p for p in payload["propositions"] if p["prop_type"] == "legal_test"]
    for p in legal:
        assert p["epistemic_class"] == "interpretation"


def test_schema_rejects_missing_evidence():
    bad = {
        "schema_version": "1.0.0",
        "document_sha256": "a" * 64,
        "extractor": {
            "pipeline_version": "x",
            "model_provider": "mock",
            "model_version": "1",
            "prompt_version": "1",
        },
        "propositions": [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "prop_type": "charge",
                "epistemic_class": "fact",
                "claim_text": "Something",
                "confidence": 0.5,
                "evidence": [],
            }
        ],
    }
    errors = validate_extraction(bad)
    assert errors


def test_ingest_idempotent(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    rows = load_manifest(FIXTURES / "manifests/m1.jsonl")
    row = rows[0]
    d1 = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    d2 = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    assert d1["document_sha256"] == d2["document_sha256"]
    # blob stored once
    blob_dir = tmp_path / "objects" / "sha256" / d1["document_sha256"][:2]
    matches = list(blob_dir.glob(d1["document_sha256"]))
    assert len(matches) == 1
    assert all(p.get("published") for p in d1["propositions"])
    assert all(p["evidence"] for p in d1["propositions"])


def test_provenance_links_resolve_to_pages(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    pages = {p["page_no"]: p["text"] for p in decision["pages"]}
    for prop in decision["propositions"]:
        for ev in prop["evidence"]:
            assert ev["span_id"]
            assert ev["quote"] in pages[ev["page_no"]]
            assert any(pg["span_id"] == ev["span_id"] for pg in decision["pages"])
