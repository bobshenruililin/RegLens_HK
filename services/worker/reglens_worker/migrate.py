"""PostgreSQL SQL migration runner for RegLens HK."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import psycopg


class MigrationError(RuntimeError):
    """Raised when migrations cannot be applied safely."""


def migrations_dir() -> Path:
    """Return the repo path containing ordered `*.sql` migration files."""
    return Path(__file__).resolve().parents[3] / "packages" / "db" / "migrations"


def file_checksum(path: Path) -> str:
    """Return the SHA-256 hex digest of a migration file's bytes."""
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _require_dsn(dsn: str) -> str:
    if dsn is None or not str(dsn).strip():
        raise MigrationError("DATABASE_URL / DSN is empty or missing")
    return str(dsn).strip()


def _discover_migrations() -> list[Path]:
    directory = migrations_dir()
    if not directory.is_dir():
        raise MigrationError(f"migrations directory not found: {directory}")
    return sorted(directory.glob("*.sql"), key=lambda p: p.name)


def _ensure_schema_migrations(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id serial PRIMARY KEY,
            filename text NOT NULL UNIQUE,
            checksum text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def migrate(dsn: str) -> list[str]:
    """Apply pending migrations once. Returns filenames newly applied."""
    dsn = _require_dsn(dsn)
    applied: list[str] = []
    files = _discover_migrations()

    with psycopg.connect(dsn) as conn:
        _ensure_schema_migrations(conn)
        conn.commit()

        for path in files:
            checksum = file_checksum(path)
            row = conn.execute(
                "SELECT checksum FROM schema_migrations WHERE filename = %s",
                (path.name,),
            ).fetchone()
            if row is not None:
                existing = row[0]
                if existing != checksum:
                    raise MigrationError(
                        f"checksum mismatch for {path.name}: recorded={existing} current={checksum}"
                    )
                continue

            sql_text = path.read_text(encoding="utf-8")
            try:
                with conn.transaction():
                    with conn.cursor() as cur:
                        # No bind params → simple query protocol (multi-statement OK).
                        if sql_text.strip():
                            cur.execute(sql_text)
                        cur.execute(
                            """
                            INSERT INTO schema_migrations (filename, checksum)
                            VALUES (%s, %s)
                            """,
                            (path.name, checksum),
                        )
            except MigrationError:
                raise
            except Exception as exc:
                raise MigrationError(f"failed applying {path.name}: {exc}") from exc
            applied.append(path.name)

    return applied


def status(dsn: str) -> list[dict[str, Any]]:
    """Return per-file migration status (pending / applied / mismatch)."""
    dsn = _require_dsn(dsn)
    files = _discover_migrations()
    results: list[dict[str, Any]] = []

    with psycopg.connect(dsn) as conn:
        _ensure_schema_migrations(conn)
        conn.commit()
        rows = conn.execute(
            "SELECT filename, checksum, applied_at FROM schema_migrations"
        ).fetchall()
        recorded = {filename: (checksum, applied_at) for filename, checksum, applied_at in rows}

        for path in files:
            checksum = file_checksum(path)
            if path.name not in recorded:
                results.append(
                    {
                        "filename": path.name,
                        "checksum": checksum,
                        "applied": False,
                        "applied_at": None,
                        "status": "pending",
                    }
                )
                continue
            recorded_checksum, applied_at = recorded[path.name]
            if recorded_checksum != checksum:
                results.append(
                    {
                        "filename": path.name,
                        "checksum": checksum,
                        "recorded_checksum": recorded_checksum,
                        "applied": True,
                        "applied_at": applied_at.isoformat() if applied_at else None,
                        "status": "checksum_mismatch",
                    }
                )
            else:
                results.append(
                    {
                        "filename": path.name,
                        "checksum": checksum,
                        "applied": True,
                        "applied_at": applied_at.isoformat() if applied_at else None,
                        "status": "applied",
                    }
                )

    return results
