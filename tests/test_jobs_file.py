"""FileJobQueue unit tests (demo mode; no Postgres required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reglens_worker.jobs import FileJobQueue


def test_file_queue_dedupe_claim_succeed(tmp_path: Path) -> None:
    queue = FileJobQueue(tmp_path / "jobs")
    payload = {"relative_path": "synthetic/mchk/a.html"}

    j1 = queue.enqueue("ingest_fixture", "dedupe-1", payload)
    j2 = queue.enqueue("ingest_fixture", "dedupe-1", {"relative_path": "other.html"})
    assert j1.id == j2.id
    assert j2.payload_json["relative_path"] == "synthetic/mchk/a.html"
    assert len(queue.list_jobs()) == 1

    claimed = queue.claim(worker_id="worker-a", lease_seconds=30)
    assert claimed is not None
    assert claimed.id == j1.id
    assert claimed.status == "running"
    assert claimed.attempts == 1
    assert claimed.lease_owner == "worker-a"
    assert claimed.lease_expires_at is not None

    assert queue.claim(worker_id="worker-b") is None

    queue.heartbeat(claimed.id, "worker-a", lease_seconds=30)
    queue.succeed(claimed.id, "worker-a")

    done = queue.list_jobs(status="succeeded")
    assert len(done) == 1
    assert done[0].id == j1.id
    assert done[0].lease_owner is None


def test_file_queue_fail_retries_then_dead_letters(tmp_path: Path) -> None:
    queue = FileJobQueue(tmp_path / "jobs")
    queue.enqueue("ingest_fixture", "dedupe-fail", {"x": 1})
    # Force low max_attempts via file mutation for a short test.
    rows = queue._read()
    rows[0]["max_attempts"] = 2
    queue._write(rows)

    claimed = queue.claim(worker_id="w1")
    assert claimed is not None
    queue.fail(claimed.id, "w1", "boom", retry=True)

    pending = queue.list_jobs(status="pending")
    assert len(pending) == 1
    assert pending[0].last_error == "boom"
    assert pending[0].attempts == 1

    # available_at may be in the future due to backoff — force it now.
    rows = queue._read()
    rows[0]["available_at"] = rows[0]["created_at"]
    queue._write(rows)

    claimed2 = queue.claim(worker_id="w1")
    assert claimed2 is not None
    assert claimed2.attempts == 2
    queue.fail(claimed2.id, "w1", "boom-again", retry=True)

    failed = queue.list_jobs(status="failed")
    assert len(failed) == 1
    assert failed[0].last_error == "boom-again"


def test_file_queue_cancel_and_retry(tmp_path: Path) -> None:
    queue = FileJobQueue(tmp_path / "jobs")
    job = queue.enqueue("ingest_fixture", "dedupe-cancel", {})
    queue.cancel(job.id)
    assert queue.list_jobs(status="cancelled")[0].id == job.id

    retried = queue.retry(job.id)
    assert retried.status == "pending"

    claimed = queue.claim(worker_id="w")
    assert claimed is not None
    with pytest.raises(RuntimeError):
        queue.succeed(claimed.id, "other-worker")
