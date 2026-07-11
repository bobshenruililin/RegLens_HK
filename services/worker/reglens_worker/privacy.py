"""Private-data boundary helpers for derived fields (Milestone 2A).

Practitioner names in published judgments may remain. Patient / complainant
identifiers and unnecessary personal details are suppressed in derived text.
Does not claim full de-identification of raw source spans.
"""

from __future__ import annotations

import re

# Patterns commonly used in HK disciplinary judgments for patients / third parties.
_PATIENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bPatient\s+[A-Z0-9]\b", re.I),
    re.compile(r"\b(?:Madam|Mr|Mrs|Ms|Miss)\s+[Xx]{2,}\b"),
    re.compile(r"\b(?:Madam|Mr|Mrs|Ms|Miss)\s+[A-Z]\b"),
    re.compile(r"\bthe Patient\b", re.I),
    re.compile(r"\bcomplainant\b", re.I),
    # Explicit names after Patient label (conservative)
    re.compile(r"\bPatient\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"),
]

_REDACTION = "[REDACTED_PERSON]"


def redact_derived_text(text: str) -> str:
    """Redact likely patient/third-party references from derived claim text."""
    if not text:
        return text
    out = text
    for pat in _PATIENT_PATTERNS:
        out = pat.sub(_REDACTION, out)
    # Collapse duplicate redaction tokens (escape so [] are literal, not a char class)
    out = re.sub(
        r"(?:\[REDACTED_PERSON\]\s*)+",
        f"{_REDACTION} ",
        out,
    ).strip()
    return out


def assert_no_obvious_patient_leak(text: str) -> None:
    """Raise if obvious patient tokens remain (used in tests / publish checks)."""
    checks = [
        re.compile(r"\bPatient\s+[A-Z0-9]\b", re.I),
        re.compile(r"\b(?:Madam|Mr|Mrs|Ms)\s+[Xx]{2,}\b"),
    ]
    for pat in checks:
        if pat.search(text):
            raise ValueError(f"Derived text may leak patient identifier: {text!r}")
