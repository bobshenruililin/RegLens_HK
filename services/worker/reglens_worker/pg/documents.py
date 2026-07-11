"""Blobs, documents, document_versions, and acquisitions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row


class DocumentError(ValueError):
    """Invalid document / blob persistence input."""


def upsert_blob(
    conn: psycopg.Connection,
    *,
    sha256: str,
    storage_key: str,
    byte_size: int,
    mime_type: str,
    blob_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Insert content-addressed blob metadata; no-op on sha256 conflict."""
    digest = (sha256 or "").strip().lower()
    if len(digest) != 64:
        raise DocumentError(f"Invalid sha256: {sha256!r}")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO blobs (id, sha256, storage_key, byte_size, mime_type)
            VALUES (COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s)
            ON CONFLICT (sha256) DO UPDATE SET sha256 = EXCLUDED.sha256
            RETURNING *
            """,
            (blob_id, digest, storage_key, byte_size, mime_type),
        )
        row = cur.fetchone()
        if row is None:
            raise DocumentError("blob upsert returned no row")
        return dict(row)


def upsert_document(
    conn: psycopg.Connection,
    *,
    source_id: str,
    external_ref: str,
    title: str | None = None,
    language: str = "en",
    ingest_status: str = "stored",
    text_quality: str | None = None,
    ocr_used: bool = False,
    document_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Upsert logical document by (source_collection_id, external_ref)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id FROM source_collections WHERE source_id = %s",
            (source_id,),
        )
        src = cur.fetchone()
        if src is None:
            raise DocumentError(f"Unknown source_id={source_id!r}")
        cur.execute(
            """
            INSERT INTO documents (
                id, source_collection_id, external_ref, title, language,
                ingest_status, text_quality, ocr_used
            ) VALUES (
                COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (source_collection_id, external_ref) DO UPDATE SET
                title = COALESCE(EXCLUDED.title, documents.title),
                language = EXCLUDED.language,
                ingest_status = EXCLUDED.ingest_status,
                text_quality = EXCLUDED.text_quality,
                ocr_used = EXCLUDED.ocr_used,
                updated_at = now()
            RETURNING *
            """,
            (
                document_id,
                src["id"],
                external_ref.strip(),
                title,
                language,
                ingest_status,
                text_quality,
                ocr_used,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise DocumentError("document upsert returned no row")
        return dict(row)


def insert_document_version(
    conn: psycopg.Connection,
    *,
    document_id: uuid.UUID | str,
    blob_id: uuid.UUID | str,
    sha256: str,
    storage_key: str,
    version_number: int | None = None,
    acquired_at: datetime | None = None,
    note: str | None = None,
    document_version_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """
    Insert an immutable document version.

    When `version_number` is omitted, uses max(existing)+1 (or 1).
    """
    digest = (sha256 or "").strip().lower()
    with conn.cursor(row_factory=dict_row) as cur:
        if version_number is None:
            cur.execute(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
                FROM document_versions
                WHERE document_id = %s
                """,
                (document_id,),
            )
            next_row = cur.fetchone()
            if next_row is None:
                raise DocumentError("failed to allocate document version_number")
            version_number = int(next_row["next_version"])

        cur.execute(
            """
            INSERT INTO document_versions (
                id, document_id, blob_id, version_number, sha256, storage_key,
                acquired_at, note
            ) VALUES (
                COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s, %s,
                COALESCE(%s, now()), %s
            )
            ON CONFLICT (document_id, sha256) DO UPDATE SET
                storage_key = EXCLUDED.storage_key
            RETURNING *
            """,
            (
                document_version_id,
                document_id,
                blob_id,
                version_number,
                digest,
                storage_key,
                acquired_at,
                note,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise DocumentError("document_version insert returned no row")
        return dict(row)


def insert_acquisition(
    conn: psycopg.Connection,
    *,
    source_id: str,
    blob_id: uuid.UUID | str,
    external_ref: str,
    fixture_kind: str,
    source_url: str | None = None,
    title: str | None = None,
    acquired_by: str | None = None,
    notes: str | None = None,
    acquired_at: datetime | None = None,
    acquisition_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Record a manual acquisition linking a collection item to an immutable blob."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id FROM source_collections WHERE source_id = %s",
            (source_id,),
        )
        src = cur.fetchone()
        if src is None:
            raise DocumentError(f"Unknown source_id={source_id!r}")
        cur.execute(
            """
            INSERT INTO acquisitions (
                id, source_collection_id, blob_id, external_ref, source_url,
                fixture_kind, title, acquired_at, acquired_by, notes
            ) VALUES (
                COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s,
                %s, %s, COALESCE(%s, now()), %s, %s
            )
            ON CONFLICT (source_collection_id, external_ref) DO UPDATE SET
                blob_id = EXCLUDED.blob_id,
                source_url = EXCLUDED.source_url,
                title = EXCLUDED.title,
                notes = EXCLUDED.notes
            RETURNING *
            """,
            (
                acquisition_id,
                src["id"],
                blob_id,
                external_ref.strip(),
                source_url,
                fixture_kind,
                title,
                acquired_at,
                acquired_by,
                notes,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise DocumentError("acquisition insert returned no row")
        return dict(row)
