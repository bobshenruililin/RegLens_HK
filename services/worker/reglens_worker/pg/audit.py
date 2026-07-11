"""Append-only operational audit events."""

from __future__ import annotations

import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def insert_audit_event(
    conn: psycopg.Connection,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: uuid.UUID | str | None = None,
    before_json: dict[str, Any] | list[Any] | None = None,
    after_json: dict[str, Any] | list[Any] | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    """Insert an append-only audit_events row (no updates/deletes)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            INSERT INTO audit_events (
                actor, actor_user_id, action, entity_type, entity_id,
                before_json, after_json, request_id, ip_address
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                actor,
                actor_user_id,
                action,
                entity_type,
                str(entity_id),
                Jsonb(before_json) if before_json is not None else None,
                Jsonb(after_json) if after_json is not None else None,
                request_id,
                ip_address,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("insert_audit_event returned no row")
        return dict(row)
