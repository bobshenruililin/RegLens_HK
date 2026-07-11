"""Optional PostgreSQL persistence (Milestone 2B)."""

from __future__ import annotations

import json
import os
from typing import Any


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def persist_ingest_to_postgres(decision: dict[str, Any], doc_record: dict[str, Any]) -> None:
    """Upsert document, spans, decision and propositions when DATABASE_URL is set."""
    dsn = database_url()
    if not dsn:
        return

    import psycopg

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sources WHERE source_id = %s", (doc_record["source_id"],))
            source = cur.fetchone()
            if not source:
                raise RuntimeError(f"Unknown source_id {doc_record['source_id']}; run migrations")
            source_id = source[0]

            cur.execute(
                """
                INSERT INTO documents (
                  id, source_id, external_ref, title, language, mime_type, byte_size,
                  sha256, storage_key, ingest_status, text_quality, ocr_used, immutable
                ) VALUES (
                  %s::uuid, %s, %s, %s, 'en', %s, %s, %s, %s, %s, %s, false, true
                )
                ON CONFLICT (sha256) DO UPDATE SET ingest_status = EXCLUDED.ingest_status
                RETURNING id
                """,
                (
                    doc_record["document_id"],
                    source_id,
                    doc_record.get("external_ref"),
                    doc_record.get("title"),
                    doc_record["mime_type"],
                    doc_record["byte_size"],
                    doc_record["sha256"],
                    doc_record["storage_key"],
                    doc_record.get("ingest_status", "segmented"),
                    doc_record.get("text_quality"),
                ),
            )
            document_row = cur.fetchone()
            if document_row is None:
                raise RuntimeError("document upsert returned no row")
            document_uuid = document_row[0]

            for span in doc_record.get("spans", []):
                cur.execute(
                    """
                    INSERT INTO document_spans (
                      document_id, page_no, span_type, char_start, char_end, text, text_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, page_no, span_type, text_hash) DO NOTHING
                    """,
                    (
                        document_uuid,
                        span["page_no"],
                        span.get("span_type", "page"),
                        span.get("char_start"),
                        span.get("char_end"),
                        span["text"],
                        span["text_hash"],
                    ),
                )

            cur.execute("SELECT id FROM regulators WHERE code = %s", (decision["regulator_code"],))
            reg = cur.fetchone()
            if not reg:
                raise RuntimeError("regulator missing")
            regulator_id = reg[0]

            cur.execute(
                """
                INSERT INTO decisions (
                  id, document_id, regulator_id, case_ref, decision_date, profession, coverage_json
                ) VALUES (
                  %s::uuid, %s, %s, %s, %s::date, %s, %s::jsonb
                )
                ON CONFLICT (document_id) DO UPDATE
                  SET case_ref = EXCLUDED.case_ref,
                      coverage_json = EXCLUDED.coverage_json
                RETURNING id
                """,
                (
                    decision["id"],
                    document_uuid,
                    regulator_id,
                    decision.get("case_ref"),
                    decision.get("decision_date"),
                    decision.get("profession"),
                    json.dumps(decision.get("coverage") or {}),
                ),
            )
            decision_row = cur.fetchone()
            if decision_row is None:
                raise RuntimeError("decision upsert returned no row")
            decision_uuid = decision_row[0]

            extractor = decision.get("extractor") or {}
            cur.execute(
                """
                INSERT INTO extraction_runs (
                  document_id, pipeline_version, model_provider, model_version,
                  prompt_version, status, input_hash, finished_at
                ) VALUES (%s, %s, %s, %s, %s, 'succeeded', %s, now())
                ON CONFLICT (document_id, input_hash) DO UPDATE SET status = 'succeeded'
                RETURNING id
                """,
                (
                    document_uuid,
                    extractor.get("pipeline_version", "m1.0.0"),
                    extractor.get("model_provider", "mock"),
                    extractor.get("model_version", "mock-1.0.0"),
                    extractor.get("prompt_version", "mock-prompt-1.0.0"),
                    decision["document_sha256"],
                ),
            )
            run_row = cur.fetchone()
            if run_row is None:
                raise RuntimeError("extraction_run upsert returned no row")
            run_id = run_row[0]

            # Map page_no -> span uuid
            cur.execute(
                "SELECT id, page_no FROM document_spans WHERE document_id = %s",
                (document_uuid,),
            )
            page_to_span = {page: sid for sid, page in cur.fetchall()}

            for prop in decision.get("propositions", []):
                cur.execute(
                    """
                    INSERT INTO propositions (
                      id, decision_id, extraction_run_id, prop_type, epistemic_class,
                      claim_text, confidence, review_status, published
                    ) VALUES (
                      %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      claim_text = EXCLUDED.claim_text,
                      review_status = EXCLUDED.review_status,
                      published = EXCLUDED.published
                    """,
                    (
                        prop["id"],
                        decision_uuid,
                        run_id,
                        prop["prop_type"],
                        prop["epistemic_class"],
                        prop["claim_text"],
                        prop["confidence"],
                        prop["review_status"],
                        prop["published"],
                    ),
                )
                for ev in prop.get("evidence", []):
                    span_uuid = page_to_span.get(ev["page_no"])
                    if not span_uuid:
                        continue
                    cur.execute(
                        """
                        INSERT INTO proposition_spans (proposition_id, span_id, quote_text)
                        VALUES (%s::uuid, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (prop["id"], span_uuid, ev["quote"]),
                    )

            # FTS helper table content already via generated tsvector on spans
            conn.commit()
