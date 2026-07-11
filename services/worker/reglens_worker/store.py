from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashutil import sha256_file
from .objectstore import ObjectStore, build_object_store
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
    """Immutable blobs (via ObjectStore) + JSON metadata / decision catalog."""

    def __init__(self, root: Path, object_store: ObjectStore | None = None):
        self.root = root
        self.object_store = object_store or build_object_store(root)
        self.meta = root / "meta"
        self.seed = root / "seed"
        self.meta.mkdir(parents=True, exist_ok=True)
        self.seed.mkdir(parents=True, exist_ok=True)

    def store_blob(self, src: Path, sha256: str) -> str:
        return self.object_store.put_immutable(src, sha256)

    def write_document_record(self, record: dict[str, Any]) -> Path:
        path = self.meta / "documents" / f"{record['sha256']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def write_spans(self, sha256: str, spans: list[PageSpan]) -> Path:
        path = self.meta / "spans" / f"{sha256}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([asdict(s) for s in spans], indent=2), encoding="utf-8")
        return path

    def write_extraction(self, sha256: str, extraction: dict[str, Any]) -> Path:
        path = self.meta / "extractions" / f"{sha256}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")
        return path

    def write_decision_seed(self, decision: dict[str, Any]) -> Path:
        by_id = self.seed / "decisions" / f"{decision['id']}.json"
        by_id.parent.mkdir(parents=True, exist_ok=True)
        by_id.write_text(json.dumps(decision, indent=2), encoding="utf-8")
        # Maintain decision.json as the first/latest written for home link convenience
        path = self.seed / "decision.json"
        path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
        return path

    def list_decisions(self) -> list[dict[str, Any]]:
        folder = self.seed / "decisions"
        if not folder.exists():
            return []
        out = []
        for p in sorted(folder.glob("*.json")):
            out.append(json.loads(p.read_text(encoding="utf-8")))
        return out

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        path = self.seed / "decisions" / f"{decision_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_decision(self, decision: dict[str, Any]) -> None:
        self.write_decision_seed(decision)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def mime_for(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".htm": "text/html",
    }.get(path.suffix.lower(), "application/octet-stream")


# Back-compat re-export
def span_stable_id(document_sha256: str, span: PageSpan) -> str:
    from .determinism import span_stable_id as _stable

    return _stable(document_sha256, span)


def sync_demo_fixture_seed(repo_fixtures_seed: Path, store: LocalArtifactStore) -> None:
    """Optional: copy catalog into versioned fixtures/seed for the web app."""
    if not store.seed.exists():
        return
    repo_fixtures_seed.mkdir(parents=True, exist_ok=True)
    for src in store.seed.rglob("*.json"):
        rel = src.relative_to(store.seed)
        dest = repo_fixtures_seed / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
