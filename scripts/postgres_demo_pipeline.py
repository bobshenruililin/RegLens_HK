#!/usr/bin/env python3
"""Synthetic-only Postgres demo pipeline (MVP-RC2).

Steps:
  1. migrate
  2. ensure admin user (password from env)
  3. enqueue synthetic manifest
  4. worker run-once until idle (max N)
  5. auto-accept synthetic revisions ONLY (labelled demo)
  6. create draft release + approve
  7. build_release_from_postgres → generated/public-release-pg

Rejects any real fixture_kind in the manifest or database.
Requires DATABASE_URL and REGLENS_MODE=postgres.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "services" / "worker"))

DEFAULT_MANIFEST = REPO_ROOT / "fixtures" / "manifests" / "m1.jsonl"
DEFAULT_ANNOTATIONS = REPO_ROOT / "publications" / "demo" / "editorial_annotations.v1.json"
DEFAULT_POLICY = REPO_ROOT / "publications" / "policies" / "source_publication_policy.v1.json"
DEFAULT_TAXONOMY = REPO_ROOT / "publications" / "taxonomy" / "taxonomy.v1.json"
DEFAULT_OUTPUT = REPO_ROOT / "generated" / "public-release-pg"
MAX_WORKER_ITERS = 32
DEMO_REVIEW_NOTE = (
    "DEMO ONLY: auto-accept synthetic revision via scripts/postgres_demo_pipeline.py "
    "(fixture_kind=synthetic). Not a production review action."
)


def _die(msg: str, code: int = 1) -> None:
    print(f"postgres_demo_pipeline FAILED: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _require_env() -> str:
    mode = (os.environ.get("REGLENS_MODE") or "").strip().lower()
    if mode != "postgres":
        _die("REGLENS_MODE must be 'postgres' (refusing demo filesystem path)")
    dsn = (os.environ.get("DATABASE_URL") or "").strip()
    if not dsn:
        _die("DATABASE_URL is required")
    return dsn


def _load_manifest_rows(path: Path) -> list[dict]:
    from reglens_worker.ingest import load_manifest

    rows = load_manifest(path)
    for row in rows:
        if row.fixture_kind != "synthetic":
            _die(
                f"Rejecting non-synthetic fixture_kind={row.fixture_kind!r} "
                f"path={row.relative_path} (synthetic-only demo pipeline)"
            )
    return [
        {
            "relative_path": r.relative_path,
            "fixture_kind": r.fixture_kind,
            "external_ref": r.external_ref,
            "source_id": r.source_id,
            "regulator_code": r.regulator_code,
        }
        for r in rows
    ]


def step_migrate(dsn: str) -> None:
    from reglens_worker.migrate import migrate

    applied = migrate(dsn)
    print(json.dumps({"step": "migrate", "applied": applied}, indent=2))


def step_ensure_admin(conn) -> dict:
    from psycopg.rows import dict_row

    from reglens_worker.pg.users import create_user

    username = (os.environ.get("REGLENS_DEMO_ADMIN_USER") or "admin").strip()
    password = (os.environ.get("REGLENS_DEMO_ADMIN_PASSWORD") or "").strip()
    if not password:
        password = (os.environ.get("REGLENS_ADMIN_PASSWORD") or "").strip()
    if not password:
        # Local/CI demo default — never for production.
        password = "reglens_demo_admin_local_only"
        print(
            "NOTE: using default REGLENS_DEMO_ADMIN_PASSWORD="
            "reglens_demo_admin_local_only (set env to override)",
            file=sys.stderr,
        )

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, username, role, active FROM users WHERE username = %s",
            (username,),
        )
        existing = cur.fetchone()
    if existing is not None:
        print(
            json.dumps(
                {
                    "step": "ensure_admin",
                    "created": False,
                    "user_id": str(existing["id"]),
                    "username": existing["username"],
                    "role": existing["role"],
                },
                indent=2,
            )
        )
        return dict(existing)

    user = create_user(
        conn,
        username=username,
        password=password,
        role="admin",
        display_name="RC2 Demo Admin",
    )
    conn.commit()
    print(
        json.dumps(
            {
                "step": "ensure_admin",
                "created": True,
                "user_id": str(user["id"]),
                "username": user["username"],
                "role": user["role"],
            },
            indent=2,
        )
    )
    return user


def step_enqueue(data_root: Path, manifest: Path) -> list:
    from reglens_worker.worker_loop import enqueue_manifest

    jobs = enqueue_manifest(
        fixtures_root=REPO_ROOT / "fixtures",
        manifest_path=manifest,
        data_root=data_root,
    )
    print(
        json.dumps(
            {
                "step": "enqueue",
                "enqueued": len(jobs),
                "job_ids": [j.id for j in jobs],
            },
            indent=2,
        )
    )
    return jobs


def step_worker_until_idle(data_root: Path, max_iters: int = MAX_WORKER_ITERS) -> int:
    from reglens_worker.worker_loop import default_worker_id, run_once

    worker_id = default_worker_id()
    processed = 0
    for i in range(max_iters):
        job = run_once(
            worker_id,
            data_root=data_root,
            fixtures_root=REPO_ROOT / "fixtures",
            demo_auto_approve_synthetic=False,  # review step is explicit + labelled
        )
        if job is None:
            break
        processed += 1
        print(
            json.dumps(
                {
                    "step": "worker_once",
                    "iter": i + 1,
                    "job_id": job.id,
                    "status": job.status,
                    "job_type": job.job_type,
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(
            f"WARNING: reached max worker iterations ({max_iters}); queue may not be idle",
            file=sys.stderr,
        )
    print(json.dumps({"step": "worker_drain", "processed": processed}, indent=2))
    return processed


def _assert_no_real_decisions(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM decisions WHERE fixture_kind = 'real'")
        n = int(cur.fetchone()[0])
    if n:
        _die(f"Refuse demo pipeline: {n} decision(s) with fixture_kind=real present")


def step_auto_accept_synthetic(conn, admin_user_id) -> int:
    """Accept pending head revisions for synthetic decisions only — labelled DEMO."""
    from psycopg.rows import dict_row

    from reglens_worker.pg.reviews import accept_or_edit

    _assert_no_real_decisions(conn)

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                rv.id AS review_id,
                rv.extracted_proposition_id,
                rv.proposition_revision_id,
                pr.revision_number,
                d.id AS decision_id,
                d.fixture_kind,
                d.external_ref
            FROM reviews rv
            JOIN proposition_revisions pr ON pr.id = rv.proposition_revision_id
            JOIN decisions d ON d.id = rv.decision_id
            WHERE rv.review_status = 'pending'
            ORDER BY rv.created_at ASC
            """
        )
        pending = [dict(r) for r in cur.fetchall()]

    accepted = 0
    for row in pending:
        if row["fixture_kind"] != "synthetic":
            _die(
                f"Refuse auto-accept: pending review on non-synthetic decision "
                f"{row['external_ref']} fixture_kind={row['fixture_kind']!r}"
            )
        accept_or_edit(
            conn,
            extracted_proposition_id=row["extracted_proposition_id"],
            reviewer_user_id=admin_user_id,
            expected_head_revision_number=int(row["revision_number"]),
            claim_text=None,
            notes=DEMO_REVIEW_NOTE,
        )
        accepted += 1

    conn.commit()
    print(
        json.dumps(
            {
                "step": "auto_accept_synthetic",
                "label": "DEMO ONLY",
                "accepted": accepted,
                "pending_seen": len(pending),
            },
            indent=2,
        )
    )
    return accepted


