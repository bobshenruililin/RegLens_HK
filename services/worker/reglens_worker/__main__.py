from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .hashutil import sha256_file
from .ingest import ingest_manifest
from .jobs import build_job_queue
from .migrate import MigrationError, migrate
from .migrate import status as migration_status
from .mode import require_postgres_dsn
from .publication import pending_review_queue, set_proposition_review
from .release import ReleaseError, build_release
from .search import search
from .store import LocalArtifactStore
from .worker_loop import (
    default_worker_id,
    enqueue_manifest,
    run_forever,
    run_once,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_path(value: str | None, *, default_relative: str | None = None) -> Path:
    root = _repo_root()
    if value is None:
        if default_relative is None:
            raise ValueError("path required")
        return (root / default_relative).resolve()
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _resolve_data_root(args: argparse.Namespace) -> Path:
    root = Path(args.data_root)
    if not root.is_absolute():
        root = _repo_root() / root
    return root.resolve()


def cmd_ingest_enqueue(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve() if args.repo_root else _repo_root()
    fixtures_root = root / "fixtures"
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = root / manifest
    data_root = Path(args.data_root)
    if not data_root.is_absolute():
        data_root = root / data_root

    jobs = enqueue_manifest(
        fixtures_root=fixtures_root,
        manifest_path=manifest,
        data_root=data_root,
    )
    print(
        json.dumps(
            {
                "enqueued": len(jobs),
                "jobs": [
                    {
                        "id": j.id,
                        "job_type": j.job_type,
                        "dedupe_key": j.dedupe_key,
                        "status": j.status,
                    }
                    for j in jobs
                ],
            },
            indent=2,
        )
    )
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """
    Legacy ingest entrypoint.

    Always enqueues manifest rows. With ``--inline-demo-synthetic`` (or the
    compat flag ``--demo-auto-approve-synthetic``) also processes inline for
    synthetic demo fixtures only — real fixtures are rejected.
    """
    if getattr(args, "ingest_cmd", None) == "enqueue":
        return cmd_ingest_enqueue(args)

    root = Path(args.repo_root).resolve() if args.repo_root else _repo_root()
    fixtures_root = root / "fixtures"
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = root / manifest
    data_root = Path(args.data_root)
    if not data_root.is_absolute():
        data_root = root / data_root

    inline = bool(
        getattr(args, "inline_demo_synthetic", False)
        or getattr(args, "demo_auto_approve_synthetic", False)
    )
    if not inline:
        return cmd_ingest_enqueue(args)

    results = ingest_manifest(
        fixtures_root=fixtures_root,
        manifest_path=manifest,
        data_root=data_root,
        demo_auto_approve_synthetic=True,
    )
    summary = [
        {
            "id": r["id"],
            "run_key": r["run_key"],
            "sha256": r["document_sha256"],
            "title": r["title"],
            "propositions": len(r["propositions"]),
            "published": sum(1 for p in r["propositions"] if p["published"]),
            "pages": len(r["pages"]),
        }
        for r in results
    ]
    print(json.dumps({"ingested": len(results), "decisions": summary}, indent=2))
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    print(sha256_file(Path(args.path)))
    return 0


def cmd_jobs_list(args: argparse.Namespace) -> int:
    queue = build_job_queue(_resolve_data_root(args))
    jobs = queue.list_jobs(status=args.status)
    print(json.dumps([job.__dict__ for job in jobs], indent=2, default=str))
    return 0


def cmd_jobs_retry(args: argparse.Namespace) -> int:
    queue = build_job_queue(_resolve_data_root(args))
    if not hasattr(queue, "retry"):
        print("retry is not supported by this queue backend", file=sys.stderr)
        return 1
    try:
        job = queue.retry(args.job_id)
    except KeyError:
        print(f"job not found: {args.job_id}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"jobs retry FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(job.__dict__, indent=2, default=str))
    return 0


def cmd_jobs_cancel(args: argparse.Namespace) -> int:
    queue = build_job_queue(_resolve_data_root(args))
    try:
        queue.cancel(args.job_id)
    except KeyError:
        print(f"job not found: {args.job_id}", file=sys.stderr)
        return 1
    print(json.dumps({"cancelled": args.job_id}, indent=2))
    return 0


def cmd_worker_run_once(args: argparse.Namespace) -> int:
    worker_id = args.worker_id or default_worker_id()
    try:
        job = run_once(
            worker_id,
            data_root=_resolve_data_root(args),
            fixtures_root=_resolve_path(args.fixtures_root, default_relative="fixtures")
            if args.fixtures_root
            else None,
            lease_seconds=args.lease_seconds,
            demo_auto_approve_synthetic=bool(args.demo_auto_approve_synthetic),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"worker run-once FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(job.__dict__ if job else None, indent=2, default=str))
    return 0


def cmd_worker_run(args: argparse.Namespace) -> int:
    worker_id = args.worker_id or default_worker_id()
    try:
        run_forever(
            worker_id,
            data_root=_resolve_data_root(args),
            fixtures_root=_resolve_path(args.fixtures_root, default_relative="fixtures")
            if args.fixtures_root
            else None,
            lease_seconds=args.lease_seconds,
            idle_sleep_seconds=args.idle_sleep,
            demo_auto_approve_synthetic=bool(args.demo_auto_approve_synthetic),
        )
    except KeyboardInterrupt:
        print(json.dumps({"stopped": True, "worker_id": worker_id}, indent=2))
        return 0
    return 0


def cmd_review_list(args: argparse.Namespace) -> int:
    store = LocalArtifactStore(_resolve_data_root(args))
    print(json.dumps(pending_review_queue(store), indent=2))
    return 0


def cmd_review_set(args: argparse.Namespace) -> int:
    store = LocalArtifactStore(_resolve_data_root(args))
    decision = set_proposition_review(
        store,
        decision_id=args.decision_id,
        proposition_id=args.proposition_id,
        review_status=args.status,
        claim_text=args.claim_text,
        publish=None if args.status in {"accepted", "edited"} else False,
    )
    print(json.dumps({"id": decision["id"], "updated": args.proposition_id}, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    store = LocalArtifactStore(_resolve_data_root(args))
    hits = search(
        store,
        query=args.query,
        regulator_code=args.regulator,
        profession=args.profession,
        prop_type=args.prop_type,
    )
    print(json.dumps([h.__dict__ for h in hits], indent=2))
    return 0


def cmd_release_build(args: argparse.Namespace) -> int:
    data_root = _resolve_path(args.data_root, default_relative="data")
    annotations = _resolve_path(
        args.annotations,
        default_relative="publications/demo/editorial_annotations.v1.json",
    )
    policy = _resolve_path(
        args.policy,
        default_relative="publications/policies/source_publication_policy.v1.json",
    )
    taxonomy = _resolve_path(
        args.taxonomy,
        default_relative="publications/taxonomy/taxonomy.v1.json",
    )
    output = _resolve_path(args.output, default_relative="generated/public-release")
    try:
        manifest = build_release(
            data_root=data_root,
            annotations_path=annotations,
            policy_path=policy,
            taxonomy_path=taxonomy,
            release_id=args.release_id,
            release_mode=args.release_mode,
            released_at=args.released_at,
            output_dir=output,
            title=args.title,
            description=args.description,
        )
    except ReleaseError as exc:
        print(f"release build FAILED: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "release_id": manifest["release_id"],
                "release_mode": manifest["release_mode"],
                "decision_count": manifest["decision_count"],
                "proposition_count": manifest["proposition_count"],
                "output": str(output),
            },
            indent=2,
        )
    )
    return 0


def cmd_db_migrate(args: argparse.Namespace) -> int:
    try:
        dsn = require_postgres_dsn()
        applied = migrate(dsn)
    except (MigrationError, RuntimeError, ValueError) as exc:
        print(f"db migrate FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"applied": applied}, indent=2))
    return 0


def cmd_db_status(args: argparse.Namespace) -> int:
    try:
        dsn = require_postgres_dsn()
        rows = migration_status(dsn)
    except (MigrationError, RuntimeError, ValueError) as exc:
        print(f"db status FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(rows, indent=2))
    return 0


def _add_ingest_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", default="fixtures/manifests/m1.jsonl")
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--repo-root", default=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens_worker", description="RegLens HK worker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser(
        "ingest",
        help=(
            "Enqueue fixture manifest jobs. Alias: without a subcommand, enqueues only; "
            "use --inline-demo-synthetic to also process inline (synthetic demo only)."
        ),
    )
    _add_ingest_common_args(p_ingest)
    p_ingest.add_argument(
        "--inline-demo-synthetic",
        action="store_true",
        help=(
            "After enqueue, process inline for synthetic fixtures only "
            "(rejects any non-synthetic / real row)."
        ),
    )
    p_ingest.add_argument(
        "--demo-auto-approve-synthetic",
        action="store_true",
        help=(
            "Compat alias for --inline-demo-synthetic: synthetic fixtures only; "
            "mark propositions accepted/published for local demo."
        ),
    )
    ingest_sub = p_ingest.add_subparsers(dest="ingest_cmd", required=False)
    p_ingest_enqueue = ingest_sub.add_parser(
        "enqueue",
        help="Enqueue ingest jobs for each manifest row (no inline processing)",
    )
    _add_ingest_common_args(p_ingest_enqueue)
    p_ingest_enqueue.set_defaults(func=cmd_ingest_enqueue)
    p_ingest.set_defaults(func=cmd_ingest)

    p_worker = sub.add_parser("worker", help="Background worker loop")
    worker_sub = p_worker.add_subparsers(dest="worker_cmd", required=True)
    p_worker_once = worker_sub.add_parser("run-once", help="Claim and process one job")
    p_worker_once.add_argument("--data-root", default="data")
    p_worker_once.add_argument("--fixtures-root", default=None)
    p_worker_once.add_argument("--worker-id", default=None)
    p_worker_once.add_argument("--lease-seconds", type=int, default=60)
    p_worker_once.add_argument(
        "--demo-auto-approve-synthetic",
        action="store_true",
        help="When processing demo ingest jobs, auto-approve synthetic propositions",
    )
    p_worker_once.set_defaults(func=cmd_worker_run_once)
    p_worker_run = worker_sub.add_parser("run", help="Process jobs until interrupted")
    p_worker_run.add_argument("--data-root", default="data")
    p_worker_run.add_argument("--fixtures-root", default=None)
    p_worker_run.add_argument("--worker-id", default=None)
    p_worker_run.add_argument("--lease-seconds", type=int, default=60)
    p_worker_run.add_argument("--idle-sleep", type=float, default=1.0)
    p_worker_run.add_argument(
        "--demo-auto-approve-synthetic",
        action="store_true",
        help="When processing demo ingest jobs, auto-approve synthetic propositions",
    )
    p_worker_run.set_defaults(func=cmd_worker_run)

    p_hash = sub.add_parser("hash", help="SHA-256 a file")
    p_hash.add_argument("path")
    p_hash.set_defaults(func=cmd_hash)

    p_jobs = sub.add_parser("jobs", help="Job queue operations")
    jobs_sub = p_jobs.add_subparsers(dest="jobs_cmd", required=True)
    p_jobs_list = jobs_sub.add_parser("list")
    p_jobs_list.add_argument("--data-root", default="data")
    p_jobs_list.add_argument("--status", default=None)
    p_jobs_list.set_defaults(func=cmd_jobs_list)
    p_jobs_retry = jobs_sub.add_parser("retry", help="Re-queue a failed/cancelled job")
    p_jobs_retry.add_argument("job_id")
    p_jobs_retry.add_argument("--data-root", default="data")
    p_jobs_retry.set_defaults(func=cmd_jobs_retry)
    p_jobs_cancel = jobs_sub.add_parser("cancel", help="Cancel a job")
    p_jobs_cancel.add_argument("job_id")
    p_jobs_cancel.add_argument("--data-root", default="data")
    p_jobs_cancel.set_defaults(func=cmd_jobs_cancel)

    p_review = sub.add_parser("review", help="Human review operations")
    rev_sub = p_review.add_subparsers(dest="review_cmd", required=True)
    p_rev_list = rev_sub.add_parser("list")
    p_rev_list.add_argument("--data-root", default="data")
    p_rev_list.set_defaults(func=cmd_review_list)
    p_rev_set = rev_sub.add_parser("set")
    p_rev_set.add_argument("--data-root", default="data")
    p_rev_set.add_argument("--decision-id", required=True)
    p_rev_set.add_argument("--proposition-id", required=True)
    p_rev_set.add_argument(
        "--status",
        required=True,
        choices=["pending", "accepted", "edited", "rejected"],
    )
    p_rev_set.add_argument("--claim-text", default=None)
    p_rev_set.set_defaults(func=cmd_review_set)

    p_search = sub.add_parser("search", help="Keyword FTS over published content")
    p_search.add_argument("query")
    p_search.add_argument("--data-root", default="data")
    p_search.add_argument("--regulator", default=None)
    p_search.add_argument("--profession", default=None)
    p_search.add_argument("--prop-type", default=None)
    p_search.set_defaults(func=cmd_search)

    p_release = sub.add_parser("release", help="Publication release operations")
    release_sub = p_release.add_subparsers(dest="release_cmd", required=True)
    p_rel_build = release_sub.add_parser(
        "build",
        help="Build a privacy-checked public release bundle",
    )
    p_rel_build.add_argument("--data-root", default="data")
    p_rel_build.add_argument(
        "--annotations",
        default="publications/demo/editorial_annotations.v1.json",
    )
    p_rel_build.add_argument(
        "--policy",
        default="publications/policies/source_publication_policy.v1.json",
    )
    p_rel_build.add_argument(
        "--taxonomy",
        default="publications/taxonomy/taxonomy.v1.json",
    )
    p_rel_build.add_argument("--release-id", required=True)
    p_rel_build.add_argument(
        "--release-mode",
        required=True,
        choices=["synthetic_demo", "public"],
    )
    p_rel_build.add_argument(
        "--released-at",
        required=True,
        help="ISO-8601 timestamp recorded in the release manifest (also used as generated_at)",
    )
    p_rel_build.add_argument("--output", default="generated/public-release")
    p_rel_build.add_argument("--title", default=None)
    p_rel_build.add_argument("--description", default=None)
    p_rel_build.set_defaults(func=cmd_release_build)

    p_db = sub.add_parser("db", help="Database migration operations")
    db_sub = p_db.add_subparsers(dest="db_cmd", required=True)
    p_db_migrate = db_sub.add_parser("migrate", help="Apply pending SQL migrations")
    p_db_migrate.set_defaults(func=cmd_db_migrate)
    p_db_status = db_sub.add_parser("status", help="Show SQL migration status")
    p_db_status.set_defaults(func=cmd_db_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
