#!/usr/bin/env python3
"""Hash files listed in a manifest and print an updated view (stdout)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.hashutil import sha256_file  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: hash_manifest.py fixtures/manifests/m1.jsonl", file=sys.stderr)
        return 2
    manifest = Path(sys.argv[1])
    if not manifest.is_absolute():
        manifest = ROOT / manifest
    fixtures_root = ROOT / "fixtures"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        path = fixtures_root / row["relative_path"]
        row["sha256"] = sha256_file(path)
        row["byte_size"] = path.stat().st_size
        print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
