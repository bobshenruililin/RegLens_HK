from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "packages"
    / "extraction-schema"
    / "extraction_result.v1.json"
)


def load_extraction_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_extraction(payload: dict[str, Any]) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    schema = load_extraction_schema()
    validator = Draft202012Validator(schema)
    return sorted({e.message for e in validator.iter_errors(payload)})


def assert_valid_extraction(payload: dict[str, Any]) -> None:
    errors = validate_extraction(payload)
    if errors:
        raise ValueError("Extraction schema validation failed:\n- " + "\n- ".join(errors))


def evidence_quotes_supported(
    payload: dict[str, Any],
    page_texts: dict[int, str],
    *,
    min_ratio: float = 0.9,
) -> list[str]:
    """
    Ensure each evidence quote appears in the corresponding page text.
    Uses exact substring match first; falls back to whitespace-collapsed containment.
    """
    failures: list[str] = []

    def collapse(s: str) -> str:
        return " ".join(s.split()).lower()

    for prop in payload.get("propositions", []):
        for ev in prop.get("evidence", []):
            page_no = ev["page_no"]
            quote = ev["quote"]
            page = page_texts.get(page_no, "")
            if quote in page:
                continue
            cq, cp = collapse(quote), collapse(page)
            if cq and cq in cp:
                continue
            # Soft path: require high character overlap for short OCR noise — still fail for M1.
            failures.append(
                f"proposition {prop.get('id')}: quote not found on page {page_no}"
            )
    return failures
