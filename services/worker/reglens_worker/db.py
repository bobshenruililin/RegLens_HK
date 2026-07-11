"""Legacy optional PostgreSQL helpers (pre-RC2 experimental path).

MVP-RC2: demo-mode filesystem ingest must never write to PostgreSQL.
Postgres ingest uses ``reglens_worker.pg`` repositories via the worker loop.
"""

from __future__ import annotations

import os
from typing import Any

from .mode import get_mode


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def persist_ingest_to_postgres(decision: dict[str, Any], doc_record: dict[str, Any]) -> None:
    """
    No-op in RC2.

    Historical Milestone 2B dual-write targeted an obsolete schema (``sources``,
    ``propositions``). Demo ingest stays filesystem-only; Postgres mode persists
    through ``worker_loop._process_ingest_job_postgres``.
    """
    _ = (decision, doc_record, database_url(), get_mode())
    return
