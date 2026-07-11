"""Storage mode helpers for RegLens HK (demo vs postgres)."""

from __future__ import annotations

import os
from urllib.parse import parse_qs, unquote, urlparse

VALID_MODES = frozenset({"demo", "postgres"})
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "db"})


def get_mode() -> str:
    """Return `REGLENS_MODE` (`demo` | `postgres`). Defaults to `demo`."""
    raw = os.environ.get("REGLENS_MODE")
    if raw is None or not raw.strip():
        return "demo"
    mode = raw.strip().lower()
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid REGLENS_MODE={raw!r}; expected demo|postgres")
    return mode


def require_postgres_dsn() -> str:
    """
    Return `DATABASE_URL`.

    Fail closed when `REGLENS_MODE=postgres` and `DATABASE_URL` is unset/empty.
    Also rejects an empty DSN in any mode when a caller explicitly requires one.
    """
    dsn = (os.environ.get("DATABASE_URL") or "").strip()
    if get_mode() == "postgres" and not dsn:
        raise RuntimeError(
            "REGLENS_MODE=postgres requires DATABASE_URL (fail-closed; refusing to continue)"
        )
    if not dsn:
        raise RuntimeError("DATABASE_URL is required but empty or unset")
    return dsn


def assert_local_database_url(url: str) -> str:
    """
    Allow only local / docker-compose database URLs suitable for destructive reset.

    Accepted hosts: localhost, 127.0.0.1, ::1, docker service name `db`,
    and Unix-domain sockets (path hosts or `.s.PGSQL` in the URL).
    Remote hosts are rejected.
    """
    if url is None or not str(url).strip():
        raise ValueError("DATABASE_URL is empty or missing")
    url = str(url).strip()

    if ".s.PGSQL" in url:
        return url

    parsed = urlparse(url)
    host = parsed.hostname

    qs = parse_qs(parsed.query)
    if "host" in qs and qs["host"]:
        host = unquote(qs["host"][0])

    if host is None or host == "":
        # postgresql:///dbname → default local socket
        return url

    if host.startswith("/"):
        return url

    if host.lower() in _LOCAL_HOSTS:
        return url

    raise ValueError(
        f"Refusing non-local DATABASE_URL host {host!r}; "
        "only localhost/127.0.0.1/::1/db or Unix sockets are allowed for reset"
    )
