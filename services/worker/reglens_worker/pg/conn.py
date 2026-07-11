"""PostgreSQL connection helpers (psycopg3)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg

from ..mode import require_postgres_dsn


def connect(**kwargs: object) -> psycopg.Connection:
    """Open a connection using `DATABASE_URL` (fail-closed via mode helpers)."""
    dsn = require_postgres_dsn()
    return psycopg.connect(dsn, **kwargs)  # type: ignore[arg-type]


@contextmanager
def transaction(**kwargs: object) -> Iterator[psycopg.Connection]:
    """Yield a connection inside an explicit transaction; commit on success."""
    with connect(**kwargs) as conn:
        with conn.transaction():
            yield conn
