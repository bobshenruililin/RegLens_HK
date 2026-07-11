"""Review queue, append-only revisions, and optimistic concurrency."""

from __future__ import annotations

import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class ReviewError(ValueError):
    """Invalid review / revision operation."""


class RevisionConflictError(ReviewError):
    """Optimistic concurrency failure on proposition revision_number."""


def list_pending(
    conn: psycopg.Connection,
    *,
    decision_id: uuid.UUID | str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List open pending reviews (default ingest state)."""
    sql = """
        SELECT
            rv.id AS review_id,
            rv.decision_id,
            rv.proposition_revision_id,
            rv.extracted_proposition_id,
            rv.review_status,
            rv.notes,
            rv.created_at AS review_created_at,
            pr.revision_number,
            pr.claim_text,
            pr.prop_type,
            pr.epistemic_class,
            pr.derivation,
            ep.client_ref,
            d.title AS decision_title,
            d.external_ref,
            r.code AS regulator_code
        FROM reviews rv
        JOIN proposition_revisions pr ON pr.id = rv.proposition_revision_id
        JOIN extracted_propositions ep ON ep.id = rv.extracted_proposition_id
        JOIN decisions d ON d.id = rv.decision_id
        JOIN regulators r ON r.id = d.regulator_id
        WHERE rv.review_status = 'pending'
    """
    params: list[Any] = []
    if decision_id is not None:
        sql += " AND rv.decision_id = %s"
        params.append(decision_id)
    sql += " ORDER BY rv.created_at ASC LIMIT %s"
    params.append(limit)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _head_revision(
    cur: Any,
    extracted_proposition_id: uuid.UUID | str,
) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT * FROM proposition_revisions
        WHERE extracted_proposition_id = %s
        ORDER BY revision_number DESC
        LIMIT 1
        FOR UPDATE
        """,
        (extracted_proposition_id,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def create_revision(
    conn: psycopg.Connection,
    *,
    extracted_proposition_id: uuid.UUID | str,
    expected_head_revision_number: int,
    claim_text: str,
    prop_type: str | None = None,
    epistemic_class: str | None = None,
    derivation: str | None = None,
    structured_json: dict[str, Any] | None = None,
    created_by_user_id: uuid.UUID | str | None = None,
    origin: str = "human_edited",
) -> dict[str, Any]:
    """
    Append a new proposition_revision with optimistic concurrency.

    `expected_head_revision_number` must equal the current max revision_number
    or a `RevisionConflictError` is raised (fail closed).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        head = _head_revision(cur, extracted_proposition_id)
        if head is None:
            raise ReviewError(f"No revisions for proposition {extracted_proposition_id}")
        current = int(head["revision_number"])
        if current != int(expected_head_revision_number):
            raise RevisionConflictError(
                f"Revision conflict for {extracted_proposition_id}: "
                f"expected_head={expected_head_revision_number}, actual={current}"
            )

        cur.execute(
            """
            INSERT INTO proposition_revisions (
                extracted_proposition_id, decision_id, revision_number,
                supersedes_revision_id, origin, prop_type, epistemic_class,
                derivation, claim_text, structured_json, created_by_user_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                extracted_proposition_id,
                head["decision_id"],
                current + 1,
                head["id"],
                origin,
                prop_type or head["prop_type"],
                epistemic_class or head["epistemic_class"],
                derivation or head["derivation"],
                claim_text,
                Jsonb(structured_json) if structured_json is not None else head["structured_json"],
                created_by_user_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise ReviewError("create_revision returned no row")
        return dict(row)


def add_review(
    conn: psycopg.Connection,
    *,
    proposition_revision_id: uuid.UUID | str,
    reviewer_user_id: uuid.UUID | str | None,
    review_status: str,
    notes: str | None = None,
    expected_revision_number: int | None = None,
) -> dict[str, Any]:
    """
    Append a review action against a proposition_revision.

    When `expected_revision_number` is provided, verifies the revision's number
    still matches (optimistic concurrency) before inserting.
    """
    if review_status not in {
        "pending",
        "accepted",
        "edited",
        "rejected",
        "disputed",
        "incomplete",
    }:
        raise ReviewError(f"Invalid review_status={review_status!r}")
    if review_status == "pending" and reviewer_user_id is not None:
        raise ReviewError("pending reviews must not set reviewer_user_id")
    if review_status != "pending" and reviewer_user_id is None:
        raise ReviewError(f"{review_status} reviews require reviewer_user_id")

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT pr.*, ep.id AS extracted_proposition_id
            FROM proposition_revisions pr
            JOIN extracted_propositions ep ON ep.id = pr.extracted_proposition_id
            WHERE pr.id = %s
            FOR UPDATE OF pr
            """,
            (proposition_revision_id,),
        )
        rev = cur.fetchone()
        if rev is None:
            raise ReviewError(f"Unknown proposition_revision_id={proposition_revision_id}")

        if expected_revision_number is not None and int(rev["revision_number"]) != int(
            expected_revision_number
        ):
            raise RevisionConflictError(
                f"Revision conflict for review: expected={expected_revision_number}, "
                f"actual={rev['revision_number']}"
            )

        # Partial unique index allows only one pending row per revision — clear it
        # before inserting a terminal review status.
        if review_status != "pending":
            cur.execute(
                """
                DELETE FROM reviews
                WHERE proposition_revision_id = %s AND review_status = 'pending'
                """,
                (proposition_revision_id,),
            )

        cur.execute(
            """
            INSERT INTO reviews (
                decision_id, proposition_revision_id, extracted_proposition_id,
                reviewer_user_id, review_status, notes
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                rev["decision_id"],
                proposition_revision_id,
                rev["extracted_proposition_id"],
                reviewer_user_id,
                review_status,
                notes,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise ReviewError("add_review returned no row")
        return dict(row)


def accept_or_edit(
    conn: psycopg.Connection,
    *,
    extracted_proposition_id: uuid.UUID | str,
    reviewer_user_id: uuid.UUID | str,
    expected_head_revision_number: int,
    claim_text: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Accept the head revision, or create an edited revision then mark it edited.

    Uses optimistic concurrency on the head revision number.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        head = _head_revision(cur, extracted_proposition_id)
        if head is None:
            raise ReviewError(f"No revisions for proposition {extracted_proposition_id}")

        if claim_text is not None and claim_text != head["claim_text"]:
            # Release lock before create_revision re-locks; same outer transaction.
            pass

    if claim_text is not None and claim_text != head["claim_text"]:
        new_rev = create_revision(
            conn,
            extracted_proposition_id=extracted_proposition_id,
            expected_head_revision_number=expected_head_revision_number,
            claim_text=claim_text,
            created_by_user_id=reviewer_user_id,
            origin="human_edited",
        )
        review = add_review(
            conn,
            proposition_revision_id=new_rev["id"],
            reviewer_user_id=reviewer_user_id,
            review_status="edited",
            notes=notes,
            expected_revision_number=int(new_rev["revision_number"]),
        )
        return {"revision": new_rev, "review": review}

    review = add_review(
        conn,
        proposition_revision_id=head["id"],
        reviewer_user_id=reviewer_user_id,
        review_status="accepted",
        notes=notes,
        expected_revision_number=expected_head_revision_number,
    )
    return {"revision": head, "review": review}