def step_upsert_demo_annotations(conn, admin_user_id) -> int:
    from reglens_worker.pg.annotations import upsert_annotation

    payload = json.loads(DEFAULT_ANNOTATIONS.read_text(encoding="utf-8"))
    taxonomy_version = payload.get("taxonomy_version") or "1.0.0"
    count = 0
    for ann in payload.get("annotations") or []:
        note = ann.get("editorial_note") or {}
        # Bind to decision when present
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, fixture_kind FROM decisions WHERE external_ref = %s",
                (ann["external_ref"],),
            )
            drow = cur.fetchone()
        decision_id = None
        if drow is not None:
            if drow[1] != "synthetic":
                _die(f"Refuse annotation upsert for non-synthetic {ann['external_ref']}")
            decision_id = drow[0]
        upsert_annotation(
            conn,
            external_ref=ann["external_ref"],
            regulator_code=ann["regulator_code"],
            taxonomy_version=taxonomy_version,
            summary=note.get("summary") or "",
            takeaway=note.get("takeaway") or "",
            reviewer_status=note.get("reviewer_status") or "verified",
            issue_categories=ann.get("issue_categories"),
            finding_outcomes=ann.get("finding_outcomes"),
            sanction_categories=ann.get("sanction_categories"),
            factor_categories=ann.get("factor_categories"),
            supporting_client_refs=note.get("supporting_client_refs"),
            decision_id=decision_id,
            created_by_user_id=admin_user_id,
            updated_by_user_id=admin_user_id,
        )
        count += 1
    conn.commit()
    print(json.dumps({"step": "upsert_annotations", "count": count}, indent=2))
    return count


