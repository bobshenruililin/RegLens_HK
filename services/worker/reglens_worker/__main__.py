from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .hashutil import sha256_file
from .ingest import ingest_manifest
from .jobs import build_job_queue
from .publication import pending_review_queue, set_proposition_review
from .release import ReleaseError, build_release
from .search import search
from .store import LocalArtifactStore


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


def cmd_ingest(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve() if args.repo_root else _repo_root()
    fixtures_root = root / "fixtures"
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = root / manifest
    data_root = Path(args.data_root)
    if not data_root.is_absolute():
        data_root = root / data_root

    results = ingest_manifest(
        fixtures_root=fixtures_root,
        manifest_path=manifest,
        data_root=data_root,
        demo_auto_approve_synthetic=bool(args.demo_auto_approve_synthetic),
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
    root = Path(args.data_root)
    if not root.is_absolute():
        root = _repo_root() / root
    queue = build_job_queue(root)
    jobs = queue.list_jobs(status=args.status)
    print(json.dumps([job.__dict__ for job in jobs], indent=2, default=str))
    return 0


def cmd_jobs_claim(args: argparse.Namespace) -> int:
    root = Path(args.data_root)
    if not root.is_absolute():
        root = _repo_root() / root
    queue = build_job_queue(root)
    job = queue.claim()
    print(json.dumps(job.__dict__ if job else None, indent=2, default=str))
    return 0


def cmd_review_list(args: argparse.Namespace) -> int:
    root = Path(args.data_root)
    if not root.is_absolute():
        root = _repo_root() / root
    store = LocalArtifactStore(root)
    print(json.dumps(pending_review_queue(store), indent=2))
    return 0


def cmd_review_set(args: argparse.Namespace) -> int:
    root = Path(args.data_root)
    if not root.is_absolute():
        root = _repo_root() / root
    store = LocalArtifactStore(root)
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
    root = Path(args.data_root)
    if not root.is_absolute():
        root = _repo_root() / root
    store = LocalArtifactStore(root)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens_worker", description="RegLens HK worker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest fixture manifest (idempotent)")
    p_ingest.add_argument("--manifest", default="fixtures/manifests/m1.jsonl")
    p_ingest.add_argument("--data-root", default="data")
    p_ingest.add_argument("--repo-root", default=None)
    p_ingest.add_argument(
        "--demo-auto-approve-synthetic",
        action="store_true",
        help=(
            "Synthetic fixtures only: mark propositions accepted/published for local demo. "
            "Rejects any non-synthetic manifest row."
        ),
    )
    p_ingest.set_defaults(func=cmd_ingest)

    p_hash = sub.add_parser("hash", help="SHA-256 a file")
    p_hash.add_argument("path")
    p_hash.set_defaults(func=cmd_hash)

    p_jobs = sub.add_parser("jobs", help="Job queue operations")
    jobs_sub = p_jobs.add_subparsers(dest="jobs_cmd", required=True)
    p_jobs_list = jobs_sub.add_parser("list")
    p_jobs_list.add_argument("--data-root", default="data")
    p_jobs_list.add_argument("--status", default=None)
    p_jobs_list.set_defaults(func=cmd_jobs_list)
    p_jobs_claim = jobs_sub.add_parser("claim")
    p_jobs_claim.add_argument("--data-root", default="data")
    p_jobs_claim.set_defaults(func=cmd_jobs_claim)

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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
