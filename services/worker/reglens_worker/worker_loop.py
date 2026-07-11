"""Worker loop: enqueue manifests and process ingest jobs (MVP-RC2 Checkpoint B)."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from . import PIPELINE_VERSION
from .determinism import job_dedupe_key
from .hashutil import sha256_file
from .ingest import ManifestRow, ManifestSafetyError, ingest_fixture, load_manifest
from .jobs import DEFAULT_LEASE_SECONDS, Job, JobQueue, build_job_queue
from .mode import get_mode, require_postgres_dsn
from .objectstore import build_object_store
from .store import LocalArtifactStore, mime_for

MOCK_PROMPT_VERSION = "mock-prompt-2.0.0"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def enqueue_manifest(
    *,
    fixtures_root: Path,
    manifest_path: Path,
    data_root: Path,
    queue: JobQueue | None = None,
) -> list[Job]:
    """
    Enqueue ingest jobs for each manifest row.

    Demo mode: file queue + payload with relative_path for ``ingest_fixture``.
    Postgres mode: store blob, insert blob/acquisition rows, enqueue job payload
    with acquisition_id / sha256 references.
    """
    data_root = Path(data_root)
    queue = queue or build_job_queue(data_root)
    rows = load_manifest(manifest_path)
    mode = get_mode()
    jobs: list[Job] = []

    if mode == "postgres":
        jobs.extend(
            _enqueue_manifest_postgres(
                fixtures_root=fixtures_root,
                rows=rows,
                data_root=data_root,
                queue=queue,
            )
        )
    else:
        for row in rows:
            src = fixtures_root / row.relative_path
            if not src.is_file():
                raise FileNotFoundError(src)
            digest = sha256_file(src)
            dedupe = job_dedupe_key(
                job_type="ingest_fixture",
                document_sha256=digest,
                pipeline_version=PIPELINE_VERSION,
                prompt_version=MOCK_PROMPT_VERSION,
            )
            job = queue.enqueue(
                "ingest_fixture",
                dedupe,
                {
                    "relative_path": row.relative_path,
                    "regulator_code": row.regulator_code,
                    "source_id": row.source_id,
                    "fixture_kind": row.fixture_kind,
                    "external_ref": row.external_ref,
                    "title": row.title,
                    "source_url": row.source_url,
                    "downloaded_at": row.downloaded_at,
                    "notes": row.notes,
                    "document_sha256": digest,
                },
            )
            jobs.append(job)
    return jobs


def _enqueue_manifest_postgres(
    *,
    fixtures_root: Path,
    rows: list[ManifestRow],
    data_root: Path,
    queue: JobQueue,
) -> list[Job]:
    import psycopg

    dsn = require_postgres_dsn()
    store = build_object_store(data_root)
    jobs: list[Job] = []

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for row in rows:
                src = fixtures_root / row.relative_path
                if not src.is_file():
                    raise FileNotFoundError(src)
                digest = sha256_file(src)
                storage_key = store.put_immutable(src, digest)
                byte_size = src.stat().st_size
                mime_type = mime_for(src)

                cur.execute(
                    "SELECT id FROM source_collections WHERE source_id = %s",
                    (row.source_id,),
                )
                sc = cur.fetchone()
                if sc is None:
                    raise RuntimeError(
                        f"Unknown source_id {row.source_id!r}; run migrations / seed"
                    )
                source_collection_id = sc[0]

                cur.execute(
                    """
                    INSERT INTO blobs (sha256, storage_key, byte_size, mime_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (sha256) DO UPDATE
                      SET storage_key = EXCLUDED.storage_key
                    RETURNING id
                    """,
                    (digest, storage_key, byte_size, mime_type),
                )
                blob_row = cur.fetchone()
                if blob_row is None:
                    raise RuntimeError("blob upsert returned no row")
                blob_id = blob_row[0]

                external_ref = row.external_ref or row.relative_path
                cur.execute(
                    """
                    INSERT INTO acquisitions (
                      source_collection_id, blob_id, external_ref, source_url,
                      fixture_kind, title, notes, acquired_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_collection_id, external_ref) DO UPDATE
                      SET blob_id = EXCLUDED.blob_id,
                          title = COALESCE(EXCLUDED.title, acquisitions.title),
                          notes = COALESCE(EXCLUDED.notes, acquisitions.notes)
                    RETURNING id
                    """,
                    (
                        source_collection_id,
                        blob_id,
                        external_ref,
                        row.source_url,
                        row.fixture_kind,
                        row.title or src.name,
                        row.notes,
                        "enqueue_manifest",
                    ),
                )
                acq_row = cur.fetchone()
                if acq_row is None:
                    raise RuntimeError("acquisition upsert returned no row")
                acquisition_id = str(acq_row[0])

                dedupe = job_dedupe_key(
                    job_type="ingest_fixture",
                    document_sha256=digest,
                    pipeline_version=PIPELINE_VERSION,
                    prompt_version=MOCK_PROMPT_VERSION,
                )
                payload = {
                    "acquisition_id": acquisition_id,
                    "blob_id": str(blob_id),
                    "document_sha256": digest,
                    "storage_key": storage_key,
                    "regulator_code": row.regulator_code,
                    "source_id": row.source_id,
                    "fixture_kind": row.fixture_kind,
                    "external_ref": external_ref,
                    "relative_path": row.relative_path,
                    "title": row.title,
                }
                # Enqueue outside the same cursor transaction ownership of JobQueue
                # connections — commit acquisition rows first, then enqueue.
                conn.commit()
                jobs.append(queue.enqueue("ingest_fixture", dedupe, payload))
    return jobs


def _manifest_row_from_payload(payload: dict[str, Any]) -> ManifestRow:
    relative_path = payload.get("relative_path")
    if not relative_path:
        raise ValueError("ingest job payload missing relative_path")
    kind = payload.get("fixture_kind")
    if kind not in {"synthetic", "real"}:
        raise ManifestSafetyError(
            f"ingest job missing fixture_kind=synthetic|real for {relative_path}"
        )
    return ManifestRow(
        regulator_code=payload["regulator_code"],
        source_id=payload["source_id"],
        relative_path=relative_path,
        fixture_kind=kind,
        external_ref=payload.get("external_ref"),
        title=payload.get("title"),
        source_url=payload.get("source_url"),
        downloaded_at=payload.get("downloaded_at"),
        notes=payload.get("notes"),
    )


def process_ingest_job(
    job: Job,
    *,
    fixtures_root: Path,
    data_root: Path,
    demo_auto_approve_synthetic: bool = False,
) -> dict[str, Any]:
    """
    Process one ``ingest_fixture`` job.

    Demo path: run ``ingest_fixture`` when payload has ``relative_path``.
    Postgres path (Checkpoint B stub): verify acquisition/blob and record progress.
    """
    if job.job_type != "ingest_fixture":
        raise ValueError(f"Unsupported job_type for process_ingest_job: {job.job_type}")

    payload = job.payload_json or {}
    mode = get_mode()

    if mode == "postgres":
        return _process_ingest_job_postgres(job, data_root=data_root)

    row = _manifest_row_from_payload(payload)
    store = LocalArtifactStore(Path(data_root))
    decision = ingest_fixture(
        fixtures_root=fixtures_root,
        store=store,
        row=row,
        demo_auto_approve_synthetic=demo_auto_approve_synthetic,
    )
    return {
        "mode": "demo",
        "decision_id": decision["id"],
        "run_key": decision["run_key"],
        "document_sha256": decision["document_sha256"],
    }


def _process_ingest_job_postgres(job: Job, *, data_root: Path) -> dict[str, Any]:
    """Checkpoint B stub: validate acquisition/blob rows and record progress."""
    import psycopg

    payload = job.payload_json or {}
    acquisition_id = payload.get("acquisition_id")
    sha256 = payload.get("document_sha256")
    storage_key = payload.get("storage_key")
    if not acquisition_id:
        raise ValueError("postgres ingest job missing acquisition_id")

    dsn = require_postgres_dsn()
    store = build_object_store(data_root)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id::text, a.fixture_kind, a.external_ref, a.title,
                       b.sha256, b.storage_key, b.byte_size
                FROM acquisitions a
                JOIN blobs b ON b.id = a.blob_id
                WHERE a.id = %s::uuid
                """,
                (acquisition_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(f"acquisition {acquisition_id} not found")
            _acq_id, fixture_kind, external_ref, title, blob_sha, blob_key, byte_size = row
            if sha256 and blob_sha != sha256:
                raise RuntimeError(f"acquisition blob sha mismatch: payload={sha256} db={blob_sha}")
            key = storage_key or blob_key
            # Verify object store bytes when present.
            if store.exists(key):
                store.get(key, expected_sha256=blob_sha)

            progress = {
                "job_id": job.id,
                "acquisition_id": acquisition_id,
                "document_sha256": blob_sha,
                "storage_key": key,
                "fixture_kind": fixture_kind,
                "external_ref": external_ref,
                "title": title,
                "byte_size": byte_size,
                "stage": "queued_validated",
                "note": (
                    "RC2 Checkpoint B postgres stub: acquisition/blob verified; "
                    "full segment+extract persistence lands in a later checkpoint."
                ),
            }
            cur.execute(
                """
                INSERT INTO audit_events (actor, action, entity_type, entity_id, after_json)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (
                    f"worker:{job.lease_owner or 'unknown'}",
                    "ingest.progress",
                    "acquisition",
                    str(acquisition_id),
                    json.dumps(progress),
                ),
            )
            conn.commit()
    return {"mode": "postgres", **progress}


def run_once(
    worker_id: str,
    *,
    data_root: Path | None = None,
    fixtures_root: Path | None = None,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    demo_auto_approve_synthetic: bool = False,
) -> Job | None:
    """Claim at most one job, process it, and succeed/fail the lease."""
    root = _repo_root()
    data_root = Path(data_root) if data_root else root / "data"
    fixtures_root = Path(fixtures_root) if fixtures_root else root / "fixtures"
    if not data_root.is_absolute():
        data_root = root / data_root
    if not fixtures_root.is_absolute():
        fixtures_root = root / fixtures_root

    queue = build_job_queue(data_root)
    queue.recover_expired_leases()
    job = queue.claim(worker_id=worker_id, lease_seconds=lease_seconds)
    if job is None:
        return None

    try:
        process_ingest_job(
            job,
            fixtures_root=fixtures_root,
            data_root=data_root,
            demo_auto_approve_synthetic=demo_auto_approve_synthetic,
        )
        queue.heartbeat(job.id, worker_id, lease_seconds=lease_seconds)
        queue.succeed(job.id, worker_id)
        job.status = "succeeded"
        job.lease_owner = None
        job.lease_expires_at = None
        job.last_error = None
    except Exception as exc:  # noqa: BLE001 — worker boundary
        queue.fail(job.id, worker_id, str(exc), retry=True)
        raise
    return job


def run_forever(
    worker_id: str,
    *,
    data_root: Path | None = None,
    fixtures_root: Path | None = None,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    idle_sleep_seconds: float = 1.0,
    demo_auto_approve_synthetic: bool = False,
) -> None:
    """Poll the queue until interrupted."""
    while True:
        job = run_once(
            worker_id,
            data_root=data_root,
            fixtures_root=fixtures_root,
            lease_seconds=lease_seconds,
            demo_auto_approve_synthetic=demo_auto_approve_synthetic,
        )
        if job is None:
            time.sleep(idle_sleep_seconds)


def default_worker_id() -> str:
    return os.environ.get("REGLENS_WORKER_ID") or f"worker-{uuid.uuid4().hex[:8]}"
