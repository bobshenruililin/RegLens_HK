from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .hashutil import sha256_file
from .ingest import ingest_manifest
from .jobs import build_job_queue
from .publication import pending_review_queue, set_proposition_review
from .search import search
from .store import LocalArtifactStore


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


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
        review_accept=bool(args.accept),
    )
    summary = [
        {
            "id": r["id"],
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
    print(
        json.dumps([h.__dict__ for h in hits], indent=2)
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
        "--accept",
        action="store_true",
        help="Auto-accept/publish propositions (synthetic demos only)",
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
    p_rev_set.add_argument("--status", required=True, choices=["pending", "accepted", "edited", "rejected"])
    p_rev_set.add_argument("--claim-text", default=None)
    p_rev_set.set_defaults(func=cmd_review_set)

    p_search = sub.add_parser("search", help="Keyword FTS over published content")
    p_search.add_argument("query")
    p_search.add_argument("--data-root", default="data")
    p_search.add_argument("--regulator", default=None)
    p_search.add_argument("--profession", default=None)
    p_search.add_argument("--prop-type", default=None)
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
