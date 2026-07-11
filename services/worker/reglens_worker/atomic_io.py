"""Atomic filesystem helpers and immutable run artifact storage."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .hashutil import sha256_bytes, sha256_file


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> str:
    """Write JSON atomically; return SHA-256 of canonical bytes written."""
    raw = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    data = raw.encode("utf-8")
    digest = sha256_bytes(data)
    atomic_write_bytes(path, data)
    return digest


class DeterministicRunConflict(RuntimeError):
    pass


class ImmutableRunStore:
    """Store extraction outputs under run-key paths; never overwrite differing content."""

    def __init__(self, root: Path):
        self.root = root
        self.runs = root / "meta" / "runs"
        self.runs.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_key: str) -> Path:
        return self.runs / run_key

    def write_extraction(self, run_key: str, extraction: dict[str, Any]) -> tuple[Path, str]:
        directory = self.run_dir(run_key)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "extraction.json"
        hash_path = directory / "extraction.sha256"
        raw = json.dumps(extraction, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        digest = sha256_bytes(raw.encode("utf-8"))
        if path.exists():
            existing = sha256_file(path)
            if existing != digest:
                quarantine = directory / "quarantine"
                quarantine.mkdir(exist_ok=True)
                atomic_write_bytes(quarantine / f"conflict-{digest}.json", raw.encode("utf-8"))
                raise DeterministicRunConflict(
                    f"Run {run_key} output hash mismatch: stored={existing} new={digest}"
                )
            return path, existing
        atomic_write_bytes(path, raw.encode("utf-8"))
        atomic_write_text(hash_path, digest + "\n")
        return path, digest

    def write_decision(self, run_key: str, decision: dict[str, Any]) -> Path:
        directory = self.run_dir(run_key)
        path = directory / "decision.json"
        raw = json.dumps(decision, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        digest = sha256_bytes(raw.encode("utf-8"))
        if path.exists():
            existing = sha256_file(path)
            if existing != digest:
                quarantine = directory / "quarantine"
                quarantine.mkdir(exist_ok=True)
                atomic_write_bytes(
                    quarantine / f"decision-conflict-{digest}.json", raw.encode("utf-8")
                )
                raise DeterministicRunConflict(
                    f"Decision for run {run_key} changed under same run key"
                )
            return path
        atomic_write_bytes(path, raw.encode("utf-8"))
        return path

    def verify_extraction_hash(self, run_key: str) -> str:
        directory = self.run_dir(run_key)
        path = directory / "extraction.json"
        recorded = (directory / "extraction.sha256").read_text(encoding="utf-8").strip()
        actual = sha256_file(path)
        if recorded != actual:
            raise DeterministicRunConflict(
                f"Stored hash mismatch for {run_key}: recorded={recorded} actual={actual}"
            )
        return actual
