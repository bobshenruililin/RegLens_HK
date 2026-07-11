"""Keyword FTS over published propositions and page text (Milestone 2D).

Uses PostgreSQL full-text search when DATABASE_URL is set; otherwise a local
deterministic keyword scorer over the decision catalog. Semantic/pgvector
search is intentionally not implemented.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from .store import LocalArtifactStore


@dataclass
class SearchHit:
    decision_id: str
    title: str
    regulator_code: str
    profession: str | None
    prop_type: str | None
    claim_text: str | None
    page_no: int | None
    snippet: str
    score: float


def _tokens(q: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z0-9_]{2,}", q.lower())]


def local_search(
    store: LocalArtifactStore,
    *,
    query: str,
    regulator_code: str | None = None,
    profession: str | None = None,
    prop_type: str | None = None,
    limit: int = 25,
) -> list[SearchHit]:
    terms = _tokens(query)
    hits: list[SearchHit] = []
    for decision in store.list_decisions():
        if regulator_code and decision.get("regulator_code") != regulator_code:
            continue
        if profession and decision.get("profession") != profession:
            continue
        for prop in decision.get("propositions", []):
            if not prop.get("published"):
                continue
            if prop_type and prop.get("prop_type") != prop_type:
                continue
            text = f"{prop.get('claim_text', '')}"
            hay = text.lower()
            if terms and not all(t in hay for t in terms):
                # also allow page evidence quotes
                quotes = [ev.get("quote", "") for ev in prop.get("evidence", [])]
                evidence_blob = " ".join(quotes).lower()
                if not all(t in evidence_blob or t in hay for t in terms):
                    continue
            score = sum(hay.count(t) for t in terms) + 1.0
            page_no = prop["evidence"][0]["page_no"] if prop.get("evidence") else None
            hits.append(
                SearchHit(
                    decision_id=decision["id"],
                    title=decision.get("title") or decision["id"],
                    regulator_code=decision.get("regulator_code") or "",
                    profession=decision.get("profession"),
                    prop_type=prop.get("prop_type"),
                    claim_text=prop.get("claim_text"),
                    page_no=page_no,
                    snippet=text[:240],
                    score=float(score),
                )
            )
        # Page-level matches for published decisions only
        if any(p.get("published") for p in decision.get("propositions", [])):
            for page in decision.get("pages", []):
                hay = page.get("text", "").lower()
                if terms and all(t in hay for t in terms):
                    hits.append(
                        SearchHit(
                            decision_id=decision["id"],
                            title=decision.get("title") or decision["id"],
                            regulator_code=decision.get("regulator_code") or "",
                            profession=decision.get("profession"),
                            prop_type=None,
                            claim_text=None,
                            page_no=page.get("page_no"),
                            snippet=page.get("text", "")[:240],
                            score=0.5 + sum(hay.count(t) for t in terms),
                        )
                    )
    hits.sort(key=lambda h: h.score, reverse=True)
    # de-dupe by decision+prop/page
    seen: set[str] = set()
    unique: list[SearchHit] = []
    for h in hits:
        key = f"{h.decision_id}:{h.prop_type}:{h.page_no}:{h.snippet[:40]}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
        if len(unique) >= limit:
            break
    return unique


def postgres_search(
    *,
    query: str,
    regulator_code: str | None = None,
    profession: str | None = None,
    prop_type: str | None = None,
    limit: int = 25,
) -> list[SearchHit]:
    import psycopg

    dsn = os.environ["DATABASE_URL"]
    sql = """
      SELECT d.id::text, d.case_ref, r.code, d.profession, p.prop_type, p.claim_text,
             ts_rank(p.claim_tsv, plainto_tsquery('english', %s)) AS score
      FROM propositions p
      JOIN decisions d ON d.id = p.decision_id
      JOIN regulators r ON r.id = d.regulator_id
      WHERE p.published = true
        AND p.claim_tsv @@ plainto_tsquery('english', %s)
    """
    params: list[Any] = [query, query]
    if regulator_code:
        sql += " AND r.code = %s"
        params.append(regulator_code)
    if profession:
        sql += " AND d.profession = %s"
        params.append(profession)
    if prop_type:
        sql += " AND p.prop_type = %s"
        params.append(prop_type)
    sql += " ORDER BY score DESC LIMIT %s"
    params.append(limit)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [
        SearchHit(
            decision_id=row[0],
            title=row[1] or row[0],
            regulator_code=row[2],
            profession=row[3],
            prop_type=row[4],
            claim_text=row[5],
            page_no=None,
            snippet=(row[5] or "")[:240],
            score=float(row[6] or 0),
        )
        for row in rows
    ]


def search(
    store: LocalArtifactStore,
    *,
    query: str,
    regulator_code: str | None = None,
    profession: str | None = None,
    prop_type: str | None = None,
    limit: int = 25,
) -> list[SearchHit]:
    if os.environ.get("DATABASE_URL"):
        try:
            return postgres_search(
                query=query,
                regulator_code=regulator_code,
                profession=profession,
                prop_type=prop_type,
                limit=limit,
            )
        except Exception:
            # Fall back to local catalog if DB path is misconfigured in dev.
            pass
    return local_search(
        store,
        query=query,
        regulator_code=regulator_code,
        profession=profession,
        prop_type=prop_type,
        limit=limit,
    )
