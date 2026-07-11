"""Source automation policy loading and fail-closed gates."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from reglens_worker.mode import get_mode

Policy = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[4]
POLICY_PATH = REPO_ROOT / "sources" / "policies" / "source_automation_policy.v1.json"
SCHEMA_PATH = REPO_ROOT / "sources" / "schemas" / "source_automation_policy.v1.json"
USER_AGENT_PRODUCT = "RegLensHK/RC3"


class PolicyError(RuntimeError):
    """Base class for source policy failures."""


class PolicyValidationError(PolicyError):
    """Raised when the policy document does not satisfy its JSON schema."""


class SourceDisabledError(PolicyError):
    """Raised when a caller tries to use a disabled source policy."""


class AcquisitionNotAllowedError(PolicyError):
    """Raised when document acquisition is not allowed by source policy."""


class LivePrerequisiteError(PolicyError):
    """Raised when live/acquire prerequisites are missing."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise PolicyValidationError(f"policy file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PolicyValidationError(f"{path} must contain a JSON object")
    return data


def _validate_policy_document(document: dict[str, Any], schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        path = ".".join(str(part) for part in first.absolute_path) or "<root>"
        raise PolicyValidationError(f"source policy validation failed at {path}: {first.message}")

    seen: set[str] = set()
    for policy in document.get("policies", []):
        if not isinstance(policy, dict):
            raise PolicyValidationError("source policy entries must be objects")
        source_id = str(policy.get("source_id", "")).strip()
        if source_id in seen:
            raise PolicyValidationError(f"duplicate source policy for source_id={source_id!r}")
        seen.add(source_id)


@lru_cache(maxsize=1)
def load_policy_document() -> dict[str, Any]:
    """Load and validate the RC3 source automation policy."""
    schema = _read_json(SCHEMA_PATH)
    document = _read_json(POLICY_PATH)
    _validate_policy_document(document, schema)
    return document


def clear_policy_cache() -> None:
    """Clear cached policy data. Primarily useful for tests."""
    load_policy_document.cache_clear()


def get_policy(source_id: str) -> Policy:
    """Return the validated policy entry for `source_id`."""
    wanted = (source_id or "").strip()
    if not wanted:
        raise PolicyError("source_id is required")

    for policy in load_policy_document()["policies"]:
        if policy["source_id"] == wanted:
            return dict(policy)
    raise PolicyError(f"unknown source_id={source_id!r}")


def _as_policy(policy_or_source_id: Policy | str) -> Policy:
    if isinstance(policy_or_source_id, str):
        return get_policy(policy_or_source_id)
    return dict(policy_or_source_id)


def assert_enabled(policy_or_source_id: Policy | str) -> Policy:
    """
    Return policy only when enabled.

    Call this before applying any CLI mode/live/acquire flags so operator flags cannot
    override a disabled policy.
    """
    policy = _as_policy(policy_or_source_id)
    if not bool(policy.get("enabled")) or policy.get("discovery_mode") == "disabled":
        source_id = policy.get("source_id", "<unknown>")
        raise SourceDisabledError(f"source policy is disabled for {source_id}")
    if policy.get("content_use_posture") == "blocked":
        source_id = policy.get("source_id", "<unknown>")
        raise SourceDisabledError(f"source content use posture is blocked for {source_id}")
    return policy


def assert_mode_allows_acquire(policy_or_source_id: Policy | str) -> Policy:
    """Return policy only when document acquisition is explicitly policy-controlled."""
    policy = assert_enabled(policy_or_source_id)
    source_id = policy.get("source_id", "<unknown>")
    if policy.get("document_acquisition", "disabled") != "policy_controlled":
        raise AcquisitionNotAllowedError(
            f"document acquisition is not policy-controlled for {source_id}"
        )
    if policy.get("discovery_mode") not in {"metadata_only", "acquire_documents"}:
        raise AcquisitionNotAllowedError(f"discovery mode does not allow acquire for {source_id}")
    return policy


def user_agent_contact(policy_or_source_id: Policy | str) -> str | None:
    """Return configured User-Agent contact, enforcing required-contact policy."""
    policy = _as_policy(policy_or_source_id)
    contact = (os.environ.get("REGLENS_HTTP_CONTACT") or "").strip()
    if policy.get("require_user_agent_contact") and not contact:
        source_id = policy.get("source_id", "<unknown>")
        raise LivePrerequisiteError(
            f"REGLENS_HTTP_CONTACT is required by source policy for {source_id}"
        )
    return contact or None


def user_agent_for_policy(policy_or_source_id: Policy | str) -> str:
    """Build the source-sync User-Agent without inventing a contact identity."""
    contact = user_agent_contact(policy_or_source_id)
    if contact:
        return f"{USER_AGENT_PRODUCT} (+{contact})"
    return USER_AGENT_PRODUCT


def assert_live_prerequisites(policy_or_source_id: Policy | str) -> Policy:
    """
    Enforce live/acquire prerequisites.

    RC3 live source sync and document acquisition require PostgreSQL mode and an
    explicit operator-provided User-Agent contact when the source policy requires it.
    """
    policy = assert_enabled(policy_or_source_id)
    if get_mode() != "postgres":
        raise LivePrerequisiteError("REGLENS_MODE=postgres is required for live source sync")

    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not database_url:
        raise LivePrerequisiteError("DATABASE_URL is required for live source sync")

    user_agent_contact(policy)
    return policy
