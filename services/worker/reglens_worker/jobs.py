"""PostgreSQL-first job queue with leases (MVP-RC2 Checkpoint B).

``REGLENS_MODE=postgres`` uses ``PostgresJobQueue`` (fail-closed on missing DSN).
``REGLENS_MODE=demo`` (default) uses ``FileJobQueue`` for local/CI demos only.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from .contracts import JOB_TYPES
from .mode import get_mode, require_postgres_dsn

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LEASE_SECONDS = 60
MAX_BACKOFF_SECONDS = 300


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _dt_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).replace(microsecond=0).isoformat()


def retry_wait_seconds(attempts: int) -> int:
    """Bounded exponential backoff based on attempt count."""
    exp = max(0, min(int(attempts), 8))
    return min(MAX_BACKOFF_SECONDS, 2**exp)


@dataclass
class Job:
    id: str
    job_type: str
    dedupe_key: str
    payload_json: dict[str, Any]
    status: str
    attempts: int
    last_error: str | None
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    lease_owner: str | None = None
    lease_expires_at: str | None = None
    available_at: str | None = None


def _job_from_mapping(row: dict[str, Any]) -> Job:
    allowed = {f.name for f in fields(Job)}
    payload = {k: v for k, v in row.items() if k in allowed}
    if "max_attempts" not in payload or payload["max_attempts"] is None:
        payload["max_attempts"] = DEFAULT_MAX_ATTEMPTS
    if "available_at" not in payload or payload["available_at"] is None:
        payload["available_at"] = payload.get("created_at")
    return Job(**payload)


class JobQueue(Protocol):
    def enqueue(self, job_type: str, dedupe_key: str, payload: dict[str, Any]) -> Job: ...

    def claim(
        self, *, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS
    ) -> Job | None: ...

    def heartbeat(
        self,
        job_id: str,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None: ...

    def succeed(self, job_id: str, worker_id: str) -> None: ...

    def fail(
        self,
        job_id: str,
        worker_id: str,
        error: str,
        *,
        retry: bool = True,
    ) -> None: ...

    def cancel(self, job_id: str) -> None: ...

    def recover_expired_leases(self) -> int: ...

    def list_jobs(self, status: str | None = None) -> list[Job]: ...


class FileJobQueue:
    """File-backed job queue for ``REGLENS_MODE=demo`` only.

    Not for production. Provides the same lease/retry surface as Postgres so
    local CI and synthetic demos can exercise the worker loop without a database.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "jobs.json"
        if not self.path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def enqueue(self, job_type: str, dedupe_key: str, payload: dict[str, Any]) -> Job:
        if job_type not in JOB_TYPES:
            raise ValueError(f"Unknown job_type: {job_type}")
        rows = self._read()
        for row in rows:
            if row["dedupe_key"] == dedupe_key:
                return _job_from_mapping(row)
        now = _utcnow_iso()
        job = Job(
            id=str(uuid.uuid4()),
            job_type=job_type,
            dedupe_key=dedupe_key,
            payload_json=payload,
            status="pending",
            attempts=0,
            last_error=None,
            created_at=now,
            updated_at=now,
            max_attempts=DEFAULT_MAX_ATTEMPTS,
            available_at=now,
        )
        rows.append(asdict(job))
        self._write(rows)
        return job

    def claim(self, *, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> Job | None:
        self.recover_expired_leases()
        rows = self._read()
        now = _utcnow()
        for row in rows:
            if row.get("status") != "pending":
                continue
            available = _parse_dt(row.get("available_at") or row.get("created_at"))
            if available is not None and available > now:
                continue
            row["status"] = "running"
            row["attempts"] = int(row.get("attempts", 0)) + 1
            row["lease_owner"] = worker_id
            row["lease_expires_at"] = _dt_iso(now + timedelta(seconds=lease_seconds))
            row["started_at"] = row.get("started_at") or _dt_iso(now)
            row["updated_at"] = _dt_iso(now)
            row["finished_at"] = None
            self._write(rows)
            return _job_from_mapping(row)
        return None

    def heartbeat(
        self,
        job_id: str,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None:
        rows = self._read()
        for row in rows:
            if row["id"] != job_id:
                continue
            if row.get("status") != "running":
                raise RuntimeError(f"Job {job_id} is not running (status={row.get('status')})")
            if row.get("lease_owner") != worker_id:
                raise RuntimeError(
                    f"Job {job_id} lease owned by {row.get('lease_owner')!r}, not {worker_id!r}"
                )
            now = _utcnow()
            row["lease_expires_at"] = _dt_iso(now + timedelta(seconds=lease_seconds))
            row["updated_at"] = _dt_iso(now)
            self._write(rows)
            return
        raise KeyError(job_id)

    def succeed(self, job_id: str, worker_id: str) -> None:
        rows = self._read()
        for row in rows:
            if row["id"] != job_id:
                continue
            if row.get("status") != "running":
                raise RuntimeError(f"Job {job_id} is not running (status={row.get('status')})")
            if row.get("lease_owner") != worker_id:
                raise RuntimeError(
                    f"Job {job_id} lease owned by {row.get('lease_owner')!r}, not {worker_id!r}"
                )
            now = _dt_iso(_utcnow())
            row["status"] = "succeeded"
            row["lease_owner"] = None
            row["lease_expires_at"] = None
            row["last_error"] = None
            row["finished_at"] = now
            row["updated_at"] = now
            self._write(rows)
            return
        raise KeyError(job_id)

    def fail(
        self,
        job_id: str,
        worker_id: str,
        error: str,
        *,
        retry: bool = True,
    ) -> None:
        rows = self._read()
        for row in rows:
            if row["id"] != job_id:
                continue
            if row.get("status") != "running":
                raise RuntimeError(f"Job {job_id} is not running (status={row.get('status')})")
            if row.get("lease_owner") != worker_id:
                raise RuntimeError(
                    f"Job {job_id} lease owned by {row.get('lease_owner')!r}, not {worker_id!r}"
                )
            now = _utcnow()
            attempts = int(row.get("attempts", 0))
            max_attempts = int(row.get("max_attempts", DEFAULT_MAX_ATTEMPTS))
            row["last_error"] = error
            row["lease_owner"] = None
            row["lease_expires_at"] = None
            row["updated_at"] = _dt_iso(now)
            # Dead-letter when attempts exhausted or retry disabled.
            if (not retry) or attempts >= max_attempts:
                row["status"] = "failed"
                row["finished_at"] = _dt_iso(now)
            else:
                delay = retry_wait_seconds(attempts)
                row["status"] = "pending"
                row["available_at"] = _dt_iso(now + timedelta(seconds=delay))
                row["finished_at"] = None
            self._write(rows)
            return
        raise KeyError(job_id)

    def cancel(self, job_id: str) -> None:
        rows = self._read()
        for row in rows:
            if row["id"] != job_id:
                continue
            if row.get("status") in {"succeeded", "cancelled"}:
                return
            now = _dt_iso(_utcnow())
            row["status"] = "cancelled"
            row["lease_owner"] = None
            row["lease_expires_at"] = None
            row["finished_at"] = now
            row["updated_at"] = now
            self._write(rows)
            return
        raise KeyError(job_id)

    def recover_expired_leases(self) -> int:
        rows = self._read()
        now = _utcnow()
        recovered = 0
        for row in rows:
            if row.get("status") != "running":
                continue
            expires = _parse_dt(row.get("lease_expires_at"))
            if expires is None or expires > now:
                continue
            row["status"] = "pending"
            row["lease_owner"] = None
            row["lease_expires_at"] = None
            row["updated_at"] = _dt_iso(now)
            # Keep available_at as-is so backoff still applies if previously set.
            if not row.get("available_at"):
                row["available_at"] = _dt_iso(now)
            recovered += 1
        if recovered:
            self._write(rows)
        return recovered

    def list_jobs(self, status: str | None = None) -> list[Job]:
        rows = self._read()
        out = [_job_from_mapping(r) for r in rows]
        if status:
            out = [j for j in out if j.status == status]
        return out

    def retry(self, job_id: str) -> Job:
        """Re-queue a failed/cancelled job (demo CLI helper)."""
        rows = self._read()
        for row in rows:
            if row["id"] != job_id:
                continue
            if row.get("status") not in {"failed", "cancelled", "pending"}:
                raise RuntimeError(
                    f"Job {job_id} cannot be retried from status={row.get('status')}"
                )
            now = _dt_iso(_utcnow())
            row["status"] = "pending"
            row["lease_owner"] = None
            row["lease_expires_at"] = None
            row["available_at"] = now
            row["finished_at"] = None
            row["updated_at"] = now
            self._write(rows)
            return _job_from_mapping(row)
        raise KeyError(job_id)

    def mark_succeeded_by_dedupe(self, dedupe_key: str) -> None:
        """Inline demo helper: mark enqueued job succeeded without a lease claim."""
        rows = self._read()
        for row in rows:
            if row["dedupe_key"] != dedupe_key:
                continue
            now = _dt_iso(_utcnow())
            row["status"] = "succeeded"
            row["lease_owner"] = None
            row["lease_expires_at"] = None
            row["finished_at"] = now
            row["updated_at"] = now
            if not row.get("started_at"):
                row["started_at"] = now
            self._write(rows)
            return


class PostgresJobQueue:
    """PostgreSQL job queue using ``FOR UPDATE SKIP LOCKED`` leases."""

    def __init__(self, dsn: str):
        import psycopg

        self.dsn = dsn
        self._psycopg = psycopg

    def enqueue(self, job_type: str, dedupe_key: str, payload: dict[str, Any]) -> Job:
        if job_type not in JOB_TYPES:
            raise ValueError(f"Unknown job_type: {job_type}")
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO jobs (job_type, dedupe_key, payload_json, status)
                    VALUES (%s, %s, %s::jsonb, 'pending')
                    ON CONFLICT (dedupe_key) DO NOTHING
                    RETURNING id::text, job_type, dedupe_key, payload_json, status,
                              attempts, max_attempts, last_error,
                              created_at, updated_at, started_at, finished_at,
                              lease_owner, lease_expires_at, available_at
                    """,
                    (job_type, dedupe_key, json.dumps(payload)),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        SELECT id::text, job_type, dedupe_key, payload_json, status,
                               attempts, max_attempts, last_error,
                               created_at, updated_at, started_at, finished_at,
                               lease_owner, lease_expires_at, available_at
                        FROM jobs
                        WHERE dedupe_key = %s
                        """,
                        (dedupe_key,),
                    )
                    row = cur.fetchone()
                conn.commit()
        if row is None:
            raise RuntimeError("job enqueue returned no row")
        return self._row_to_job(row)

    def claim(self, *, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> Job | None:
        self.recover_expired_leases()
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'running',
                        attempts = attempts + 1,
                        lease_owner = %s,
                        lease_expires_at = now() + (%s || ' seconds')::interval,
                        started_at = COALESCE(started_at, now()),
                        finished_at = NULL,
                        updated_at = now()
                    WHERE id = (
                      SELECT id FROM jobs
                      WHERE status = 'pending'
                        AND available_at <= now()
                      ORDER BY created_at
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                    )
                    RETURNING id::text, job_type, dedupe_key, payload_json, status,
                              attempts, max_attempts, last_error,
                              created_at, updated_at, started_at, finished_at,
                              lease_owner, lease_expires_at, available_at
                    """,
                    (worker_id, str(int(lease_seconds))),
                )
                row = cur.fetchone()
                conn.commit()
        return self._row_to_job(row) if row else None

    def heartbeat(
        self,
        job_id: str,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET lease_expires_at = now() + (%s || ' seconds')::interval,
                        updated_at = now()
                    WHERE id = %s::uuid
                      AND status = 'running'
                      AND lease_owner = %s
                    """,
                    (str(int(lease_seconds)), job_id, worker_id),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(
                        f"heartbeat failed for job {job_id} (missing, not running, "
                        f"or lease not owned by {worker_id!r})"
                    )
                conn.commit()

    def succeed(self, job_id: str, worker_id: str) -> None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'succeeded',
                        lease_owner = NULL,
                        lease_expires_at = NULL,
                        last_error = NULL,
                        finished_at = now(),
                        updated_at = now()
                    WHERE id = %s::uuid
                      AND status = 'running'
                      AND lease_owner = %s
                    """,
                    (job_id, worker_id),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(
                        f"succeed failed for job {job_id} (missing, not running, "
                        f"or lease not owned by {worker_id!r})"
                    )
                conn.commit()

    def fail(
        self,
        job_id: str,
        worker_id: str,
        error: str,
        *,
        retry: bool = True,
    ) -> None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT attempts, max_attempts
                    FROM jobs
                    WHERE id = %s::uuid
                      AND status = 'running'
                      AND lease_owner = %s
                    FOR UPDATE
                    """,
                    (job_id, worker_id),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError(
                        f"fail failed for job {job_id} (missing, not running, "
                        f"or lease not owned by {worker_id!r})"
                    )
                attempts, max_attempts = int(row[0]), int(row[1])
                dead_letter = (not retry) or attempts >= max_attempts
                if dead_letter:
                    cur.execute(
                        """
                        UPDATE jobs
                        SET status = 'failed',
                            last_error = %s,
                            lease_owner = NULL,
                            lease_expires_at = NULL,
                            finished_at = now(),
                            updated_at = now()
                        WHERE id = %s::uuid
                        """,
                        (error, job_id),
                    )
                else:
                    delay = retry_wait_seconds(attempts)
                    cur.execute(
                        """
                        UPDATE jobs
                        SET status = 'pending',
                            last_error = %s,
                            lease_owner = NULL,
                            lease_expires_at = NULL,
                            available_at = now() + (%s || ' seconds')::interval,
                            finished_at = NULL,
                            updated_at = now()
                        WHERE id = %s::uuid
                        """,
                        (error, str(delay), job_id),
                    )
                conn.commit()

    def cancel(self, job_id: str) -> None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'cancelled',
                        lease_owner = NULL,
                        lease_expires_at = NULL,
                        finished_at = now(),
                        updated_at = now()
                    WHERE id = %s::uuid
                      AND status NOT IN ('succeeded', 'cancelled')
                    """,
                    (job_id,),
                )
                if cur.rowcount != 1:
                    # Idempotent if already cancelled/succeeded; else missing.
                    cur.execute(
                        "SELECT status FROM jobs WHERE id = %s::uuid",
                        (job_id,),
                    )
                    existing = cur.fetchone()
                    if existing is None:
                        raise KeyError(job_id)
                conn.commit()

    def recover_expired_leases(self) -> int:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'pending',
                        lease_owner = NULL,
                        lease_expires_at = NULL,
                        updated_at = now()
                    WHERE status = 'running'
                      AND lease_expires_at IS NOT NULL
                      AND lease_expires_at < now()
                    """
                )
                recovered = cur.rowcount
                conn.commit()
        return int(recovered or 0)

    def list_jobs(self, status: str | None = None) -> list[Job]:
        sql = """
            SELECT id::text, job_type, dedupe_key, payload_json, status,
                   attempts, max_attempts, last_error,
                   created_at, updated_at, started_at, finished_at,
                   lease_owner, lease_expires_at, available_at
            FROM jobs
        """
        params: tuple[Any, ...] = ()
        if status:
            sql += " WHERE status = %s"
            params = (status,)
        sql += " ORDER BY created_at"
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [self._row_to_job(r) for r in rows]

    def retry(self, job_id: str) -> Job:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'pending',
                        lease_owner = NULL,
                        lease_expires_at = NULL,
                        available_at = now(),
                        finished_at = NULL,
                        updated_at = now()
                    WHERE id = %s::uuid
                      AND status IN ('failed', 'cancelled', 'pending')
                    RETURNING id::text, job_type, dedupe_key, payload_json, status,
                              attempts, max_attempts, last_error,
                              created_at, updated_at, started_at, finished_at,
                              lease_owner, lease_expires_at, available_at
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute("SELECT status FROM jobs WHERE id = %s::uuid", (job_id,))
                    existing = cur.fetchone()
                    if existing is None:
                        raise KeyError(job_id)
                    raise RuntimeError(f"Job {job_id} cannot be retried from status={existing[0]}")
                conn.commit()
        return self._row_to_job(row)

    def mark_succeeded_by_dedupe(self, dedupe_key: str) -> None:
        """Inline helper used by legacy demo ingest paths."""
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'succeeded',
                        lease_owner = NULL,
                        lease_expires_at = NULL,
                        finished_at = now(),
                        updated_at = now(),
                        started_at = COALESCE(started_at, now())
                    WHERE dedupe_key = %s
                    """,
                    (dedupe_key,),
                )
                conn.commit()

    @staticmethod
    def _row_to_job(row: tuple[Any, ...]) -> Job:
        payload = row[3]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return Job(
            id=row[0],
            job_type=row[1],
            dedupe_key=row[2],
            payload_json=payload or {},
            status=row[4],
            attempts=int(row[5] or 0),
            max_attempts=int(row[6] or DEFAULT_MAX_ATTEMPTS),
            last_error=row[7],
            created_at=str(row[8]),
            updated_at=str(row[9]),
            started_at=str(row[10]) if row[10] else None,
            finished_at=str(row[11]) if row[11] else None,
            lease_owner=row[12],
            lease_expires_at=str(row[13]) if row[13] else None,
            available_at=str(row[14]) if row[14] else None,
        )


def build_job_queue(data_root: Path) -> JobQueue:
    """Build queue for the active ``REGLENS_MODE``.

    Postgres mode fails closed without ``DATABASE_URL``. Demo mode uses the
    file-backed queue under ``data_root/jobs``.
    """
    if get_mode() == "postgres":
        return PostgresJobQueue(require_postgres_dsn())
    return FileJobQueue(Path(data_root) / "jobs")
