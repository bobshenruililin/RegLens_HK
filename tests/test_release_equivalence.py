"""Demo vs PostgreSQL public-release canonical equivalence (MVP-RC2).

Requires DATABASE_URL. Builds both paths with the same release_id / released_at
and asserts decision JSON matches (public contract). Documented operational
metadata on release.json may differ and is excluded.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = ROOT / "publications" / "demo" / "editorial_annotations.v1.json"
POLICY = ROOT / "publications" / "policies" / "source_publication_policy.v1.json"
TAXONOMY = ROOT / "publications" / "taxonomy" / "taxonomy.v1.json"
MANIFEST = ROOT / "fixtures" / "manifests" / "m1.jsonl"

RELEASE_ID = "equiv-demo-0.1.0"
RELEASED_AT = "2026-07-11T12:00:00Z"

_EXCLUDE_RELEASE_KEYS = {
    "built_from",
    "artifact_location",
    "source_cutoff",
}


def _dsn() -> str | None:
    return (os.environ.get("DATABASE_URL") or "").strip() or None


@pytest.fixture(scope="module")
def pg_dsn() -> str:
    dsn = _dsn()
    if not dsn:
        pytest.skip("DATABASE_URL not set")
    try:
        with psycopg.connect(dsn) as conn:
            conn.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"DATABASE_URL not reachable: {exc}")
    return dsn


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_release_doc(doc: dict) -> dict:
    out = dict(doc)
    for k in _EXCLUDE_RELEASE_KEYS:
        out.pop(k, None)
    return out


def _truncate_operational(conn) -> None:
    """Clear operational rows; keep seeded regulators / source_collections."""
    with conn.cursor() as cur:
        cur.execute(
            """
            TRUNCATE TABLE
              audit_events,
              login_attempts,
              sessions,
              reviews,
              publication_release_items,
              publication_releases,
              editorial_annotation_categories,
              editorial_annotations,
              proposition_relations,
              proposition_evidence,
              proposition_revisions,
              extracted_propositions,
              extraction_runs,
              document_spans,
              decision_document_versions,
              decision_dates,
              decision_case_refs,
              decisions,
              document_versions,
              documents,
              acquisitions,
              blobs,
              jobs,
              users
            RESTART IDENTITY CASCADE
            """
        )
    conn.commit()


def test_demo_postgres_release_canonical_equivalence(pg_dsn: str, tmp_path: Path) -> None:
    from reglens_worker.ingest import ingest_manifest
    from reglens_worker.migrate import migrate
    from reglens_worker.pg.annotations import upsert_annotation
    from reglens_worker.pg.releases import (
        add_release_item,
        approve_and_build_release,
        create_draft_release,
    )
    from reglens_worker.pg.reviews import accept_or_edit
    from reglens_worker.pg.users import create_user
    from reglens_worker.release import build_release
    from reglens_worker.release_postgres import build_release_from_postgres
    from reglens_worker.worker_loop import default_worker_id, enqueue_manifest, run_once

    migrate(pg_dsn)
    with psycopg.connect(pg_dsn) as conn:
        _truncate_operational(conn)

    # --- Demo filesystem path ---
    os.environ["REGLENS_MODE"] = "demo"
    demo_data = tmp_path / "demo-data"
    demo_out = tmp_path / "demo-release"
    ingest_manifest(
        fixtures_root=ROOT / "fixtures",
        manifest_path=MANIFEST,
        data_root=demo_data,
        demo_auto_approve_synthetic=True,
        enqueue_jobs=False,
    )
    demo_manifest = build_release(
        data_root=demo_data,
        annotations_path=ANNOTATIONS,
        policy_path=POLICY,
        taxonomy_path=TAXONOMY,
        release_id=RELEASE_ID,
        release_mode="synthetic_demo",
        released_at=RELEASED_AT,
        output_dir=demo_out,
    )
    assert demo_manifest["decision_count"] == 3
    assert demo_manifest["proposition_count"] == 17

    # --- Postgres path ---
    os.environ["REGLENS_MODE"] = "postgres"
    pg_data = tmp_path / "pg-data"
    enqueue_manifest(
        fixtures_root=ROOT / "fixtures",
        manifest_path=MANIFEST,
        data_root=pg_data,
    )
    worker = default_worker_id()
    for _ in range(16):
        job = run_once(worker, data_root=pg_data, fixtures_root=ROOT / "fixtures")
        if job is None:
            break

    with psycopg.connect(pg_dsn) as conn:
        admin = create_user(
            conn,
            username="equiv-admin",
            password="equiv_admin_local_only",
            role="admin",
        )
        admin_id = admin["id"]

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rv.extracted_proposition_id, pr.revision_number, d.fixture_kind
                FROM reviews rv
                JOIN proposition_revisions pr ON pr.id = rv.proposition_revision_id
                JOIN decisions d ON d.id = rv.decision_id
                WHERE rv.review_status = 'pending'
                """
            )
            pending = cur.fetchall()
        assert len(pending) == 17
        for prop_id, rev_no, kind in pending:
            assert kind == "synthetic"
            accept_or_edit(
                conn,
                extracted_proposition_id=prop_id,
                reviewer_user_id=admin_id,
                expected_head_revision_number=int(rev_no),
                claim_text=None,
                notes="equiv test auto-accept synthetic",
            )

        payload = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
        taxonomy_version = payload.get("taxonomy_version") or "1.0.0"
        for ann in payload.get("annotations") or []:
            note = ann.get("editorial_note") or {}
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM decisions WHERE external_ref = %s",
                    (ann["external_ref"],),
                )
                drow = cur.fetchone()
            assert drow is not None
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
                decision_id=drow[0],
                created_by_user_id=admin_id,
                updated_by_user_id=admin_id,
            )

        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM decisions WHERE fixture_kind = 'synthetic' ORDER BY external_ref"
            )
            decisions = [r[0] for r in cur.fetchall()]
        assert len(decisions) == 3

        draft = create_draft_release(
            conn,
            release_id=RELEASE_ID,
            release_mode="synthetic_demo",
            title="Equivalence synthetic demo",
            description="Demo/Postgres equivalence fixture",
            corpus="Synthetic",
            methodology_version="1.0.0",
            taxonomy_version="1.0.0",
            inclusion_criteria="Synthetic accepted revisions",
            exclusion_criteria="Real fixtures",
            global_caveats=["DEMO ONLY"],
            regulators=["MCHK", "DCHK"],
            created_by_user_id=admin_id,
        )
        for did in decisions:
            add_release_item(
                conn,
                publication_release_id=draft["id"],
                decision_id=did,
                included=True,
            )
        approved = approve_and_build_release(
            conn,
            publication_release_id=draft["id"],
            expected_version=int(draft["version"]),
            actor_user_id=admin_id,
        )
        conn.commit()

        pg_out = tmp_path / "pg-release"
        if pg_out.exists():
            shutil.rmtree(pg_out)
        pg_manifest = build_release_from_postgres(
            conn,
            publication_release_id=approved["id"],
            policy_path=POLICY,
            taxonomy_path=TAXONOMY,
            output_dir=pg_out,
            released_at=RELEASED_AT,
            mark_published=True,
        )
        conn.commit()

    assert pg_manifest["decision_count"] == demo_manifest["decision_count"]
    assert pg_manifest["proposition_count"] == demo_manifest["proposition_count"]
    assert pg_manifest["schema_version"] == demo_manifest["schema_version"]

    demo_release = _normalize_release_doc(_load_json(demo_out / "release.json"))  # type: ignore[arg-type]
    pg_release = _normalize_release_doc(_load_json(pg_out / "release.json"))  # type: ignore[arg-type]
    assert demo_release["release_id"] == pg_release["release_id"] == RELEASE_ID
    assert demo_release["released_at"] == pg_release["released_at"] == RELEASED_AT
    assert demo_release["decision_count"] == pg_release["decision_count"]
    assert demo_release["proposition_count"] == pg_release["proposition_count"]

    demo_names = sorted(p.name for p in (demo_out / "decisions").glob("*.json"))
    pg_names = sorted(p.name for p in (pg_out / "decisions").glob("*.json"))
    assert demo_names == pg_names
    for name in demo_names:
        a = _load_json(demo_out / "decisions" / name)
        b = _load_json(pg_out / "decisions" / name)
        assert a == b, f"decision mismatch for {name}"
