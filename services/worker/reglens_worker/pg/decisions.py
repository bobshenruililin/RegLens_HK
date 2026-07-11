"""Decision identity and upsert helpers."""

from __future__ import annotations

import re
import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

# Same URL namespace as determinism.py — stable across demo and postgres modes.
DECISION_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class DecisionError(ValueError):
    """Invalid decision identity or upsert input."""


def decision_id_for(source_id: str, external_ref: str) -> uuid.UUID:
    """Stable decision UUID derived from source collection + external_ref."""
    if not source_id or not str(source_id).strip():
        raise DecisionError("source_id is required")
    if not external_ref or not str(external_ref).strip():
        raise DecisionError("external_ref is required")
    material = f"reglens:decision:{source_id.strip()}:{external_ref.strip()}"
    return uuid.uuid5(DECISION_NAMESPACE, material)


def public_slug_from_external_ref(external_ref: str) -> str:
    """Derive a public Observatory slug from a stable external_ref / case ref."""
    slug = (external_ref or "").strip().lower()
    if not slug or not _SLUG_RE.match(slug):
        raise DecisionError(f"Cannot derive public slug from external_ref={external_ref!r}")
    return slug


def upsert_decision(
    conn: psycopg.Connection,
    *,
    source_id: str,
    external_ref: str,
    profession: str,
    title: str | None = None,
    defendant_name_as_published: str | None = None,
    defendant_registration_no: str | None = None,
    appeal_status_as_stated: str | None = None,
    coverage_json: dict[str, Any] | None = None,
    fixture_kind: str = "synthetic",
    official_source_url: str | None = None,
    case_refs: list[str] | None = None,
    dates: dict[str, str | None] | None = None,
    decision_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """
    Upsert a decision by unique (source_collection_id, external_ref).

    Identity uses `decision_id_for(source_id, external_ref)` unless overridden.
    """
    did = decision_id or decision_id_for(source_id, external_ref)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT sc.id AS source_collection_id, sc.regulator_id
            FROM source_collections sc
            WHERE sc.source_id = %s
            """,
            (source_id,),
        )
        src = cur.fetchone()
        if src is None:
            raise DecisionError(f"Unknown source_id={source_id!r}; seed regulators first")

        cur.execute(
            """
            INSERT INTO decisions (
                id, regulator_id, source_collection_id, external_ref, profession,
                title, defendant_name_as_published, defendant_registration_no,
                appeal_status_as_stated, coverage_json, fixture_kind, official_source_url
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (source_collection_id, external_ref) DO UPDATE SET
                profession = EXCLUDED.profession,
                title = EXCLUDED.title,
                defendant_name_as_published = EXCLUDED.defendant_name_as_published,
                defendant_registration_no = EXCLUDED.defendant_registration_no,
                appeal_status_as_stated = EXCLUDED.appeal_status_as_stated,
                coverage_json = EXCLUDED.coverage_json,
                fixture_kind = EXCLUDED.fixture_kind,
                official_source_url = EXCLUDED.official_source_url,
                updated_at = now()
            RETURNING *
            """,
            (
                did,
                src["regulator_id"],
                src["source_collection_id"],
                external_ref.strip(),
                profession,
                title,
                defendant_name_as_published,
                defendant_registration_no,
                appeal_status_as_stated,
                Jsonb(coverage_json or {}),
                fixture_kind,
                official_source_url,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise DecisionError("decision upsert returned no row")

        decision_uuid = row["id"]
        if case_refs is not None:
            cur.execute("DELETE FROM decision_case_refs WHERE decision_id = %s", (decision_uuid,))
            for ordinal, ref in enumerate(case_refs):
                if not ref or not str(ref).strip():
                    continue
                cur.execute(
                    """
                    INSERT INTO decision_case_refs (decision_id, case_ref, ordinal)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (decision_id, case_ref) DO UPDATE SET ordinal = EXCLUDED.ordinal
                    """,
                    (decision_uuid, str(ref).strip(), ordinal),
                )

        if dates is not None:
            cur.execute("DELETE FROM decision_dates WHERE decision_id = %s", (decision_uuid,))
            for date_type, date_value in dates.items():
                if not date_value:
                    continue
                cur.execute(
                    """
                    INSERT INTO decision_dates (decision_id, date_type, date_value)
                    VALUES (%s, %s, %s::date)
                    ON CONFLICT (decision_id, date_type) DO UPDATE
                      SET date_value = EXCLUDED.date_value
                    """,
                    (decision_uuid, date_type, date_value),
                )

        return dict(row)


def get_decision(conn: psycopg.Connection, decision_id: uuid.UUID | str) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.*, r.code AS regulator_code, sc.source_id
            FROM decisions d
            JOIN regulators r ON r.id = d.regulator_id
            JOIN source_collections sc ON sc.id = d.source_collection_id
            WHERE d.id = %s
            """,
            (decision_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def link_document_version(
    conn: psycopg.Connection,
    *,
    decision_id: uuid.UUID | str,
    document_version_id: uuid.UUID | str,
    role: str = "primary",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO decision_document_versions (decision_id, document_version_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (decision_id, document_version_id) DO UPDATE SET role = EXCLUDED.role
            """,
            (decision_id, document_version_id, role),
        )
