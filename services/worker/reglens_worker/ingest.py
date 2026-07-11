from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .hashutil import sha256_file
from .llm import MockLLMProvider
from .schema_validate import assert_valid_extraction, evidence_quotes_supported
from .segment import segment_document, text_quality
from .store import LocalArtifactStore, mime_for, span_stable_id, utc_now_iso


@dataclass(frozen=True)
class ManifestRow:
    regulator_code: str
    source_id: str
    relative_path: str
    external_ref: str | None = None
    title: str | None = None
    source_url: str | None = None
    downloaded_at: str | None = None
    notes: str | None = None


def load_manifest(path: Path) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        data = json.loads(line)
        rows.append(
            ManifestRow(
                regulator_code=data["regulator_code"],
                source_id=data["source_id"],
                relative_path=data["relative_path"],
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
    review_accept: bool = True,
) -> dict[str, Any]:
    """
    Idempotent fixture ingest:
    hash → immutable blob → page spans → mock extract → schema/quote checks → seed decision.
    """
    provider = provider or MockLLMProvider()
    src = fixtures_root / row.relative_path
    if not src.is_file():
        raise FileNotFoundError(src)

    digest = sha256_file(src)
    storage_key = store.store_blob(src, digest)
    spans = segment_document(src)
    quality = text_quality(spans)

    doc_record = {
        "document_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"reglens:doc:{digest}")),
        "sha256": digest,
        "storage_key": storage_key,
        "mime_type": mime_for(src),
        "byte_size": src.stat().st_size,
        "regulator_code": row.regulator_code,
        "source_id": row.source_id,
        "external_ref": row.external_ref,
        "title": row.title or src.name,
        "relative_path": row.relative_path,
        "source_url": row.source_url,
        "downloaded_at": row.downloaded_at,
        "notes": row.notes,
        "ingest_status": "segmented",
        "text_quality": quality,
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

    # Attach stable span_ids to evidence where page matches.
    page_to_span = {s.page_no: span_stable_id(digest, s) for s in spans}
    for prop in extraction["propositions"]:
        for ev in prop["evidence"]:
            ev["span_id"] = page_to_span.get(ev["page_no"])

    assert_valid_extraction(extraction)
    page_texts = {s.page_no: s.text for s in spans}
    unsupported = evidence_quotes_supported(extraction, page_texts)
    if unsupported:
        raise ValueError("Evidence quote alignment failed:\n- " + "\n- ".join(unsupported))

    store.write_extraction(digest, extraction)

    decision_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"reglens:decision:{digest}"))
    propositions_out = []
    for prop in extraction["propositions"]:
        review_status = "accepted" if review_accept else "pending"
        published = bool(review_accept)
        evidence = []
        for ev in prop["evidence"]:
            evidence.append(
                {
                    "span_id": ev["span_id"],
                    "page_no": ev["page_no"],
                    "quote": ev["quote"],
                    "char_start": ev.get("char_start"),
                    "char_end": ev.get("char_end"),
                }
            )
        propositions_out.append(
            {
                "id": prop["id"],
                "prop_type": prop["prop_type"],
                "epistemic_class": prop["epistemic_class"],
                "claim_text": prop["claim_text"],
                "confidence": prop["confidence"],
                "review_status": review_status,
                "published": published,
                "evidence": evidence,
            }
        )

    decision = {
        "id": decision_id,
        "document_id": doc_record["document_id"],
        "document_sha256": digest,
        "regulator_code": row.regulator_code,
        "source_id": row.source_id,
        "title": doc_record["title"],
        "case_ref": extraction.get("decision_metadata", {}).get("case_ref") or row.external_ref,
        "decision_date": extraction.get("decision_metadata", {}).get("decision_date"),
        "profession": extraction.get("decision_metadata", {}).get("profession"),
        "defendant_name_as_published": extraction.get("decision_metadata", {}).get(
            "defendant_name_as_published"
        ),
        "defendant_registration_no": extraction.get("decision_metadata", {}).get(
            "defendant_registration_no"
        ),
        "source_url": row.source_url,
        "coverage": extraction.get("coverage", {}),
        "text_quality": quality,
        "extractor": extraction["extractor"],
        "pages": [
            {
                "span_id": span_stable_id(digest, s),
                "page_no": s.page_no,
                "text": s.text,
            }
            for s in spans
        ],
        "propositions": propositions_out,
        "licence_notice": (
            "Internal research use of fixture materials only. "
            "Not legal advice. Link to official source where available."
        ),
        "generated_at": utc_now_iso(),
    }
    store.write_decision_seed(decision)
    return decision


def ingest_manifest(
    *,
    fixtures_root: Path,
    manifest_path: Path,
    data_root: Path,
) -> list[dict[str, Any]]:
    store = LocalArtifactStore(data_root)
    rows = load_manifest(manifest_path)
    results = []
    for row in rows:
        results.append(
            ingest_fixture(fixtures_root=fixtures_root, store=store, row=row)
        )
    # Prefer MCHK synthetic as default demo seed if present
    preferred = next(
        (d for d in results if d.get("regulator_code") == "MCHK"),
        results[0] if results else None,
    )
    if preferred:
        store.write_decision_seed(preferred)
    return results
