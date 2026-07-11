"""PostgreSQL FTS over accepted proposition revisions (Studio)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .conn import connect


class SearchError(RuntimeError):
    """Raised when Postgres FTS fails — no substring fallback."""


@dataclass(frozen=True)
class FtsHit:
    decision_id: str
    title: str | None
    regulator_code: str
    profession: str | None
    external_ref: str
    client_ref: str
    prop_type: str
    claim_text: str
    revision_number: int
    review_status: str
    snippet: str
    score: float


def search_accepted_revisions(
    *,
    query: str,
    regulator_code: str | None = None,
    profession: str | None = None,
    prop_type: str | None = None,
    limit: int = 25,
    conn: psycopg.Connection | None = None,
) -> list[FtsHit]:
    """
    Full-text search over head proposition revisions whose latest review is
    accepted or edited. Raises `SearchError` on failure (no local fallback).
    """
    q = (query or "").strip()
    if not q:
        return []

    sql = """
      WITH head AS (
        SELECT DISTINCT ON (pr.extracted_proposition_id)
            pr.id AS revision_id,
            pr.decision_id,
            pr.extracted_proposition_id,
            pr.revision_number,
            pr.prop_type,
            pr.claim_text,
            pr.claim_tsv,
            ep.client_ref
        FROM proposition_revisions pr
        JOIN extracted_propositions ep ON ep.id = pr.extracted_proposition_id
        ORDER BY pr.extracted_proposition_id, pr.revision_number DESC
      ),
      latest_review AS (
        SELECT DISTINCT ON (rv.proposition_revision_id)
            rv.proposition_revision_id,
            rv.review_status
        FROM reviews rv
        ORDER BY rv.proposition_revision_id, rv.created_at DESC
      )
      SELECT
          d.id::text AS decision_id,
          d.title,
          r.code AS regulator_code,
          d.profession,
          d.external_ref,
          h.client_ref,
          h.prop_type,
          h.claim_text,
          h.revision_number,
          lr.review_status,
          ts_headline(
              'english',
              h.claim_text,
              plainto_tsquery('english', %s),
              'MaxWords=24, MinWords=12'
          ) AS snippet,
          ts_rank(h.claim_tsv, plainto_tsquery('english', %s)) AS score
      FROM head h
      JOIN latest_review lr ON lr.proposition_revision_id = h.revision_id
      JOIN decisions d ON d.id = h.decision_id
      JOIN regulators r ON r.id = d.regulator_id
      WHERE lr.review_status IN ('accepted', 'edited')
        AND h.claim_tsv @@ plainto_tsquery('english', %s)
    """
    params: list[Any] = [q, q, q]
    if regulator_code:
        sql += " AND r.code = %s"
        params.append(regulator_code)
    if profession:
        sql += " AND d.profession = %s"
        params.append(profession)
    if prop_type:
        sql += " AND h.prop_type = %s"
        params.append(prop_type)
    sql += " ORDER BY score DESC, d.external_ref, h.client_ref LIMIT %s"
    params.append(limit)

    owns_conn = conn is None
    try:
        if owns_conn:
            conn = connect()
        assert conn is not None
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    except SearchError:
        raise
    except Exception as exc:
        raise SearchError(f"PostgreSQL FTS failed: {exc}") from exc
    finally:
        if owns_conn and conn is not None:
            conn.close()

    return [
        FtsHit(
            decision_id=row["decision_id"],
            title=row["title"],
            regulator_code=row["regulator_code"],
            profession=row["profession"],
            external_ref=row["external_ref"],
            client_ref=row["client_ref"],
            prop_type=row["prop_type"],
            claim_text=row["claim_text"],
            revision_number=int(row["revision_number"]),
            review_status=row["review_status"],
            snippet=(row["snippet"] or row["claim_text"] or "")[:240],
            score=float(row["score"] or 0),
        )
        for row in rows
    ]


def search(
    *,
    query: str,
    regulator_code: str | None = None,
    profession: str | None = None,
    prop_type: str | None = None,
    limit: int = 25,
    conn: psycopg.Connection | None = None,
) -> list[FtsHit]:
    """Alias for `search_accepted_revisions` (raise on failure)."""
    return search_accepted_revisions(
        query=query,
        regulator_code=regulator_code,
        profession=profession,
        prop_type=prop_type,
        limit=limit,
        conn=conn,
    )


def decision_ids_from_hits(hits: list[FtsHit]) -> list[UUID]:
    return [UUID(h.decision_id) for h in hits]
