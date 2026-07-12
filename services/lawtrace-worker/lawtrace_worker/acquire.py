"""Acquisition helpers: hash, registry rows, selective extract."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lawtrace_worker.security.zip_safe import inspect_zip, safe_extract


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def registry_row(**kwargs: Any) -> dict[str, Any]:
    required = [
        "dataset_id",
        "resource_id",
        "source_url",
        "final_download_url",
        "source_organisation",
        "asset_type",
        "language",
        "version_class",
        "download_timestamp",
        "byte_size",
        "sha256",
        "terms_version",
        "terms_date",
        "local_path",
        "storage_classification",
        "derived_fixture",
        "acquisition_status",
    ]
    row = {k: kwargs.get(k) for k in required}
    row["error"] = kwargs.get("error")
    row["notes"] = kwargs.get("notes")
    row["content_length_header"] = kwargs.get("content_length_header")
    return row


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def extract_matching(
    archive: Path,
    dest: Path,
    *,
    contains: tuple[str, ...],
) -> list[Path]:
    inspect_zip(archive)
    return safe_extract(archive, dest, name_contains=contains, overwrite=True)