def step_create_and_approve_release(conn, admin_user_id) -> dict:
    from psycopg.rows import dict_row

    from reglens_worker.pg.releases import (
        add_release_item,
        approve_and_build_release,
        create_draft_release,
    )

    _assert_no_real_decisions(conn)

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, external_ref, fixture_kind
            FROM decisions
            WHERE fixture_kind = 'synthetic'
            ORDER BY external_ref
            """
        )
        decisions = [dict(r) for r in cur.fetchall()]

    if not decisions:
        _die(
            "No synthetic decisions in Postgres after worker drain. "
            "Full segment+extract persistence may still be incomplete "
            "(Checkpoint B stub). Re-run when ingest writes decisions/revisions.",
            code=2,
        )

    release_id = os.environ.get("REGLENS_DEMO_RELEASE_ID") or "pg-demo-0.1.0"
    draft = create_draft_release(
        conn,
        release_id=release_id,
        release_mode="synthetic_demo",
        title="RegLens HK Postgres synthetic demo",
        description=(
            "DEMO ONLY publication bundle built from Postgres synthetic fixtures "
            "via scripts/postgres_demo_pipeline.py."
        ),
        corpus="Synthetic MCHK/DCHK fixture decisions (Postgres path).",
        methodology_version="1.0.0",
        taxonomy_version="1.0.0",
        inclusion_criteria="Synthetic accepted/edited revisions with editorial annotations.",
        exclusion_criteria="Real fixtures; pending/rejected propositions; raw page text.",
        global_caveats=[
            "DEMO ONLY — synthetic fixtures; not real regulator judgments.",
            "Not legal advice. Not population prevalence.",
        ],
        regulators=["MCHK", "DCHK"],
        created_by_user_id=admin_user_id,
    )
    for d in decisions:
        add_release_item(
            conn,
            publication_release_id=draft["id"],
            decision_id=d["id"],
            included=True,
        )
    conn.commit()

    approved = approve_and_build_release(
        conn,
        publication_release_id=draft["id"],
        expected_version=int(draft["version"]),
        actor_user_id=admin_user_id,
    )
    conn.commit()
    print(
        json.dumps(
            {
                "step": "approve_release",
                "publication_release_id": str(approved["id"]),
                "release_id": approved["release_id"],
                "status": approved["status"],
                "version": approved["version"],
                "decision_count": len(decisions),
            },
            indent=2,
            default=str,
        )
    )
    return approved


def step_build_bundle(conn, release_row: dict, output: Path) -> dict:
    from reglens_worker.release_postgres import build_release_from_postgres

    released_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    output.mkdir(parents=True, exist_ok=True)
    manifest = build_release_from_postgres(
        conn,
        publication_release_id=release_row["id"],
        policy_path=DEFAULT_POLICY,
        taxonomy_path=DEFAULT_TAXONOMY,
        output_dir=output,
        released_at=released_at,
        mark_published=True,
    )
    conn.commit()
    print(
        json.dumps(
            {
                "step": "build_release_from_postgres",
                "release_id": manifest.get("release_id"),
                "decision_count": manifest.get("decision_count"),
                "output": str(output),
            },
            indent=2,
        )
    )
    return manifest


def main() -> int:
    dsn = _require_env()
    manifest = Path(os.environ.get("REGLENS_DEMO_MANIFEST") or DEFAULT_MANIFEST)
    if not manifest.is_absolute():
        manifest = REPO_ROOT / manifest
    data_root = Path(os.environ.get("DATA_ROOT") or REPO_ROOT / "data")
    if not data_root.is_absolute():
        data_root = REPO_ROOT / data_root
    output = Path(os.environ.get("REGLENS_PG_RELEASE_OUT") or DEFAULT_OUTPUT)
    if not output.is_absolute():
        output = REPO_ROOT / output

    print(
        json.dumps(
            {
                "pipeline": "postgres_demo_pipeline",
                "synthetic_only": True,
                "manifest": str(manifest),
                "data_root": str(data_root),
                "output": str(output),
            },
            indent=2,
        )
    )

    rows = _load_manifest_rows(manifest)
    print(json.dumps({"step": "manifest_ok", "rows": len(rows)}, indent=2))

    step_migrate(dsn)

    import psycopg

    with psycopg.connect(dsn) as conn:
        admin = step_ensure_admin(conn)
        admin_id = admin["id"]

    step_enqueue(data_root, manifest)
    step_worker_until_idle(data_root)

    with psycopg.connect(dsn) as conn:
        accepted = step_auto_accept_synthetic(conn, admin_id)
        step_upsert_demo_annotations(conn, admin_id)
        if accepted == 0:
            # Still attempt release if decisions+reviews already accepted from a prior run.
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM decisions WHERE fixture_kind = 'synthetic'")
                n_dec = int(cur.fetchone()[0])
            if n_dec == 0:
                _die(
                    "No synthetic decisions after worker; cannot build release. "
                    "Postgres ingest may still be a Checkpoint B validation stub.",
                    code=2,
                )
        release_row = step_create_and_approve_release(conn, admin_id)
        step_build_bundle(conn, release_row, output)

    import subprocess

    scan = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_public_release.py"), str(output)],
        cwd=str(REPO_ROOT),
        check=False,
    )
    if scan.returncode != 0:
        _die(f"public scan failed for {output}", code=scan.returncode)

    print(json.dumps({"pipeline": "postgres_demo_pipeline", "status": "ok"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
