"""MVP-RC1 acceptance tests: privacy, provenance, mock quality, release, fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from reglens_worker.determinism import span_stable_id  # noqa: E402
from reglens_worker.hashutil import sha256_file  # noqa: E402
from reglens_worker.ingest import ingest_fixture, ingest_manifest, load_manifest  # noqa: E402
from reglens_worker.llm import MockLLMProvider  # noqa: E402
from reglens_worker.privacy import (  # noqa: E402
    assert_no_obvious_patient_leak,
    redact_derived_text,
)
from reglens_worker.release import (  # noqa: E402
    ReleaseError,
    build_release,
    scan_public_artifact,
)
from reglens_worker.schema_validate import (  # noqa: E402
    assert_valid_extraction_v2,
    domain_validate_extraction,
)
from reglens_worker.segment import PageSpan, segment_document  # noqa: E402
from reglens_worker.store import LocalArtifactStore  # noqa: E402

FIXTURES = ROOT / "fixtures"
ANNOTATIONS = ROOT / "publications" / "demo" / "editorial_annotations.v1.json"
POLICY = ROOT / "publications" / "policies" / "source_publication_policy.v1.json"
TAXONOMY = ROOT / "publications" / "taxonomy" / "taxonomy.v1.json"
MANIFEST = FIXTURES / "manifests" / "m1.jsonl"

RELEASED_AT = "2026-07-11T12:00:00Z"
RELEASE_ID = "mvp-rc1-test"


# ---------------------------------------------------------------------------
# Privacy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,token",
    [
        ("Clinical notes for Patient A were incomplete.", "Patient A"),
        ("Madam xxx attended the clinic.", "Madam xxx"),
        ("Patient Alice reported symptoms.", "Patient Alice"),
        ("Contact: patient@example.com for follow-up.", "patient@example.com"),
        ("Call 9123-4567 during office hours.", "9123-4567"),
        ("Clinic at 12 Nathan Road was inspected.", "12 Nathan Road"),
    ],
)
def test_privacy_redacts_patient_and_contact_tokens(raw: str, token: str):
    redacted = redact_derived_text(raw)
    assert token not in redacted
    assert_no_obvious_patient_leak(redacted)
    assert "[REDACTED_PERSON]" in redacted or "[REDACTED_CONTACT]" in redacted


def test_assert_no_obvious_patient_leak_raises_on_patient_a():
    with pytest.raises(ValueError, match="patient_token"):
        assert_no_obvious_patient_leak("records of Patient A remain")


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def _resolved_mock_extraction(path: Path) -> tuple[dict, list[PageSpan], str]:
    spans = segment_document(path)
    digest = sha256_file(path)
    payload = MockLLMProvider().extract(document_sha256=digest, regulator_code="MCHK", spans=spans)
    for prop in payload["propositions"]:
        for ev in prop["evidence"]:
            ev["span_id"] = span_stable_id(
                digest, next(s for s in spans if s.page_no == ev["page_no"])
            )
    return payload, spans, digest


def test_provenance_wrong_span_id_rejected():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, spans, digest = _resolved_mock_extraction(path)
    payload["propositions"][0]["evidence"][0]["span_id"] = "0" * 64
    with pytest.raises(ValueError, match="span_id|unknown|mismatch"):
        assert_valid_extraction_v2(payload, spans=spans, document_sha256=digest)


def test_provenance_cross_document_span_rejected():
    path_a = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    path_b = FIXTURES / "synthetic/dchk/SYN-DCHK-2023-014.html"
    payload, spans_a, digest_a = _resolved_mock_extraction(path_a)
    spans_b = segment_document(path_b)
    digest_b = sha256_file(path_b)
    foreign_id = span_stable_id(digest_b, spans_b[0])
    payload["propositions"][0]["evidence"][0]["span_id"] = foreign_id
    errors = domain_validate_extraction(
        payload, spans=spans_a, document_sha256=digest_a, require_span_id=True
    )
    assert any("cross-document" in e or "unknown" in e or "mismatch" in e for e in errors)


def test_provenance_wrong_offsets_rejected():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, spans, digest = _resolved_mock_extraction(path)
    ev = payload["propositions"][0]["evidence"][0]
    # Keep quote but shift offsets so sliced text no longer matches
    assert ev.get("char_start") is not None and ev.get("char_end") is not None
    span = next(s for s in spans if s.page_no == ev["page_no"])
    bad_start = min(ev["char_start"] + 3, len(span.text) - 1)
    bad_end = min(ev["char_end"] + 3, len(span.text))
    if bad_start >= bad_end:
        bad_start, bad_end = 0, min(5, len(span.text))
    ev["char_start"] = bad_start
    ev["char_end"] = bad_end
    with pytest.raises(ValueError, match="offset|sliced|quote"):
        assert_valid_extraction_v2(payload, spans=spans, document_sha256=digest)


# ---------------------------------------------------------------------------
# Mock extractor quality
# ---------------------------------------------------------------------------


def test_mock_cap161_full_in_rule_claim():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, _, _ = _resolved_mock_extraction(path)
    rules = [p for p in payload["propositions"] if p["prop_type"] == "rule"]
    assert rules
    claim = rules[0]["claim_text"]
    assert "Cap. 161" in claim
    assert claim.endswith("161") or "Cap. 161" in claim


def test_mock_hearing_date_only_in_inquiry_not_judgment():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, _, _ = _resolved_mock_extraction(path)
    dates = payload["decision_metadata"]["dates"]
    assert dates["inquiry"] == "2024-03-15"
    assert dates["judgment"] is None


def test_mock_sanction_excludes_appeal():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, _, _ = _resolved_mock_extraction(path)
    sanctions = [p for p in payload["propositions"] if p["prop_type"] == "sanction"]
    assert sanctions
    claim = sanctions[0]["claim_text"]
    assert "appeal" not in claim.lower()
    assert "warning letter" in claim.lower()


def test_mock_authority_not_truncated_mid_word():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, _, _ = _resolved_mock_extraction(path)
    authorities = [p for p in payload["propositions"] if p["prop_type"] == "authority"]
    assert authorities
    claim = authorities[0]["claim_text"]
    assert "Hong Kong" in claim
    assert not claim.rstrip(".").endswith(("Hong", "Kon", "Counci", "Medica"))
    assert "endorsement principles" in claim


def test_mock_charge_evidence_not_cut_at_180_when_under_2000():
    path = FIXTURES / "synthetic/mchk/SYN-MCHK-2024-001.html"
    payload, _, _ = _resolved_mock_extraction(path)
    charges = [p for p in payload["propositions"] if p["prop_type"] == "charge"]
    assert charges
    claim = charges[0]["claim_text"]
    quote = charges[0]["evidence"][0]["quote"]
    assert len(claim) < 2000
    assert len(quote) == len(claim) or quote == claim
    assert len(quote) > 180
    assert "misconduct in a professional respect" in quote


# ---------------------------------------------------------------------------
# Exact expected outputs for three synthetic docs
# ---------------------------------------------------------------------------


def test_exact_outputs_three_synthetic_docs(tmp_path: Path):
    store = LocalArtifactStore(tmp_path)
    rows = {r.external_ref: r for r in load_manifest(MANIFEST)}

    mchk = ingest_fixture(
        fixtures_root=FIXTURES,
        store=store,
        row=rows["SYN-MCHK-2024-001"],
        demo_auto_approve_synthetic=True,
    )
    assert mchk["case_ref"] == "SYN-MCHK-2024-001"
    assert mchk["case_refs"] == ["SYN-MCHK-2024-001"]
    assert mchk["dates"]["inquiry"] == "2024-03-15"
    assert mchk["dates"]["judgment"] is None
    rules = [p for p in mchk["propositions"] if p["prop_type"] == "rule"]
    assert any("Cap. 161" in p["claim_text"] for p in rules)
    charge = next(p for p in mchk["propositions"] if p["prop_type"] == "charge")
    assert "Patient A" not in charge["claim_text"]
    assert "[REDACTED_PERSON]" in charge["claim_text"]
    assert_no_obvious_patient_leak(charge["claim_text"])

    dchk = ingest_fixture(
        fixtures_root=FIXTURES,
        store=store,
        row=rows["SYN-DCHK-2023-014"],
        demo_auto_approve_synthetic=True,
    )
    assert dchk["case_ref"] == "SYN-DCHK-2023-014"
    assert dchk["dates"]["inquiry"] == "2023-11-08"
    assert dchk["dates"]["judgment"] is None
    assert dchk["regulator_code"] == "DCHK"

    pdf = ingest_fixture(
        fixtures_root=FIXTURES,
        store=store,
        row=rows["SYN-MCHK-PDF-001"],
        demo_auto_approve_synthetic=True,
    )
    assert pdf["case_ref"] == "SYN-MCHK-PDF-001"
    assert pdf["dates"]["judgment"] is None
    assert any(p["prop_type"] == "charge" for p in pdf["propositions"])


def test_no_fixtures_seed_directory():
    assert not (FIXTURES / "seed").exists()
    assert not (FIXTURES / "raw").exists()


# ---------------------------------------------------------------------------
# Release builder
# ---------------------------------------------------------------------------


def _seed_data_root(tmp_path: Path) -> Path:
    data_root = tmp_path / "data"
    ingest_manifest(
        fixtures_root=FIXTURES,
        manifest_path=MANIFEST,
        data_root=data_root,
        demo_auto_approve_synthetic=True,
        enqueue_jobs=False,
    )
    return data_root


def _build(
    *,
    data_root: Path,
    output_dir: Path,
    release_mode: str = "synthetic_demo",
    release_id: str = RELEASE_ID,
    released_at: str = RELEASED_AT,
    annotations_path: Path = ANNOTATIONS,
    taxonomy_path: Path = TAXONOMY,
) -> dict:
    return build_release(
        data_root=data_root,
        annotations_path=annotations_path,
        policy_path=POLICY,
        taxonomy_path=taxonomy_path,
        release_id=release_id,
        release_mode=release_mode,
        released_at=released_at,
        output_dir=output_dir,
    )


def test_release_synthetic_demo_builds(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    out = tmp_path / "release"
    manifest = _build(data_root=data_root, output_dir=out)
    assert manifest["release_mode"] == "synthetic_demo"
    assert manifest["decision_count"] == 3
    assert (out / "release.json").is_file()
    assert (out / "catalog.json").is_file()
    assert (out / "checksums.sha256").is_file()
    assert (out / "decisions" / "syn-mchk-2024-001.json").is_file()


def test_release_public_mode_rejects_synthetic(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    with pytest.raises(ReleaseError, match="synthetic"):
        _build(
            data_root=data_root,
            output_dir=tmp_path / "bad-public",
            release_mode="public",
        )


def test_release_pending_excluded(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    store = LocalArtifactStore(data_root)
    decision = next(d for d in store.list_decisions() if d["case_ref"] == "SYN-MCHK-2024-001")
    before = sum(1 for p in decision["propositions"] if p.get("published"))
    # Park a non-annotation-required proposition as pending
    parked = None
    for prop in decision["propositions"]:
        if prop["client_ref"] not in {"charge-1", "finding-1", "sanction-1"}:
            prop["review_status"] = "pending"
            prop["published"] = False
            parked = prop["client_ref"]
            break
    assert parked is not None
    store.save_decision(decision)

    out = tmp_path / "release"
    _build(data_root=data_root, output_dir=out)
    public = json.loads((out / "decisions" / "syn-mchk-2024-001.json").read_text(encoding="utf-8"))
    refs = {p["client_ref"] for p in public["propositions"]}
    assert parked not in refs
    assert len(public["propositions"]) == before - 1


def test_release_no_confidence_no_pages_in_public_json(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    out = tmp_path / "release"
    _build(data_root=data_root, output_dir=out)
    for path in (out / "decisions").glob("*.json"):
        blob = path.read_text(encoding="utf-8")
        data = json.loads(blob)
        assert "confidence" not in blob
        assert "pages" not in data
        assert "extractor" not in data
        for prop in data["propositions"]:
            assert "confidence" not in prop


def _verify_checksums(release_dir: Path) -> None:
    checksums = release_dir / "checksums.sha256"
    assert checksums.is_file()
    for line in checksums.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        expected, rel = line.split(None, 1)
        actual = sha256_file(release_dir / rel)
        assert actual == expected, f"checksum mismatch for {rel}"


def test_release_checksums_validate(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    out = tmp_path / "release"
    _build(data_root=data_root, output_dir=out)
    _verify_checksums(out)


def test_release_reproducible_with_same_released_at(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    out1 = tmp_path / "r1"
    out2 = tmp_path / "r2"
    _build(data_root=data_root, output_dir=out1)
    _build(data_root=data_root, output_dir=out2)
    assert (out1 / "checksums.sha256").read_text() == (out2 / "checksums.sha256").read_text()
    assert (out1 / "release.json").read_bytes() == (out2 / "release.json").read_bytes()


def test_release_annotation_required(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    # Keep schema-valid annotations but omit one case so resolution fails
    partial = tmp_path / "partial_annotations.json"
    data = copy.deepcopy(json.loads(ANNOTATIONS.read_text(encoding="utf-8")))
    data["annotations"] = [
        a for a in data["annotations"] if a["external_ref"] != "SYN-MCHK-2024-001"
    ]
    assert data["annotations"], "fixture must retain at least one annotation"
    partial.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ReleaseError, match="Missing editorial annotation"):
        _build(
            data_root=data_root,
            output_dir=tmp_path / "no-ann",
            annotations_path=partial,
        )


def test_release_taxonomy_validation(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    bad_ann = tmp_path / "bad_annotations.json"
    data = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
    data = copy.deepcopy(data)
    data["annotations"][0]["issue_categories"] = ["not_a_real_taxonomy_code"]
    bad_ann.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ReleaseError, match="Unknown issue_categories|taxonomy|code"):
        _build(
            data_root=data_root,
            output_dir=tmp_path / "bad-tax",
            annotations_path=bad_ann,
        )


def test_scan_public_artifact_finds_planted_patient_a(tmp_path: Path):
    data_root = _seed_data_root(tmp_path)
    out = tmp_path / "release"
    _build(data_root=data_root, output_dir=out)
    assert scan_public_artifact(out) == []

    target = out / "decisions" / "syn-mchk-2024-001.json"
    planted = json.loads(target.read_text(encoding="utf-8"))
    planted["propositions"][0]["claim_text"] = (
        planted["propositions"][0]["claim_text"] + " Patient A"
    )
    target.write_text(json.dumps(planted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    hits = scan_public_artifact(out)
    assert hits
    assert any("patient_token" in h for h in hits)
