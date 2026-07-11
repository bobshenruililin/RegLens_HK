"""Deterministic run identity and persistent IDs (Milestone 2A)."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .hashutil import sha256_text
from .segment import PageSpan

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SCHEMA_VERSION = "2.0.0"


def document_id_for_sha256(sha256: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"reglens:doc:{sha256}"))


def decision_id_for_run(run_key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"reglens:decision:{run_key}"))


def proposition_id_for(run_key: str, client_ref: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"reglens:prop:{run_key}:{client_ref}"))


def span_stable_id(document_sha256: str, span: PageSpan) -> str:
    raw = f"{document_sha256}:{span.page_no}:{span.span_type}:{span.text_hash}"
    return sha256_text(raw)[:32]


def extraction_run_key(
    *,
    document_sha256: str,
    schema_version: str,
    pipeline_version: str,
    model_provider: str,
    model_version: str,
    prompt_version: str,
    deterministic_settings: dict[str, Any] | None = None,
) -> str:
    settings = deterministic_settings or {}
    material = "|".join(
        [
            document_sha256,
            schema_version,
            pipeline_version,
            model_provider,
            model_version,
            prompt_version,
            json.dumps(settings, sort_keys=True, separators=(",", ":")),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
