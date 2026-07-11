from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import PIPELINE_VERSION
from .determinism import (
    SCHEMA_VERSION,
    decision_id_for_run,
    document_id_for_sha256,
    extraction_run_key,
    proposition_id_for,
    span_stable_id,
)
from .hashutil import sha256_file
from .llm import MockLLMProvider
from .schema_validate import assert_valid_extraction_v2
from .segment import segment_document_report
from .store import LocalArtifactStore, mime_for, utc_now_iso


@dataclass(frozen=True)
class ManifestRow:
    regulator_code: str
    source_id: str
    relative_path: str
    fixture_kind: str
    external_ref: str | None = None
    title: str | None = None
    source_url: str | None = None
    downloaded_at: str | None = None
    notes: str | None = None


class ManifestSafetyError(ValueError):
    pass


def load_manifest(path: Path) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        data = json.loads(line)
        kind = data.get("fixture_kind")
        if kind not in {"synthetic", "real"}:
            raise ManifestSafetyError(
                f"manifest row missing fixture_kind=synthetic|real: {data.get('relative_path')}"
            )
        rows.append(
            ManifestRow(
                regulator_code=data["regulator_code"],
                source_id=data["source_id"],
                relative_path=data["relative_path"],
                fixture_kind=kind,
                external_ref=data.get("external_ref"),
                title=data.get("title"),
                source_url=data.get("source_url"),
                downloaded_at=data.get("downloaded_at"),
                notes=data.get("notes"),
            )
        )
    return rows


