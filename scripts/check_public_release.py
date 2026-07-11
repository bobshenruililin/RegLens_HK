#!/usr/bin/env python3
"""Validate a public release directory: checksums + privacy scan."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.hashutil import sha256_file  # noqa: E402
from reglens_worker.release import scan_public_artifact  # noqa: E402


def verify_checksums(release_dir: Path) -> list[str]:
    checksums = release_dir / "checksums.sha256"
    if not checksums.is_file():
        return [f"missing checksums.sha256 under {release_dir}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(checksums.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            errors.append(f"checksums.sha256:{line_no}: malformed line")
            continue
        expected, rel = parts[0], parts[1]
        seen.add(rel)
        target = release_dir / rel
        if not target.is_file():
            errors.append(f"missing file listed in checksums: {rel}")
            continue
        actual = sha256_file(target)
        if actual != expected:
            errors.append(f"checksum mismatch for {rel}: expected={expected} actual={actual}")
    # Ensure release.json is covered
    if "release.json" not in seen:
        errors.append("checksums.sha256 does not list release.json")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate RegLens public release checksums and privacy scan"
    )
    parser.add_argument(
        "release_dir",
        nargs="?",
        default="generated/public-release",
        help="Path to a release directory (default: generated/public-release)",
    )
    args = parser.parse_args(argv)
    release_dir = Path(args.release_dir)
    if not release_dir.is_absolute():
        release_dir = ROOT / release_dir
    release_dir = release_dir.resolve()

    if not release_dir.is_dir():
        print(f"Public release check FAILED: not a directory: {release_dir}")
        return 1

    errors = verify_checksums(release_dir)
    privacy = scan_public_artifact(release_dir)
    errors.extend(privacy)

    if errors:
        print("Public release check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"Public release check OK: {release_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
