"""Idempotent job queue (Milestone 2B).

Uses PostgreSQL when DATABASE_URL is set; otherwise a local JSONL/SQLite-free
file-backed queue under data/jobs for deterministic local/CI operation.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import JOB_STATUSES, JOB_TYPES


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


class FileJobQueue:
    def __init__(self, root: Path):
        self.root = root
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
                return Job(**row)
        job = Job(
            id=str(uuid.uuid4()),
            job_type=job_type,
            dedupe_key=dedupe_key,
            payload_json=payload,
            status="pending",
            attempts=0,
            last_error=None,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        rows.append(asdict(job))
        self._write(rows)
        return job

    def claim(self) -> Job | None:
        rows = self._read()
        for row in rows:
            if row["status"] == "pending":
                row["status"] = "running"
                row["attempts"] = int(row.get("attempts", 0)) + 1
                row["started_at"] = _utcnow()
                row["updated_at"] = _utcnow()
                self._write(rows)
                return Job(**row)
        return None

    def complete(self, job_id: str, *, error: str | None = None) -> None:
        rows = self._read()
        for row in rows:
            if row["id"] == job_id:
                row["status"] = "failed" if error else "succeeded"
                row["last_error"] = error
                row["finished_at"] = _utcnow()
                row["updated_at"] = _utcnow()
                self._write(rows)
                return
        raise KeyError(job_id)

    def mark_succeeded_by_dedupe(self, dedupe_key: str) -> None:
        rows = self._read()
        for row in rows:
            if row["dedupe_key"] == dedupe_key:
                row["status"] = "succeeded"
                row["finished_at"] = _utcnow()
                row["updated_at"] = _utcnow()
                if not row.get("started_at"):
                    row["started_at"] = row["finished_at"]
                self._write(rows)
                return

    def list_jobs(self, status: str | None = None) -> list[Job]:
        rows = self._read()
        out = [Job(**r) for r in rows]
        if status:
            out = [j for j in out if j.status == status]
        return out


class PostgresJobQueue:
    def __init__(self, dsn: str):
        import psycopg

        self.dsn = dsn
        self._psycopg = psycopg

    def enqueue(self, job_type: str, dedupe_key: str, payload: dict[str, Any]) -> Job:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO jobs (job_type, dedupe_key, payload_json, status)
                    VALUES (%s, %s, %s::jsonb, 'pending')
                    ON CONFLICT (dedupe_key) DO UPDATE
                      SET dedupe_key = EXCLUDED.dedupe_key
                    RETURNING id::text, job_type, dedupe_key, payload_json, status,
                              attempts, last_error, created_at, updated_at,
                              started_at, finished_at
                    """,
                    (job_type, dedupe_key, json.dumps(payload)),
                )
                row = cur.fetchone()
                conn.commit()
        return self._row_to_job(row)

    def claim(self) -> Job | None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'running',
                        attempts = attempts + 1,
                        started_at = now(),
                        updated_at = now()
                    WHERE id = (
                      SELECT id FROM jobs
                      WHERE status = 'pending'
                      ORDER BY created_at
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                    )
                    RETURNING id::text, job_type, dedupe_key, payload_json, status,
                              attempts, last_error, created_at, updated_at,
                              started_at, finished_at
                    """
                )
                row = cur.fetchone()
                conn.commit()
        return self._row_to_job(row) if row else None

    def complete(self, job_id: str, *, error: str | None = None) -> None:
        status = "failed" if error else "succeeded"
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = %s, last_error = %s, finished_at = now(), updated_at = now()
                    WHERE id = %s::uuid
                    """,
                    (status, error, job_id),
                )
                conn.commit()

    def mark_succeeded_by_dedupe(self, dedupe_key: str) -> None:
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = 'succeeded', finished_at = now(), updated_at = now(),
                        started_at = COALESCE(started_at, now())
                    WHERE dedupe_key = %s
                    """,
                    (dedupe_key,),
                )
                conn.commit()

    def list_jobs(self, status: str | None = None) -> list[Job]:
        sql = """
            SELECT id::text, job_type, dedupe_key, payload_json, status,
                   attempts, last_error, created_at, updated_at, started_at, finished_at
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
            attempts=row[5],
            last_error=row[6],
            created_at=str(row[7]),
            updated_at=str(row[8]),
            started_at=str(row[9]) if row[9] else None,
            finished_at=str(row[10]) if row[10] else None,
        )


def build_job_queue(data_root: Path) -> FileJobQueue | PostgresJobQueue:
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return PostgresJobQueue(dsn)
    return FileJobQueue(data_root / "jobs")
