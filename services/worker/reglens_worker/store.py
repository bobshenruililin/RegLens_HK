from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashutil import sha256_file, sha256_text
from .segment import PageSpan


@dataclass
class StoredDocument:
    document_id: str
    sha256: str
    storage_key: str
    mime_type: str
    byte_size: int
    regulator_code: str
    source_id: str
    external_ref: str | None
    title: str | None
    relative_path: str


class LocalArtifactStore:
    """
    Milestone 1 local store: immutable object blobs + JSON metadata.
    Mirrors what Postgres/MinIO will hold once Compose is available.
    """

    def __init__(self, root: Path):
        self.root = root
        self.objects = root / "objects"
        self.meta = root / "meta"
        self.seed = root / "seed"
        self.objects.mkdir(parents=True, exist_ok=True)
        self.meta.mkdir(parents=True, exist_ok=True)
        self.seed.mkdir(parents=True, exist_ok=True)

    def store_blob(self, src: Path, sha256: str) -> str:
        storage_key = f"sha256/{sha256[:2]}/{sha256}"
        dest = self.objects / storage_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            # Idempotent: identical content is a no-op.
            existing = sha256_file(dest)
            if existing != sha256:
                raise RuntimeError(f"Hash collision or corrupt blob at {dest}")
            return storage_key
        shutil.copy2(src, dest)
        # Write-once marker
        (dest.parent / f"{sha256}.immutable").write_text("1", encoding="utf-8")
        return storage_key

    def write_document_record(self, record: dict[str, Any]) -> Path:
        path = self.meta / "documents" / f"{record['sha256']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return path
        path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def write_spans(self, sha256: str, spans: list[PageSpan]) -> Path:
        path = self.meta / "spans" / f"{sha256}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(s) for s in spans]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def write_extraction(self, sha256: str, extraction: dict[str, Any]) -> Path:
        path = self.meta / "extractions" / f"{sha256}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")
        return path

    def write_decision_seed(self, decision: dict[str, Any]) -> Path:
        # Stable demo page target
        path = self.seed / "decision.json"
        path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
        # Also index by id
        by_id = self.seed / "decisions" / f"{decision['id']}.json"
        by_id.parent.mkdir(parents=True, exist_ok=True)
        by_id.write_text(json.dumps(decision, indent=2), encoding="utf-8")
        return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def mime_for(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".htm": "text/html",
    }.get(path.suffix.lower(), "application/octet-stream")


def span_stable_id(document_sha256: str, span: PageSpan) -> str:
    raw = f"{document_sha256}:{span.page_no}:{span.span_type}:{span.text_hash}"
    return sha256_text(raw)[:32]
