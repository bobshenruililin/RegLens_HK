from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.contracts import can_publish_proposition  # noqa: E402
from reglens_worker.determinism import (  # noqa: E402
    decision_id_for_sha256,
    document_id_for_sha256,
    job_dedupe_key,
)
from reglens_worker.hashutil import sha256_file  # noqa: E402
from reglens_worker.ingest import ingest_fixture, ingest_manifest, load_manifest  # noqa: E402
from reglens_worker.jobs import FileJobQueue  # noqa: E402
from reglens_worker.llm import MockLLMProvider  # noqa: E402
from reglens_worker.privacy import assert_no_obvious_patient_leak, redact_derived_text  # noqa: E402
from reglens_worker.publication import PublicationError, set_proposition_review  # noqa: E402
from reglens_worker.schema_validate import (  # noqa: E402
    assert_valid_extraction,
    evidence_quotes_supported,
    validate_extraction,
)
from reglens_worker.search import local_search  # noqa: E402
from reglens_worker.segment import segment_document  # noqa: E402
from reglens_worker.store import LocalArtifactStore  # noqa: E402


FIXTURES = ROOT / "fixtures"


def test_sha256_stable():
    from reglens_worker.hashutil import sha256_bytes

    assert sha256_bytes(b"reglens") == sha256_bytes(b"reglens")
    assert len(sha256_bytes(b"x")) == 64


def test_deterministic_ids():
    digest = "a" * 64
    assert document_id_for_sha256(digest) == document_id_for_sha256(digest)
    assert decision_id_for_sha256(digest) == decision_id_for_sha256(digest)
    assert job_dedupe_key(
        job_type="ingest_fixture",
        document_sha256=digest,
        pipeline_version="m1.0.0",
        prompt_version="p",
    ) == job_dedupe_key(
        job_type="ingest_fixture",
        document_sha256=digest,
        pipeline_version="m1.0.0",
        prompt_version="p",
    )


def test_privacy_redaction():
    text = "Charge concerning Patient A and Madam xxx was proved."
    red = redact_derived_text(text)
    assert "Patient A" not in red
    assert "Madam xxx" not in red
    assert_no_obvious_patient_leak(red)


def test_segment_html_pages():
    path = FIXTURES / "raw/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    assert len(spans) == 3
    assert "Charge:" in spans[0].text


def test_segment_pdf_pages():
    path = FIXTURES / "raw/mchk/SYN-MCHK-PDF-001.pdf"
    spans = segment_document(path)
    assert len(spans) >= 1


def test_mock_extraction_schema_and_evidence():
    path = FIXTURES / "raw/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    digest = sha256_file(path)
    payload = MockLLMProvider().extract(
        document_sha256=digest,
        regulator_code="MCHK",
        spans=spans,
    )
    assert validate_extraction(payload) == []
    assert_valid_extraction(payload)
    assert evidence_quotes_supported(payload, {s.page_no: s.text for s in spans}) == []


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
    assert validate_extraction(bad)


def test_ingest_defaults_to_pending(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    d1 = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    d2 = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    assert d1["document_sha256"] == d2["document_sha256"]
    assert all(p["review_status"] == "pending" for p in d1["propositions"])
    assert all(p["published"] is False for p in d1["propositions"])


def test_publication_gate_requires_review_and_evidence(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    prop = decision["propositions"][0]
    assert not can_publish_proposition(
        review_status="pending", evidence=prop["evidence"]
    )
    updated = set_proposition_review(
        store,
        decision_id=decision["id"],
        proposition_id=prop["id"],
        review_status="accepted",
    )
    published = next(p for p in updated["propositions"] if p["id"] == prop["id"])
    assert published["published"] is True

    # Reject path cannot stay published
    updated2 = set_proposition_review(
        store,
        decision_id=decision["id"],
        proposition_id=prop["id"],
        review_status="rejected",
        publish=False,
    )
    rejected = next(p for p in updated2["propositions"] if p["id"] == prop["id"])
    assert rejected["published"] is False


def test_cannot_publish_without_evidence(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    prop = decision["propositions"][0]
    prop["evidence"] = []
    store.save_decision(decision)
    try:
        set_proposition_review(
            store,
            decision_id=decision["id"],
            proposition_id=prop["id"],
            review_status="accepted",
        )
        assert False, "expected PublicationError"
    except PublicationError:
        pass


def test_job_queue_idempotent(tmp_path: Path):
    q = FileJobQueue(tmp_path / "jobs")
    key = job_dedupe_key(
        job_type="ingest_fixture",
        document_sha256="b" * 64,
        pipeline_version="m1.0.0",
        prompt_version="p",
    )
    j1 = q.enqueue("ingest_fixture", key, {"x": 1})
    j2 = q.enqueue("ingest_fixture", key, {"x": 2})
    assert j1.id == j2.id
    assert len(q.list_jobs()) == 1
    claimed = q.claim()
    assert claimed is not None
    q.complete(claimed.id)
    assert q.list_jobs(status="succeeded")


def test_fts_only_published(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    assert local_search(store, query="misconduct") == []
    prop = decision["propositions"][0]
    set_proposition_review(
        store,
        decision_id=decision["id"],
        proposition_id=prop["id"],
        review_status="accepted",
    )
    hits = local_search(store, query=prop["claim_text"].split()[0])
    assert hits
    assert hits[0].decision_id == decision["id"]


def test_provenance_links_resolve_to_pages(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(
        fixtures_root=FIXTURES, store=store, row=row, review_accept=True
    )
    pages = {p["page_no"]: p["text"] for p in decision["pages"]}
    for prop in decision["propositions"]:
        for ev in prop["evidence"]:
            assert ev["span_id"]
            assert ev["quote"] in pages[ev["page_no"]]


def test_manifest_ingest_enqueues_jobs(tmp_path: Path):
    results = ingest_manifest(
        fixtures_root=FIXTURES,
        manifest_path=FIXTURES / "manifests/m1.jsonl",
        data_root=tmp_path,
        review_accept=False,
        enqueue_jobs=True,
    )
    assert len(results) >= 2
    q = FileJobQueue(tmp_path / "jobs")
    assert q.list_jobs(status="succeeded")
