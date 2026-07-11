"""Shared contract enums (Milestone 2A). Keep aligned with packages/contracts."""

from __future__ import annotations

REGULATOR_CODES = frozenset({"MCHK", "DCHK"})
PROFESSIONS = frozenset({"doctor", "dentist"})
PROP_TYPES = frozenset(
    {
        "charge",
        "rule",
        "finding",
        "legal_test",
        "aggravating_factor",
        "mitigating_factor",
        "sanction",
        "costs",
        "authority",
        "appeal_status",
    }
)
EPISTEMIC_CLASSES = frozenset({"fact", "interpretation"})
REVIEW_STATUSES = frozenset({"pending", "accepted", "edited", "rejected"})
JOB_TYPES = frozenset({"ingest_fixture", "segment", "extract", "index_fts"})
JOB_STATUSES = frozenset({"pending", "running", "succeeded", "failed", "cancelled"})

PUBLISHABLE_REVIEW = frozenset({"accepted", "edited"})


def can_publish_proposition(*, review_status: str, evidence: list) -> bool:
    if review_status not in PUBLISHABLE_REVIEW:
        return False
    return bool(evidence)
