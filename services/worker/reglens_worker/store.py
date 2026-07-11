from __future__ import annotations

import shutil
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .atomic_io import ImmutableRunStore, atomic_write_json
from .hashutil import sha256_file
from .segment import PageSpan


class LocalArtifactStore:
    """Immutable blobs + metadata; extraction runs stored under run keys."""

    def __init__(self, root: Path):
        self.root = root
        self.objects = root / "objects"
        self.meta = root / "meta"
        self.seed = root / "seed"
        self.objects.mkdir(parents=True, exist_ok=True)
        self.meta.mkdir(parents=True, exist_ok=True)
        self.seed.mkdir(parents=True, exist_ok=True)
        self.runs = ImmutableRunStore(root)

    def store_blob(self, src: Path, sha256: str) -> str:
        storage_key = f"sha256/{sha256[:2]}/{sha256}"
        dest = self.objects / storage_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            existing = sha256_file(dest)
            if existing != sha256:
                raise RuntimeError(f"Hash collision or corrupt blob at {dest}")
            return storage_key
        tmp = dest.with_suffix(".tmp")
        shutil.copy2(src, tmp)
        tmp.replace(dest)
        (dest.parent / f"{sha256}.immutable").write_text("1", encoding="utf-8")
        return storage_key

    def write_document_record(self, record: dict[str, Any]) -> Path:
        path = self.meta / "documents" / f"{record['sha256']}.json"
        if path.exists():
            return path
        atomic_write_json(path, record)
        return path

    def write_spans(self, sha256: str, spans: list[PageSpan]) -> Path:
        path = self.meta / "spans" / f"{sha256}.json"
        if path.exists():
            return path
        atomic_write_json(path, [asdict(s) for s in spans])
        return path

    def write_run_extraction(self, run_key: str, extraction: dict[str, Any]) -> tuple[Path, str]:
        return self.runs.write_extraction(run_key, extraction)

    def write_run_decision(self, run_key: str, decision: dict[str, Any]) -> Path:
        return self.runs.write_decision(run_key, decision)

    def write_demo_pointer(self, decision: dict[str, Any], *, run_key: str) -> Path:
        """Mutable synthetic-demo pointer — not the audit record."""
        pointer = {
            "pointer_kind": "synthetic_demo",
            "run_key": run_key,
            "decision_id": decision["id"],
            "immutable_decision_path": f"meta/runs/{run_key}/decision.json",
            "immutable_extraction_path": f"meta/runs/{run_key}/extraction.json",
            "decision": decision,
        }
        path = self.seed / "decision.json"
        atomic_write_json(path, pointer)
        by_id = self.seed / "decisions" / f"{decision['id']}.json"
        atomic_write_json(by_id, pointer)
        return path


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def mime_for(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".htm": "text/html",
    }.get(path.suffix.lower(), "application/octet-stream")


def span_stable_id(document_sha256: str, span: PageSpan) -> str:
    from .determinism import span_stable_id as _stable

    return _stable(document_sha256, span)
