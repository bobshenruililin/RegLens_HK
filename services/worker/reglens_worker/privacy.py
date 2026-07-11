"""Private-data boundary helpers for derived and public fields.

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
    re.compile(r"\bPatient\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"),
]

_CONTACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+?852[-\s]?)?(?:[2-9]\d{3})[-\s]?\d{4}\b"),
    re.compile(r"\b[A-Z]\d{6}\(?\d\)?\b"),  # HKID-like
    re.compile(
        r"\b\d{1,4}\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+"
        r"(?:Road|Street|Avenue|Lane|Path|Drive|Court)\b",
        re.I,
    ),
]

_REDACTION = "[REDACTED_PERSON]"
_CONTACT_REDACTION = "[REDACTED_CONTACT]"


def redact_derived_text(text: str) -> str:
    """Redact likely patient/third-party and contact identifiers from derived text."""
    if not text:
        return text
    out = text
    for pat in _PATIENT_PATTERNS:
        out = pat.sub(_REDACTION, out)
    for pat in _CONTACT_PATTERNS:
        out = pat.sub(_CONTACT_REDACTION, out)
    out = re.sub(r"(?:\[REDACTED_PERSON\]\s*)+", f"{_REDACTION} ", out)
    out = re.sub(r"(?:\[REDACTED_CONTACT\]\s*)+", f"{_CONTACT_REDACTION} ", out)
    return out.strip()


def public_evidence_excerpt(quote: str, *, max_chars: int = 280) -> str:
    """Build a redacted public excerpt from an internal evidence quote."""
    redacted = redact_derived_text(quote)
    if len(redacted) <= max_chars:
        return redacted
    return redacted[: max_chars - 1].rstrip() + "…"


def find_privacy_warnings(text: str) -> list[str]:
    """Return blocking privacy warning codes for public release scanning."""
    warnings: list[str] = []
    if re.search(r"\bPatient\s+[A-Z0-9]\b", text, re.I):
        warnings.append("patient_token")
    if re.search(r"\b(?:Madam|Mr|Mrs|Ms|Miss)\s+[Xx]{2,}\b", text):
        warnings.append("masked_person_label")
    if re.search(r"\bPatient\s+[A-Z][a-z]+", text):
        warnings.append("patient_named")
    if re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.I):
        warnings.append("email")
    if re.search(r"\b(?:\+?852[-\s]?)?(?:[2-9]\d{3})[-\s]?\d{4}\b", text):
        warnings.append("phone_like")
    if re.search(
        r"\b\d{1,4}\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s+"
        r"(?:Road|Street|Avenue|Lane|Path|Drive|Court)\b",
        text,
        re.I,
    ):
        warnings.append("address_like")
    return warnings


def assert_no_obvious_patient_leak(text: str) -> None:
    """Raise if obvious patient/contact tokens remain (tests / publish checks)."""
    leaks = find_privacy_warnings(text)
    if leaks:
        raise ValueError(f"Derived text may leak identifiers ({', '.join(leaks)}): {text!r}")
