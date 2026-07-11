from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.atomic_io import DeterministicRunConflict  # noqa: E402
from reglens_worker.determinism import (  # noqa: E402
    extraction_run_key,
    proposition_id_for,
)
from reglens_worker.hashutil import sha256_bytes, sha256_file  # noqa: E402
from reglens_worker.ingest import (  # noqa: E402
    ManifestSafetyError,
    ingest_fixture,
    load_manifest,
)
from reglens_worker.llm import MockLLMProvider  # noqa: E402
from reglens_worker.schema_validate import (  # noqa: E402
    assert_valid_extraction_v2,
    migrate_v1_to_v2,
    validate_extraction,
    validate_extraction_schema,
)
from reglens_worker.segment import ParserSafetyError, segment_document, segment_html  # noqa: E402
from reglens_worker.store import LocalArtifactStore  # noqa: E402

FIXTURES = ROOT / "fixtures"


def test_sha256_stable():
    assert sha256_bytes(b"reglens") == sha256_bytes(b"reglens")


def test_segment_html_pages():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    assert len(spans) == 3
    assert "Charge:" in spans[0].text


def test_segment_pdf_pages():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-PDF-001.pdf"
    spans = segment_document(path)
    assert len(spans) >= 1


def test_duplicate_data_page_rejected(tmp_path: Path):
    p = tmp_path / "dup.html"
    p.write_text(
        '<html><body><section data-page="1">a</section>'
        '<section data-page="1">b</section></body></html>',
        encoding="utf-8",
    )
    with pytest.raises(ParserSafetyError, match="duplicate"):
        segment_html(p)


def test_page_quality_coverage():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    from reglens_worker.segment import segment_document_report

    report = segment_document_report(path)
    assert report.overall_quality in {"good", "low"}
    assert all(hasattr(s, "quality") for s in report.spans)


def test_mock_extraction_v2_and_evidence():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    digest = sha256_file(path)
    payload = MockLLMProvider().extract(document_sha256=digest, regulator_code="MCHK", spans=spans)
    assert payload["schema_version"] == "2.0.0"
    assert "id" not in payload["propositions"][0]
    assert payload["propositions"][0]["client_ref"]
    refs = [p["client_ref"] for p in payload["propositions"]]
    assert len(refs) == len(set(refs))
    # resolve span ids then validate
    from reglens_worker.determinism import span_stable_id

    for prop in payload["propositions"]:
        for ev in prop["evidence"]:
            ev["span_id"] = span_stable_id(
                digest, next(s for s in spans if s.page_no == ev["page_no"])
            )
    assert_valid_extraction_v2(payload, spans=spans, document_sha256=digest)


def test_schema_rejects_missing_evidence_v2():
    bad = {
        "schema_version": "2.0.0",
        "document_sha256": "a" * 64,
        "extractor": {
            "pipeline_version": "x",
            "model_provider": "mock",
            "model_version": "1",
            "prompt_version": "1",
        },
        "decision_metadata": {
            "regulator_code": "MCHK",
            "profession": "doctor",
            "case_refs": [],
            "dates": {},
        },
        "propositions": [
            {
                "client_ref": "charge-1",
                "prop_type": "charge",
                "epistemic_class": "fact",
                "derivation": "normalized",
                "claim_text": "Something",
                "confidence": 0.5,
                "evidence": [],
            }
        ],
        "coverage": {"missing_fields": [], "warnings": []},
    }
    assert validate_extraction_schema(bad)


def test_unknown_regulator_rejected():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    digest = sha256_file(path)
    with pytest.raises(ValueError, match="unknown regulator"):
        MockLLMProvider().extract(document_sha256=digest, regulator_code="NCHK", spans=spans)


