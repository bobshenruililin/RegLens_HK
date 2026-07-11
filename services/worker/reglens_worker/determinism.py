"""Deterministic identifiers and job dedupe keys (Milestone 2A)."""

from __future__ import annotations

import hashlib
import uuid

from .hashutil import sha256_text
from .segment import PageSpan

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace


def document_id_for_sha256(sha256: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"reglens:doc:{sha256}"))


def decision_id_for_sha256(sha256: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"reglens:decision:{sha256}"))


def span_stable_id(document_sha256: str, span: PageSpan) -> str:
    raw = f"{document_sha256}:{span.page_no}:{span.span_type}:{span.text_hash}"
    return sha256_text(raw)[:32]


def job_dedupe_key(
    *,
    job_type: str,
    document_sha256: str,
    pipeline_version: str,
    prompt_version: str = "",
) -> str:
    material = "|".join([job_type, document_sha256, pipeline_version, prompt_version])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
