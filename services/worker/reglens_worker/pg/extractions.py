"""Extraction runs, spans, propositions, evidence, relations, and revision 1."""

from __future__ import annotations

import json
import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class ExtractionError(ValueError):
    """Invalid extraction persistence input."""


def upsert_document_span(
    conn: psycopg.Connection,
    *,
    document_version_id: uuid.UUID | str,
    page_no: int,
    text: str,
    text_hash: str,
    stable_span_id: str,
    span_type: str = "page",
    char_start: int | None = None,
    char_end: int | None = None,
    bbox_json: dict[str, Any] | list[Any] | None = None,
    span_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO document_spans (
                id, document_version_id, page_no, span_type, char_start, char_end,
                text, text_hash, bbox_json, stable_span_id
            ) VALUES (
                COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (document_version_id, page_no, span_type, text_hash) DO NOTHING
            RETURNING *
            """,
            (
                span_id,
                document_version_id,
                page_no,
                span_type,
                char_start,
                char_end,
                text,
                text_hash.strip().lower(),
                Jsonb(bbox_json) if bbox_json is not None else None,
                stable_span_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                SELECT * FROM document_spans
                WHERE document_version_id = %s
                  AND page_no = %s
                  AND span_type = %s
                  AND text_hash = %s
                """,
                (document_version_id, page_no, span_type, text_hash.strip().lower()),
            )
            row = cur.fetchone()
        if row is None:
            raise ExtractionError("document_span upsert returned no row")
        return dict(row)


def insert_extraction_run(
    conn: psycopg.Connection,
    *,
    run_key: str,
    document_version_id: uuid.UUID | str,
    pipeline_version: str,
    model_provider: str,
    model_version: str,
    prompt_version: str,
    input_hash: str,
    decision_id: uuid.UUID | str | None = None,
    schema_version: str = "2.0.0",
    output_sha256: str | None = None,
    status: str = "succeeded",
    coverage_json: dict[str, Any] | None = None,
    extraction_run_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        finished = status in {"succeeded", "failed", "quarantined"}
        cur.execute(
            """
            INSERT INTO extraction_runs (
                id, run_key, document_version_id, decision_id, pipeline_version,
                model_provider, model_version, prompt_version, schema_version,
                input_hash, output_sha256, status, coverage_json, finished_at
            ) VALUES (
                COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                CASE WHEN %s THEN now() ELSE NULL END
            )
            ON CONFLICT (run_key) DO NOTHING
            RETURNING *
            """,
            (
                extraction_run_id,
                run_key,
                document_version_id,
                decision_id,
                pipeline_version,
                model_provider,
                model_version,
                prompt_version,
                schema_version,
                input_hash.strip().lower(),
                output_sha256.strip().lower() if output_sha256 else None,
                status,
                Jsonb(coverage_json or {"missing_fields": [], "warnings": []}),
                finished,
            ),
        )
        row = cur.fetchone()
        if row is None:
            # Immutable: same run_key must not overwrite earlier extraction output.
            cur.execute(
                "SELECT * FROM extraction_runs WHERE run_key = %s",
                (run_key,),
            )
            row = cur.fetchone()
        if row is None:
            raise ExtractionError("extraction_run insert returned no row")
        return dict(row)


def _structured_payload(structured: Any) -> Any:
    if structured is None:
        return None
    if isinstance(structured, (dict, list)):
        return Jsonb(structured)
    return Jsonb(json.loads(json.dumps(structured)))


def insert_extracted_proposition(
    conn: psycopg.Connection,
    *,
    extraction_run_id: uuid.UUID | str,
    decision_id: uuid.UUID | str,
    client_ref: str,
    prop_type: str,
    epistemic_class: str,
    derivation: str,
    claim_text: str,
    confidence: float,
    structured: dict[str, Any] | None = None,
    proposition_id: uuid.UUID | None = None,
    create_initial_revision: bool = True,
    create_pending_review: bool = True,
    reviewer_user_id: uuid.UUID | str | None = None,
) -> dict[str, Any]:
    """
    Insert an immutable extracted proposition plus revision 1 (origin=extracted).

    Optionally creates an initial pending review row (default ingest state).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO extracted_propositions (
                id, extraction_run_id, decision_id, client_ref, prop_type,
                epistemic_class, derivation, claim_text, structured_json, confidence
            ) VALUES (
                COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (extraction_run_id, client_ref) DO NOTHING
            RETURNING *
            """,
            (
                proposition_id,
                extraction_run_id,
                decision_id,
                client_ref,
                prop_type,
                epistemic_class,
                derivation,
                claim_text,
                _structured_payload(structured),
                confidence,
            ),
        )
        prop = cur.fetchone()
        if prop is None:
            cur.execute(
                """
                SELECT * FROM extracted_propositions
                WHERE extraction_run_id = %s AND client_ref = %s
                """,
                (extraction_run_id, client_ref),
            )
            prop = cur.fetchone()
        if prop is None:
            raise ExtractionError("extracted_proposition insert returned no row")

        revision: dict[str, Any] | None = None
        if create_initial_revision:
            cur.execute(
                """
                INSERT INTO proposition_revisions (
                    extracted_proposition_id, decision_id, revision_number,
                    supersedes_revision_id, origin, prop_type, epistemic_class,
                    derivation, claim_text, structured_json
                ) VALUES (
                    %s, %s, 1, NULL, 'extracted', %s, %s, %s, %s, %s
                )
                ON CONFLICT (extracted_proposition_id, revision_number) DO NOTHING
                RETURNING *
                """,
                (
                    prop["id"],
                    decision_id,
                    prop_type,
                    epistemic_class,
                    derivation,
                    claim_text,
                    _structured_payload(structured),
                ),
            )
            revision = cur.fetchone()
            if revision is None:
                cur.execute(
                    """
                    SELECT * FROM proposition_revisions
                    WHERE extracted_proposition_id = %s AND revision_number = 1
                    """,
                    (prop["id"],),
                )
                revision = cur.fetchone()

            if create_pending_review and revision is not None:
                cur.execute(
                    """
                    SELECT 1 FROM reviews
                    WHERE proposition_revision_id = %s AND review_status = 'pending'
                    LIMIT 1
                    """,
                    (revision["id"],),
                )
                if cur.fetchone() is None:
                    # Pending queue rows have no human reviewer yet (reviewer_user_id NULL).
                    # Terminal statuses require a real reviewer (see migration 0002).
                    cur.execute(
                        """
                        INSERT INTO reviews (
                            decision_id, proposition_revision_id, extracted_proposition_id,
                            reviewer_user_id, review_status
                        ) VALUES (%s, %s, %s, %s, 'pending')
                        """,
                        (
                            decision_id,
                            revision["id"],
                            prop["id"],
                            reviewer_user_id,  # normally None at ingest
                        ),
                    )

        out = dict(prop)
        if revision is not None:
            out["revision"] = dict(revision)
        return out


def insert_proposition_evidence(
    conn: psycopg.Connection,
    *,
    extracted_proposition_id: uuid.UUID | str,
    document_span_id: uuid.UUID | str,
    page_no: int,
    quote_text: str,
    char_start: int | None = None,
    char_end: int | None = None,
    relevance: str | None = None,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO proposition_evidence (
                extracted_proposition_id, document_span_id, page_no, quote_text,
                char_start, char_end, relevance
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (extracted_proposition_id, document_span_id, quote_text) DO NOTHING
            RETURNING *
            """,
            (
                extracted_proposition_id,
                document_span_id,
                page_no,
                quote_text,
                char_start,
                char_end,
                relevance,
            ),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                SELECT * FROM proposition_evidence
                WHERE extracted_proposition_id = %s
                  AND document_span_id = %s
                  AND quote_text = %s
                """,
                (extracted_proposition_id, document_span_id, quote_text),
            )
            row = cur.fetchone()
        if row is None:
            raise ExtractionError("proposition_evidence insert returned no row")
        return dict(row)


def insert_proposition_relation(
    conn: psycopg.Connection,
    *,
    extraction_run_id: uuid.UUID | str,
    from_proposition_id: uuid.UUID | str,
    to_proposition_id: uuid.UUID | str,
    relation_type: str,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO proposition_relations (
                extraction_run_id, from_proposition_id, to_proposition_id, relation_type
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (extraction_run_id, from_proposition_id, to_proposition_id, relation_type)
            DO NOTHING
            RETURNING *
            """,
            (extraction_run_id, from_proposition_id, to_proposition_id, relation_type),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                SELECT * FROM proposition_relations
                WHERE extraction_run_id = %s
                  AND from_proposition_id = %s
                  AND to_proposition_id = %s
                  AND relation_type = %s
                """,
                (extraction_run_id, from_proposition_id, to_proposition_id, relation_type),
            )
            row = cur.fetchone()
        if row is None:
            raise ExtractionError("proposition_relation insert returned no row")
        return dict(row)


def persist_extraction_bundle(
    conn: psycopg.Connection,
    *,
    run_key: str,
    document_version_id: uuid.UUID | str,
    decision_id: uuid.UUID | str,
    pipeline_version: str,
    model_provider: str,
    model_version: str,
    prompt_version: str,
    input_hash: str,
    propositions: list[dict[str, Any]],
    relations: list[dict[str, Any]] | None = None,
    spans: list[dict[str, Any]] | None = None,
    output_sha256: str | None = None,
    coverage_json: dict[str, Any] | None = None,
    schema_version: str = "2.0.0",
    reviewer_user_id: uuid.UUID | str | None = None,
) -> dict[str, Any]:
    """
    Persist spans (optional), extraction run, propositions, evidence, relations,
    and initial proposition_revisions (revision 1).
    """
    span_rows: list[dict[str, Any]] = []
    if spans:
        for span in spans:
            span_rows.append(
                upsert_document_span(
                    conn,
                    document_version_id=document_version_id,
                    page_no=int(span["page_no"]),
                    text=span["text"],
                    text_hash=span["text_hash"],
                    stable_span_id=span["stable_span_id"],
                    span_type=span.get("span_type", "page"),
                    char_start=span.get("char_start"),
                    char_end=span.get("char_end"),
                    bbox_json=span.get("bbox_json"),
                    span_id=span.get("id"),
                )
            )

    # Map page_no / stable_span_id → span uuid for evidence linking
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, page_no, stable_span_id
            FROM document_spans
            WHERE document_version_id = %s
            """,
            (document_version_id,),
        )
        all_spans = list(cur.fetchall())
    by_stable = {s["stable_span_id"]: s["id"] for s in all_spans}
    by_page = {s["page_no"]: s["id"] for s in all_spans}

    run = insert_extraction_run(
        conn,
        run_key=run_key,
        document_version_id=document_version_id,
        decision_id=decision_id,
        pipeline_version=pipeline_version,
        model_provider=model_provider,
        model_version=model_version,
        prompt_version=prompt_version,
        input_hash=input_hash,
        output_sha256=output_sha256,
        coverage_json=coverage_json,
        schema_version=schema_version,
        status="succeeded",
    )

    prop_by_ref: dict[str, uuid.UUID] = {}
    prop_rows: list[dict[str, Any]] = []
    for prop in propositions:
        row = insert_extracted_proposition(
            conn,
            extraction_run_id=run["id"],
            decision_id=decision_id,
            client_ref=prop["client_ref"],
            prop_type=prop["prop_type"],
            epistemic_class=prop["epistemic_class"],
            derivation=prop["derivation"],
            claim_text=prop["claim_text"],
            confidence=float(prop["confidence"]),
            structured=prop.get("structured") or prop.get("structured_json"),
            proposition_id=prop.get("id"),
            create_initial_revision=True,
            create_pending_review=True,
            reviewer_user_id=reviewer_user_id,
        )
        prop_by_ref[prop["client_ref"]] = row["id"]
        prop_rows.append(row)

        for ev in prop.get("evidence") or []:
            span_id = ev.get("document_span_id") or ev.get("span_id")
            if span_id is None and ev.get("stable_span_id"):
                span_id = by_stable.get(ev["stable_span_id"])
            if span_id is None:
                span_id = by_page.get(ev["page_no"])
            if span_id is None:
                raise ExtractionError(
                    f"No document_span for evidence on {prop['client_ref']} "
                    f"page={ev.get('page_no')}"
                )
            insert_proposition_evidence(
                conn,
                extracted_proposition_id=row["id"],
                document_span_id=span_id,
                page_no=int(ev["page_no"]),
                quote_text=ev.get("quote_text")
                or ev.get("quote")
                or ev.get("quote_internal")
                or "",
                char_start=ev.get("char_start"),
                char_end=ev.get("char_end"),
                relevance=ev.get("relevance"),
            )

    rel_rows: list[dict[str, Any]] = []
    for rel in relations or []:
        from_id = rel.get("from_proposition_id") or prop_by_ref.get(rel.get("from_ref", ""))
        to_id = rel.get("to_proposition_id") or prop_by_ref.get(rel.get("to_ref", ""))
        if from_id is None or to_id is None:
            raise ExtractionError(f"Cannot resolve relation endpoints: {rel}")
        rel_rows.append(
            insert_proposition_relation(
                conn,
                extraction_run_id=run["id"],
                from_proposition_id=from_id,
                to_proposition_id=to_id,
                relation_type=rel["relation_type"],
            )
        )

    return {
        "extraction_run": run,
        "spans": span_rows,
        "propositions": prop_rows,
        "relations": rel_rows,
    }
