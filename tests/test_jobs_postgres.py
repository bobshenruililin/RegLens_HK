"""PostgresJobQueue integration tests — skipped without DATABASE_URL."""

from __future__ import annotations

import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

pytestmark = pytest.mark.integration


def _dsn() -> str | None:
    return (os.environ.get("DATABASE_URL") or "").strip() or None


@pytest.fixture(scope="module")
def pg_dsn() -> str:
    dsn = _dsn()
    if not dsn:
        pytest.skip("DATABASE_URL not set")
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"DATABASE_URL not reachable: {exc}")
    return dsn


@pytest.fixture
def queue(pg_dsn: str):
    from reglens_worker.jobs import PostgresJobQueue

    return PostgresJobQueue(pg_dsn)


def test_postgres_enqueue_dedupe_claim_succeed(queue, pg_dsn: str) -> None:
    dedupe = f"test-dedupe-{uuid.uuid4().hex}"
    j1 = queue.enqueue("ingest_fixture", dedupe, {"n": 1})
    j2 = queue.enqueue("ingest_fixture", dedupe, {"n": 2})
    assert j1.id == j2.id
    assert j2.payload_json.get("n") == 1

    worker = f"itest-{uuid.uuid4().hex[:8]}"
    claimed = queue.claim(worker_id=worker, lease_seconds=60)
    # May claim an unrelated pending job if the DB is dirty; keep claiming until ours
    # or clean up by cancelling ours if we cannot claim it promptly.
    seen = []
    current = claimed
    target = None
    for _ in range(20):
        if current is None:
            break
        seen.append(current.id)
        if current.dedupe_key == dedupe:
            target = current
            break
        queue.fail(current.id, worker, "not-our-test-job", retry=False)
        current = queue.claim(worker_id=worker, lease_seconds=60)

    if target is None:
        queue.cancel(j1.id)
        pytest.fail(f"could not claim test job; claimed others={seen}")

    queue.heartbeat(target.id, worker, lease_seconds=60)
    queue.succeed(target.id, worker)
    jobs = [j for j in queue.list_jobs() if j.dedupe_key == dedupe]
    assert len(jobs) == 1
    assert jobs[0].status == "succeeded"