def ingest_fixture(
    *,
    fixtures_root: Path,
    store: LocalArtifactStore,
    row: ManifestRow,
    provider: MockLLMProvider | None = None,
    demo_auto_approve_synthetic: bool = False,
) -> dict[str, Any]:
    """
    Idempotent fixture ingest with immutable run artifacts.
    Default: propositions pending and unpublished.
    """
    if demo_auto_approve_synthetic and row.fixture_kind != "synthetic":
        raise ManifestSafetyError(
            "--demo-auto-approve-synthetic rejected non-synthetic row: "
            f"{row.relative_path} ({row.fixture_kind})"
        )

    provider = provider or MockLLMProvider()
    src = fixtures_root / row.relative_path
    if not src.is_file():
        raise FileNotFoundError(src)

    digest = sha256_file(src)
    storage_key = store.store_blob(src, digest)
    report = segment_document_report(src)
    spans = report.spans

    doc_record = {
        "document_id": document_id_for_sha256(digest),
        "sha256": digest,
        "storage_key": storage_key,
        "mime_type": mime_for(src),
        "byte_size": src.stat().st_size,
        "regulator_code": row.regulator_code,
        "source_id": row.source_id,
        "fixture_kind": row.fixture_kind,
        "external_ref": row.external_ref,
        "title": row.title or src.name,
        "relative_path": row.relative_path,
        "source_url": row.source_url,
        "downloaded_at": row.downloaded_at,
        "notes": row.notes,
        "ingest_status": "segmented",
        "text_quality": report.overall_quality,
        "empty_page_ratio": report.empty_page_ratio,
        "segmentation_warnings": report.warnings,
        "page_qualities": [{"page_no": s.page_no, "quality": s.quality} for s in spans],
        "ocr_used": False,
        "immutable": True,
        "ingested_at": utc_now_iso(),
        "spans": [
            {
                **span.__dict__,
                "span_id": span_stable_id(digest, span),
            }
            for span in spans
        ],
    }
    store.write_document_record(doc_record)
    store.write_spans(digest, spans)

    extraction = provider.extract(
        document_sha256=digest,
        regulator_code=row.regulator_code,
        spans=spans,
        metadata={
            "case_ref": row.external_ref,
            "defendant_name_as_published": None,
            "decision_date": None,
        },
    )

    page_to_span_id = {s.page_no: span_stable_id(digest, s) for s in spans}
    for prop in extraction["propositions"]:
        for ev in prop["evidence"]:
            sid = page_to_span_id.get(ev["page_no"])
            if not sid:
                raise ValueError(f"no span for page {ev['page_no']}")
            ev["span_id"] = sid

    assert_valid_extraction_v2(
        extraction,
        spans=spans,
        document_sha256=digest,
        require_span_id=True,
    )

    run_key = extraction_run_key(
        document_sha256=digest,
        schema_version=SCHEMA_VERSION,
        pipeline_version=extraction["extractor"]["pipeline_version"],
        model_provider=extraction["extractor"]["model_provider"],
        model_version=extraction["extractor"]["model_version"],
        prompt_version=extraction["extractor"]["prompt_version"],
        deterministic_settings={"fixture_kind": row.fixture_kind},
    )
    _, output_sha = store.write_run_extraction(run_key, extraction)

    auto = bool(demo_auto_approve_synthetic and row.fixture_kind == "synthetic")
    decision_id = decision_id_for_run(run_key)
    propositions_out = []
    for prop in extraction["propositions"]:
        prop_id = proposition_id_for(run_key, prop["client_ref"])
        propositions_out.append(
            {
                "id": prop_id,
                "client_ref": prop["client_ref"],
                "prop_type": prop["prop_type"],
                "epistemic_class": prop["epistemic_class"],
                "derivation": prop["derivation"],
                "claim_text": prop["claim_text"],
                "structured": prop.get("structured"),
                "confidence": prop["confidence"],
                "review_status": "accepted" if auto else "pending",
                "published": bool(auto),
                "evidence": prop["evidence"],
            }
        )

    meta = extraction["decision_metadata"]
    decision = {
        "id": decision_id,
        "run_key": run_key,
        "extraction_sha256": output_sha,
        "document_id": doc_record["document_id"],
        "document_sha256": digest,
        "regulator_code": row.regulator_code,
        "source_id": row.source_id,
        "fixture_kind": row.fixture_kind,
        "title": doc_record["title"],
        "case_refs": meta.get("case_refs") or [],
        "case_ref": (meta.get("case_refs") or [row.external_ref])[0]
        if (meta.get("case_refs") or row.external_ref)
        else None,
        "dates": meta.get("dates"),
        "decision_date": (meta.get("dates") or {}).get("judgment"),
        "profession": meta.get("profession"),
        "defendant_name_as_published": meta.get("defendant_name_as_published"),
        "defendant_registration_no": meta.get("defendant_registration_no"),
        "source_url": row.source_url,
        "coverage": extraction.get("coverage", {}),
        "text_quality": report.overall_quality,
        "segmentation_warnings": report.warnings,
        "extractor": extraction["extractor"],
        "relations": extraction.get("relations") or [],
        "pages": [
            {
                "span_id": span_stable_id(digest, s),
                "page_no": s.page_no,
                "source_page_no": s.source_page_no,
                "printed_page_label": s.printed_page_label,
                "quality": s.quality,
                "text": s.text,
            }
            for s in spans
        ],
        "propositions": propositions_out,
        "licence_notice": (
            "Internal research use of fixture materials only. "
            "Not legal advice. Synthetic demo pointer is not the audit record."
        ),
        "generated_at": utc_now_iso(),
        "pipeline_version": PIPELINE_VERSION,
    }
    store.write_run_decision(run_key, decision)
    # Demo pointer always updated for local UX; audit path is meta/runs/{run_key}/
    store.write_demo_pointer(decision, run_key=run_key)
    return decision


def ingest_manifest(
    *,
    fixtures_root: Path,
    manifest_path: Path,
    data_root: Path,
    demo_auto_approve_synthetic: bool = False,
) -> list[dict[str, Any]]:
    store = LocalArtifactStore(data_root)
    rows = load_manifest(manifest_path)
    if demo_auto_approve_synthetic:
        for row in rows:
            if row.fixture_kind != "synthetic":
                raise ManifestSafetyError(
                    "demo auto-approve refused: manifest contains non-synthetic row "
                    f"{row.relative_path}"
                )
    results = [
        ingest_fixture(
            fixtures_root=fixtures_root,
            store=store,
            row=row,
            demo_auto_approve_synthetic=demo_auto_approve_synthetic,
        )
        for row in rows
    ]
    preferred = next(
        (
            d
            for d in results
            if d.get("regulator_code") == "MCHK" and "PDF" not in (d.get("title") or "")
        ),
        results[0] if results else None,
    )
    if preferred:
        store.write_demo_pointer(preferred, run_key=preferred["run_key"])
    return results
