"""Policy-gated source discovery and acquisition for RegLens HK RC3."""

from __future__ import annotations

from .policy import (
    AcquisitionNotAllowedError,
    LivePrerequisiteError,
    PolicyError,
    PolicyValidationError,
    SourceDisabledError,
    assert_enabled,
    assert_live_prerequisites,
    assert_mode_allows_acquire,
    get_policy,
    load_policy_document,
)

__all__ = [
    "AcquisitionNotAllowedError",
    "LivePrerequisiteError",
    "PolicyError",
    "PolicyValidationError",
    "SourceDisabledError",
    "assert_enabled",
    "assert_live_prerequisites",
    "assert_mode_allows_acquire",
    "get_policy",
    "load_policy_document",
]
