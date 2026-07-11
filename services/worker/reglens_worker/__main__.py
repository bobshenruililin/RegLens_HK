from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ingest import ingest_manifest
from .hashutil import sha256_file


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
    )
    summary = [
        {
            "id": r["id"],
            "sha256": r["document_sha256"],
            "title": r["title"],
            "propositions": len(r["propositions"]),
            "pages": len(r["pages"]),
        }
        for r in results
    ]
    print(json.dumps({"ingested": len(results), "decisions": summary}, indent=2))
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    path = Path(args.path)
    print(sha256_file(path))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reglens_worker", description="RegLens HK worker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest fixture manifest (idempotent)")
    p_ingest.add_argument(
        "--manifest",
        default="fixtures/manifests/m1.jsonl",
        help="Path to manifest JSONL",
    )
    p_ingest.add_argument("--data-root", default="data", help="Local artifact root")
    p_ingest.add_argument("--repo-root", default=None)
    p_ingest.set_defaults(func=cmd_ingest)

    p_hash = sub.add_parser("hash", help="SHA-256 a file")
    p_hash.add_argument("path")
    p_hash.set_defaults(func=cmd_hash)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
