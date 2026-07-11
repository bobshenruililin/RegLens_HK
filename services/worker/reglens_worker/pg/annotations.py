"""Editorial annotations keyed by decision / external_ref."""

from __future__ import annotations

import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class AnnotationError(ValueError):
    """Invalid editorial annotation input."""


_CATEGORY_KIND_MAP = {
    "issue_categories": "issue",
    "finding_outcomes": "finding_outcome",
    "sanction_categories": "sanction",
    "factor_categories": "factor",
}


def upsert_annotation(
    conn: psycopg.Connection,
    *,
    external_ref: str,
    regulator_code: str,
    taxonomy_version: str,
    summary: str,
    takeaway: str,
    reviewer_status: str,
    issue_categories: list[str] | None = None,
    finding_outcomes: list[str] | None = None,
    sanction_categories: list[str] | None = None,
    factor_categories: list[str] | None = None,
    supporting_client_refs: list[str] | None = None,
    decision_id: uuid.UUID | str | None = None,
    created_by_user_id: uuid.UUID | str | None = None,
    updated_by_user_id: uuid.UUID | str | None = None,
) -> dict[str, Any]:
    """Upsert an editorial annotation (stable on external_ref)."""
    issues = list(issue_categories or [])
    findings = list(finding_outcomes or [])
    sanctions = list(sanction_categories or [])
    factors = list(factor_categories or [])
    supporting = list(supporting_client_refs or [])

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO editorial_annotations (
                decision_id, external_ref, regulator_code, taxonomy_version,
                issue_categories, finding_outcomes, sanction_categories, factor_categories,
                summary, takeaway, supporting_client_refs, reviewer_status,
                created_by_user_id, updated_by_user_id
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            ON CONFLICT (external_ref) DO UPDATE SET
                decision_id = COALESCE(EXCLUDED.decision_id, editorial_annotations.decision_id),
                regulator_code = EXCLUDED.regulator_code,
                taxonomy_version = EXCLUDED.taxonomy_version,
                issue_categories = EXCLUDED.issue_categories,
                finding_outcomes = EXCLUDED.finding_outcomes,
                sanction_categories = EXCLUDED.sanction_categories,
                factor_categories = EXCLUDED.factor_categories,
                summary = EXCLUDED.summary,
                takeaway = EXCLUDED.takeaway,
                supporting_client_refs = EXCLUDED.supporting_client_refs,
                reviewer_status = EXCLUDED.reviewer_status,
                updated_by_user_id = EXCLUDED.updated_by_user_id,
                updated_at = now()
            RETURNING *
            """,
            (
                decision_id,
                external_ref.strip(),
                regulator_code,
                taxonomy_version,
                Jsonb(issues),
                Jsonb(findings),
                Jsonb(sanctions),
                Jsonb(factors),
                summary,
                takeaway,
                Jsonb(supporting),
                reviewer_status,
                created_by_user_id,
                updated_by_user_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise AnnotationError("annotation upsert returned no row")

        ann_id = row["id"]
        cur.execute(
            "DELETE FROM editorial_annotation_categories WHERE editorial_annotation_id = %s",
            (ann_id,),
        )
        category_payload = {
            "issue_categories": issues,
            "finding_outcomes": findings,
            "sanction_categories": sanctions,
            "factor_categories": factors,
        }
        for field, kind in _CATEGORY_KIND_MAP.items():
            for code in category_payload[field]:
                cur.execute(
                    """
                    INSERT INTO editorial_annotation_categories (
                        editorial_annotation_id, category_kind, category_code
                    ) VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (ann_id, kind, code),
                )
        return dict(row)


def get_annotation_by_decision(
    conn: psycopg.Connection,
    decision_id: uuid.UUID | str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM editorial_annotations WHERE decision_id = %s",
            (decision_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_annotation_by_external_ref(
    conn: psycopg.Connection,
    external_ref: str,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM editorial_annotations WHERE external_ref = %s",
            (external_ref,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_annotations_for_decisions(
    conn: psycopg.Connection,
    decision_ids: list[uuid.UUID | str],
) -> list[dict[str, Any]]:
    if not decision_ids:
        return []
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT * FROM editorial_annotations
            WHERE decision_id = ANY(%s::uuid[])
            """,
            (list(decision_ids),),
        )
        return [dict(row) for row in cur.fetchall()]