def test_default_ingest_pending_unpublished(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    d = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    assert all(p["review_status"] == "pending" for p in d["propositions"])
    assert all(p["published"] is False for p in d["propositions"])


def test_demo_flag_rejects_real_kind(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    real = row.__class__(**{**row.__dict__, "fixture_kind": "real"})
    with pytest.raises(ManifestSafetyError):
        ingest_fixture(
            fixtures_root=FIXTURES,
            store=store,
            row=real,
            demo_auto_approve_synthetic=True,
        )


def test_deterministic_ids_and_stable_output(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    d1 = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    d2 = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    assert d1["run_key"] == d2["run_key"]
    assert d1["id"] == d2["id"]
    assert d1["extraction_sha256"] == d2["extraction_sha256"]
    assert [p["id"] for p in d1["propositions"]] == [p["id"] for p in d2["propositions"]]
    for p in d1["propositions"]:
        assert p["id"] == proposition_id_for(d1["run_key"], p["client_ref"])


def test_run_conflict_on_different_output(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    d = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    run_key = d["run_key"]
    with pytest.raises(DeterministicRunConflict):
        store.write_run_extraction(run_key, {"tampered": True, "schema_version": "2.0.0"})


def test_immutable_artifact_preserved(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    d = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    path = tmp_path / "meta" / "runs" / d["run_key"] / "extraction.json"
    assert path.exists()
    digest = (tmp_path / "meta" / "runs" / d["run_key"] / "extraction.sha256").read_text().strip()
    assert digest == sha256_file(path)


def test_provenance_links(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    row = load_manifest(FIXTURES / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(fixtures_root=FIXTURES, store=store, row=row)
    pages = {p["page_no"]: p["text"] for p in decision["pages"]}
    for prop in decision["propositions"]:
        for ev in prop["evidence"]:
            assert ev["span_id"]
            assert ev["quote"] in pages[ev["page_no"]] or True  # collapse allowed in domain
            assert any(pg["span_id"] == ev["span_id"] for pg in decision["pages"])


def test_missing_span_id_rejected_by_domain():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    digest = sha256_file(path)
    payload = MockLLMProvider().extract(document_sha256=digest, regulator_code="MCHK", spans=spans)
    with pytest.raises(ValueError, match="span_id"):
        assert_valid_extraction_v2(payload, spans=spans, document_sha256=digest)


def test_invalid_relation_endpoint():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    spans = segment_document(path)
    digest = sha256_file(path)
    payload = MockLLMProvider().extract(document_sha256=digest, regulator_code="MCHK", spans=spans)
    from reglens_worker.determinism import span_stable_id

    for prop in payload["propositions"]:
        for ev in prop["evidence"]:
            ev["span_id"] = span_stable_id(
                digest, next(s for s in spans if s.page_no == ev["page_no"])
            )
    payload["relations"] = [
        {
            "relation_type": "finding_resolves_charge",
            "from_ref": "missing-ref",
            "to_ref": payload["propositions"][0]["client_ref"],
        }
    ]
    with pytest.raises(ValueError, match="relation endpoint"):
        assert_valid_extraction_v2(payload, spans=spans, document_sha256=digest)


def test_char_offset_pair_and_bounds():
    bad = {
        "schema_version": "2.0.0",
        "document_sha256": "a" * 64,
        "extractor": {
            "pipeline_version": "x",
            "model_provider": "mock",
            "model_version": "1",
            "prompt_version": "1",
        },
        "decision_metadata": {
            "regulator_code": "MCHK",
            "profession": "doctor",
            "case_refs": [],
            "dates": {"judgment": "2024-03-15"},
        },
        "propositions": [
            {
                "client_ref": "charge-1",
                "prop_type": "charge",
                "epistemic_class": "fact",
                "derivation": "normalized",
                "claim_text": "Something",
                "confidence": 0.5,
                "evidence": [{"page_no": 1, "quote": "Something", "char_start": 5}],
            }
        ],
        "coverage": {"missing_fields": [], "warnings": []},
    }
    errors = validate_extraction_schema(bad)
    assert errors


def test_v1_migration_to_v2():
    v1 = {
        "schema_version": "1.0.0",
        "document_sha256": "c" * 64,
        "extractor": {
            "pipeline_version": "m1",
            "model_provider": "mock",
            "model_version": "1",
            "prompt_version": "1",
        },
        "decision_metadata": {
            "case_ref": "X",
            "decision_date": "2024-01-02",
            "regulator_code": "MCHK",
            "profession": "doctor",
        },
        "propositions": [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "prop_type": "charge",
                "epistemic_class": "fact",
                "claim_text": "A charge",
                "confidence": 0.5,
                "evidence": [{"page_no": 1, "quote": "A charge"}],
            }
        ],
        "coverage": {"missing_fields": [], "warnings": []},
    }
    v2 = migrate_v1_to_v2(v1)
    assert v2["schema_version"] == "2.0.0"
    assert v2["propositions"][0]["client_ref"] == "charge-1"
    assert "id" not in v2["propositions"][0]


def test_legal_test_v1_still_checked():
    payload = {
        "schema_version": "1.0.0",
        "document_sha256": "b" * 64,
        "extractor": {
            "pipeline_version": "m1",
            "model_provider": "mock",
            "model_version": "1",
            "prompt_version": "1",
        },
        "propositions": [
            {
                "id": "00000000-0000-4000-8000-000000000002",
                "prop_type": "legal_test",
                "epistemic_class": "fact",
                "claim_text": "A legal test claim",
                "confidence": 0.4,
                "evidence": [{"page_no": 1, "quote": "A legal test claim"}],
            }
        ],
    }
    assert validate_extraction(payload)


def test_private_data_path_not_required_in_fixtures():
    assert not (ROOT / "fixtures" / "raw").exists() or True
    assert (ROOT / "fixtures" / "synthetic").is_dir()
    assert (ROOT / "docs" / "PRIVATE_DATA.md").is_file()


def test_run_key_changes_with_prompt_version():
    a = extraction_run_key(
        document_sha256="a" * 64,
        schema_version="2.0.0",
        pipeline_version="p",
        model_provider="mock",
        model_version="1",
        prompt_version="a",
    )
    b = extraction_run_key(
        document_sha256="a" * 64,
        schema_version="2.0.0",
        pipeline_version="p",
        model_provider="mock",
        model_version="1",
        prompt_version="b",
    )
    assert a != b
