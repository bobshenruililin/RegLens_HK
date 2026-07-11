from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

LLM_PROVIDER_ENV = "LLM_PROVIDER"
APPROVED_ENV = "REAL_LLM_PROCESSING_APPROVED"
APPROVAL_RECORD_ENV = "REAL_LLM_APPROVAL_RECORD_PATH"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_PINNED_MODEL_ENV = "OPENAI_PINNED_MODEL"
SOURCE_POLICY_PATH_ENV = "REGLENS_LLM_SOURCE_POLICY_PATH"
PRIVACY_MODE_ENV = "REGLENS_PRIVACY_MODE"

OPENAI_RUNTIME_OPTIONS = MappingProxyType(
    {
        "store": False,
        "tools": (),
        "files": (),
        "web": False,
        "background": False,
    }
)


@dataclass(frozen=True)
class OpenAIGateDecision:
    provider: str
    openai_enabled: bool
    model: str | None
    reasons: tuple[str, ...]
    runtime_options: Mapping[str, object]

    def require_openai_enabled(self) -> None:
        if not self.openai_enabled:
            raise OpenAIGateError("; ".join(self.reasons) or "OpenAI processing is disabled")


@dataclass(frozen=True)
class PseudonymReplacement:
    token_type: str
    original: str
    pseudonym: str


@dataclass(frozen=True)
class PseudonymizationPreview:
    text: str
    replacements: tuple[PseudonymReplacement, ...]


class OpenAIGateError(RuntimeError):
    pass


def evaluate_openai_gate(
    *,
    env: Mapping[str, str] | None = None,
    source_policy: Mapping[str, Any] | None = None,
    source_id: str | None = None,
    path_exists: Callable[[str], bool] | None = None,
) -> OpenAIGateDecision:
    """Evaluate whether OpenAI may be used; never creates a network client."""

    current_env = env if env is not None else os.environ
    provider = current_env.get(LLM_PROVIDER_ENV, "mock").strip().lower() or "mock"
    if provider not in {"mock", "openai"}:
        raise OpenAIGateError(f"unsupported LLM_PROVIDER: {provider!r}")

    model = current_env.get(OPENAI_PINNED_MODEL_ENV)
    reasons: list[str] = []
    if provider != "openai":
        return OpenAIGateDecision(
            provider=provider,
            openai_enabled=False,
            model=None,
            reasons=("LLM_PROVIDER is not openai",),
            runtime_options=OPENAI_RUNTIME_OPTIONS,
        )

    exists = path_exists or (lambda p: Path(p).is_file())
    approval_path = current_env.get(APPROVAL_RECORD_ENV)
    policy = source_policy if source_policy is not None else _load_source_policy(current_env)

    if current_env.get(APPROVED_ENV, "").strip().lower() != "true":
        reasons.append(f"{APPROVED_ENV} is not true")
    if not approval_path:
        reasons.append(f"{APPROVAL_RECORD_ENV} is not set")
    elif not exists(approval_path):
        reasons.append(f"{APPROVAL_RECORD_ENV} does not exist")
    if not current_env.get(OPENAI_API_KEY_ENV):
        reasons.append(f"{OPENAI_API_KEY_ENV} is not set")
    if not model:
        reasons.append(f"{OPENAI_PINNED_MODEL_ENV} is not set")
    if not source_policy_allows_openai(policy, source_id=source_id):
        reasons.append("source policy does not allow OpenAI processing")
    if not _privacy_mode_is_set(current_env.get(PRIVACY_MODE_ENV)):
        reasons.append(f"{PRIVACY_MODE_ENV} is not set")

    return OpenAIGateDecision(
        provider="openai",
        openai_enabled=not reasons,
        model=model,
        reasons=tuple(reasons),
        runtime_options=OPENAI_RUNTIME_OPTIONS,
    )


def source_policy_allows_openai(
    policy: Mapping[str, Any] | None,
    *,
    source_id: str | None = None,
) -> bool:
    if not policy:
        return False
    if policy.get("llm_processing_allowed") is True:
        return True
    policies = policy.get("policies")
    if not isinstance(policies, list):
        return False
    for item in policies:
        if not isinstance(item, Mapping):
            continue
        if source_id is not None and item.get("source_id") != source_id:
            continue
        if item.get("llm_processing_allowed") is True:
            processors = item.get("allowed_llm_processors")
            return processors is None or "openai" in processors
    return False


def build_openai_payload(*, model: str, input_text: str) -> dict[str, Any]:
    """Build the only allowed OpenAI request shape for real processing."""

    return {
        "model": model,
        "input": input_text,
        "store": False,
        "tools": [],
        "parallel_tool_calls": False,
        "background": False,
    }


def pseudonymization_preview(text: str) -> PseudonymizationPreview:
    replacements: list[PseudonymReplacement] = []
    counters = {"patient": 0, "contact": 0}

    def replace(match: re.Match[str], token_type: str) -> str:
        original = match.group(0)
        if any(r.original == original for r in replacements):
            return next(r.pseudonym for r in replacements if r.original == original)
        counters[token_type] += 1
        pseudonym = f"[{token_type.upper()}_{counters[token_type]}]"
        replacements.append(
            PseudonymReplacement(
                token_type=token_type,
                original=original,
                pseudonym=pseudonym,
            )
        )
        return pseudonym

    preview = text
    for pattern in _PATIENT_PATTERNS:
        preview = pattern.sub(lambda m: replace(m, "patient"), preview)
    for pattern in _CONTACT_PATTERNS:
        preview = pattern.sub(lambda m: replace(m, "contact"), preview)
    return PseudonymizationPreview(text=preview, replacements=tuple(replacements))


def _load_source_policy(env: Mapping[str, str]) -> Mapping[str, Any] | None:
    path = env.get(SOURCE_POLICY_PATH_ENV)
    if not path:
        return None
    with Path(path).open(encoding="utf-8") as fh:
        loaded = json.load(fh)
    if not isinstance(loaded, Mapping):
        raise OpenAIGateError("source policy must be a JSON object")
    return loaded


def _privacy_mode_is_set(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"", "none", "off", "disabled"}


_PATIENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bPatient\s+[A-Z0-9]\b", re.I),
    re.compile(r"\bthe Patient\b", re.I),
    re.compile(r"\b(?:Madam|Mr|Mrs|Ms|Miss)\s+[Xx]{2,}\b"),
    re.compile(r"\b(?:Madam|Mr|Mrs|Ms|Miss)\s+[A-Z]\b"),
)

_CONTACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+?852[-\s]?)?(?:[2-9]\d{3})[-\s]?\d{4}\b"),
    re.compile(r"\b[A-Z]\d{6}\(?\d\)?\b"),
)
