"""JSON Schema + domain invariant validation for extraction v2."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .segment import PageSpan

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "packages" / "extraction-schema"
SCHEMA_V2_PATH = SCHEMA_DIR / "extraction_result.v2.json"
SCHEMA_V1_PATH = SCHEMA_DIR / "extraction_result.v1.json"

ALLOWED_REGULATORS = frozenset({"MCHK", "DCHK"})
FORMAT_CHECKER = FormatChecker()


@FORMAT_CHECKER.checks("date", raises=ValueError)
def _check_date(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    date.fromisoformat(value)
    return True


def load_schema(version: str = "2.0.0") -> dict[str, Any]:
    path = SCHEMA_V2_PATH if version.startswith("2") else SCHEMA_V1_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def validate_extraction_schema(payload: dict[str, Any], *, version: str = "2.0.0") -> list[str]:
    schema = load_schema(version)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    return sorted({e.message for e in validator.iter_errors(payload)})


def collapse_ws(s: str) -> str:
    return " ".join(s.split()).lower()


def domain_validate_extraction(
    payload: dict[str, Any],
    *,
    spans: list[PageSpan],
    document_sha256: str,
    require_span_id: bool = True,
) -> list[str]:
    """Return invariant violations (empty if ok)."""
    errors: list[str] = []

    if payload.get("document_sha256") != document_sha256:
        errors.append("document_sha256 does not match current document")

    meta = payload.get("decision_metadata") or {}
    reg = meta.get("regulator_code")
    if reg not in ALLOWED_REGULATORS:
        errors.append(f"unknown regulator_code: {reg!r}")

    dates = meta.get("dates") or {}
    for key, val in dates.items():
        if val is None:
            continue
        try:
            date.fromisoformat(val)
        except Exception:
            errors.append(f"invalid date for dates.{key}: {val!r}")

    props = payload.get("propositions") or []
    if not props:
        errors.append("empty decision: no propositions (quarantine required)")

    refs = [p.get("client_ref") for p in props]
    if len(refs) != len(set(refs)):
        errors.append("duplicate client_ref values within extraction")

    span_by_page = {s.page_no: s for s in spans}
    span_by_id = {}
    # span_id filled by application before domain check when require_span_id

    for prop in props:
        cref = prop.get("client_ref")
        for ev in prop.get("evidence") or []:
            page_no = ev.get("page_no")
            quote = ev.get("quote") or ""
            span_id = ev.get("span_id")
            if require_span_id and not span_id:
                errors.append(f"{cref}: evidence missing span_id after resolution")
            span = span_by_page.get(page_no)
            if span is None:
                errors.append(f"{cref}: evidence page_no {page_no} not in document spans")
                continue
            if span_id:
                span_by_id[span_id] = span
            if quote not in span.text and collapse_ws(quote) not in collapse_ws(span.text):
                errors.append(f"{cref}: quote not found on page {page_no}")
            cs, ce = ev.get("char_start"), ev.get("char_end")
            if (cs is None) ^ (ce is None):
                errors.append(f"{cref}: char_start/char_end must both be set or both null")
            elif cs is not None and ce is not None:
                if ce < cs:
                    errors.append(f"{cref}: char_end < char_start")
                elif cs < 0 or ce > len(span.text):
                    errors.append(f"{cref}: character offsets out of bounds")
                else:
                    sliced = span.text[cs:ce]
                    if collapse_ws(sliced) != collapse_ws(quote):
                        errors.append(f"{cref}: sliced span text does not match quote at offsets")

    ref_set = set(refs)
    for rel in payload.get("relations") or []:
        fr, to = rel.get("from_ref"), rel.get("to_ref")
        if fr not in ref_set or to not in ref_set:
            errors.append(f"relation endpoint missing client_ref: {fr!r} -> {to!r}")

    return errors


def assert_valid_extraction_v2(
    payload: dict[str, Any],
    *,
    spans: list[PageSpan],
    document_sha256: str,
    require_span_id: bool = True,
) -> None:
    schema_errors = validate_extraction_schema(payload, version="2.0.0")
    domain_errors = domain_validate_extraction(
        payload,
        spans=spans,
        document_sha256=document_sha256,
        require_span_id=require_span_id,
    )
    errors = schema_errors + domain_errors
    if errors:
        raise ValueError("Extraction validation failed:\n- " + "\n- ".join(errors))


# Back-compat aliases used by older tests
def validate_extraction(payload: dict[str, Any]) -> list[str]:
    version = str(payload.get("schema_version", "2.0.0"))
    if version.startswith("1"):
        return validate_extraction_schema(payload, version="1.0.0")
    return validate_extraction_schema(payload, version="2.0.0")


def assert_valid_extraction(payload: dict[str, Any]) -> None:
    errors = validate_extraction(payload)
    if errors:
        raise ValueError("Extraction schema validation failed:\n- " + "\n- ".join(errors))


def evidence_quotes_supported(
    payload: dict[str, Any],
    page_texts: dict[int, str],
) -> list[str]:
    failures: list[str] = []
    for prop in payload.get("propositions", []):
        label = prop.get("client_ref") or prop.get("id")
        for ev in prop.get("evidence", []):
            page_no = ev["page_no"]
            quote = ev["quote"]
            page = page_texts.get(page_no, "")
            if quote in page or collapse_ws(quote) in collapse_ws(page):
                continue
            failures.append(f"proposition {label}: quote not found on page {page_no}")
    return failures


def migrate_v1_to_v2(payload: dict[str, Any]) -> dict[str, Any]:
    """Best-effort structural migration for legacy fixtures (not for production publish)."""
    if payload.get("schema_version") == "2.0.0":
        return payload
    meta = payload.get("decision_metadata") or {}
    case_ref = meta.get("case_ref")
    decision_date = meta.get("decision_date")
    propositions = []
    for i, prop in enumerate(payload.get("propositions") or [], start=1):
        cref = f"{prop.get('prop_type', 'prop')}-{i}"
        propositions.append(
            {
                "client_ref": cref.replace("_", "-")[:128].lower()
                if False
                else f"{prop['prop_type'].replace('_', '-')}-{i}",
                "prop_type": prop["prop_type"],
                "epistemic_class": prop["epistemic_class"],
                "derivation": "normalized",
                "claim_text": prop["claim_text"],
                "structured": prop.get("structured"),
                "confidence": prop["confidence"],
                "evidence": prop["evidence"],
            }
        )
    return {
        "schema_version": "2.0.0",
        "document_sha256": payload["document_sha256"],
        "extractor": payload["extractor"],
        "decision_metadata": {
            "regulator_code": meta.get("regulator_code") or "MCHK",
            "profession": meta.get("profession") or "doctor",
            "case_refs": [case_ref] if case_ref else [],
            "dates": {
                "inquiry": None,
                "judgment": decision_date,
                "publication": None,
                "conduct": None,
                "order_effective": None,
            },
            "defendant_registration_no": meta.get("defendant_registration_no"),
            "defendant_name_as_published": meta.get("defendant_name_as_published"),
        },
        "propositions": propositions,
        "relations": [],
        "coverage": payload.get("coverage")
        or {"missing_fields": [], "warnings": ["migrated_from_v1"]},
    }
