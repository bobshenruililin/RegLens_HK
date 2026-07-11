from __future__ import annotations

import re
from typing import Any

from .. import PIPELINE_VERSION
from ..segment import PageSpan
from .base import LLMProvider


class EvidenceResolutionError(ValueError):
    """Raised when a quote cannot be located on the referenced page."""


class MockLLMProvider(LLMProvider):
    """
    Deterministic, offline extractor (Milestone 2A / v2).
    Emits client_ref only — never persistent UUIDs or publication status.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_version(self) -> str:
        return "mock-2.0.0"

    @property
    def prompt_version(self) -> str:
        return "mock-prompt-2.0.0"

    def extract(
        self,
        *,
        document_sha256: str,
        regulator_code: str,
        spans: list[PageSpan],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        joined = "\n".join(s.text for s in spans)
        page_for = {s.page_no: s for s in spans}
        counters: dict[str, int] = {}

        def next_ref(prop_type: str) -> str:
            counters[prop_type] = counters.get(prop_type, 0) + 1
            return f"{prop_type.replace('_', '-')}-{counters[prop_type]}"

        def quote_on(page_no: int, needle: str) -> dict[str, Any]:
            text = page_for[page_no].text
            idx = text.find(needle)
            if idx < 0:
                collapsed_page = " ".join(text.split())
                collapsed_needle = " ".join(needle.split())
                if collapsed_needle not in collapsed_page:
                    raise EvidenceResolutionError(
                        f"quote not found on page {page_no}: {needle[:80]!r}"
                    )
                # Offsets omitted when only collapsed match is available
                return {
                    "span_id": None,
                    "page_no": page_no,
                    "quote": needle[:2000],
                    "char_start": None,
                    "char_end": None,
                }
            return {
                "span_id": None,
                "page_no": page_no,
                "quote": needle[:2000],
                "char_start": idx,
                "char_end": idx + len(needle),
            }

        case_ref = metadata.get("case_ref") or _first_match(
            joined, r"(Case\s*(?:No\.?|Reference)\s*[:#]?\s*)([A-Z0-9][A-Z0-9/.\-]*)"
        )
        defendant = metadata.get("defendant_name_as_published") or _first_match(
            joined, r"(?:Defendant|Dr|Doctor)\s*[:\s]+([A-Z][A-Za-z .'-]{2,60})"
        )
        reg_no = metadata.get("defendant_registration_no") or _first_match(
            joined, r"(?:Reg(?:istration)?\.?\s*No\.?)\s*[:#]?\s*([A-Z0-9]+)"
        )
        judgment_date = metadata.get("decision_date") or _iso_date(joined)
        inquiry_date = _iso_date(joined)

        if regulator_code not in {"MCHK", "DCHK"}:
            raise ValueError(f"unknown regulator_code: {regulator_code}")
        profession = "dentist" if regulator_code == "DCHK" else "doctor"
        propositions: list[dict[str, Any]] = []
        relations: list[dict[str, Any]] = []
        charge_ref = None
        finding_ref = None
        sanction_ref = None
        rule_ref = None
        legal_ref = None
        authority_ref = None
        factor_ref = None

        charge = _section_line(joined, "Charge") or _first_match(
            joined, r"(?:amended\s+)?charge[:\s]+(.{20,240})", flags=re.I
        )
        if charge:
            page = _page_containing(spans, charge)
            if page is None:
                raise EvidenceResolutionError("charge text not located on any page")
            charge_ref = next_ref("charge")
            propositions.append(
                _prop(
                    charge_ref,
                    "charge",
                    "fact",
                    "normalized",
                    charge,
                    0.85,
                    [quote_on(page, charge[:180])],
                    structured={"charge_text": charge[:500]},
                )
            )

        rule = _first_match(
            joined,
            r"((?:Medical|Dentists?)\s+Registration\s+Ordinance[^\n.]{0,80}|"
            r"Code of Professional[^.\n]{0,80})",
            flags=re.I,
        )
        if rule:
            page = _page_containing(spans, rule)
            if page is None:
                raise EvidenceResolutionError("rule text not located")
            rule_ref = next_ref("rule")
            propositions.append(
                _prop(
                    rule_ref,
                    "rule",
                    "fact",
                    "verbatim",
                    rule,
                    0.8,
                    [quote_on(page, rule[:180])],
                    structured={"instrument": rule[:200]},
                )
            )

        finding = _section_line(joined, "Finding") or _first_match(
            joined,
            r"(guilty of misconduct[^\n.]{0,120}|charge is proved[^\n.]{0,80})",
            flags=re.I,
        )
        if finding:
            page = _page_containing(spans, finding)
            if page is None:
                raise EvidenceResolutionError("finding text not located")
            finding_ref = next_ref("finding")
            propositions.append(
                _prop(
                    finding_ref,
                    "finding",
                    "fact",
                    "normalized",
                    finding,
                    0.82,
                    [quote_on(page, finding[:180])],
                    structured={"outcome": "proved" if "proved" in finding.lower() else "stated"},
                )
            )

        sanction = _section_line(joined, "Order") or _first_match(
            joined,
            r"(removed from the (?:General Register|register)[^\n.]{0,100}|"
            r"warning letter[^\n.]{0,80})",
            flags=re.I,
        )
        if sanction:
            page = _page_containing(spans, sanction)
            if page is None:
                raise EvidenceResolutionError("sanction text not located")
            sanction_ref = next_ref("sanction")
            propositions.append(
                _prop(
                    sanction_ref,
                    "sanction",
                    "fact",
                    "normalized",
                    sanction,
                    0.84,
                    [quote_on(page, sanction[:180])],
                    structured={"order_text": sanction[:300]},
                )
            )

        mitigating = _first_match(
            joined,
            r"(clear disciplinary record|genuine remorse|admission of[^\n.]{0,60})",
            flags=re.I,
        )
        if mitigating:
            page = _page_containing(spans, mitigating)
            if page is None:
                raise EvidenceResolutionError("mitigating factor not located")
            factor_ref = next_ref("mitigating-factor")
            propositions.append(
                _prop(
                    factor_ref,
                    "mitigating_factor",
                    "fact",
                    "verbatim",
                    mitigating,
                    0.75,
                    [quote_on(page, mitigating[:180])],
                    structured={"polarity": "mitigating"},
                )
            )

        authority = _first_match(
            joined,
            r"(Dr\.?\s+[A-Z][a-z]+.?v\.?\s+The Medical Council[^\n.]{0,40})",
            flags=re.I,
        )
        if authority:
            page = _page_containing(spans, authority)
            if page is None:
                raise EvidenceResolutionError("authority not located")
            authority_ref = next_ref("authority")
            propositions.append(
                _prop(
                    authority_ref,
                    "authority",
                    "fact",
                    "verbatim",
                    authority,
                    0.7,
                    [quote_on(page, authority[:180])],
                    structured={"citation": authority[:200]},
                )
            )

        appeal = _first_match(joined, r"(no appeal|appeal (?:is|was)[^\n.]{0,80})", flags=re.I)
        if appeal:
            page = _page_containing(spans, appeal)
            if page is None:
                raise EvidenceResolutionError("appeal status not located")
            propositions.append(
                _prop(
                    next_ref("appeal-status"),
                    "appeal_status",
                    "fact",
                    "normalized",
                    appeal,
                    0.7,
                    [quote_on(page, appeal[:180])],
                    structured=None,
                )
            )

        legal_test = _first_match(
            joined,
            r"(conduct (?:which )?falls short of the standard expected[^\n.]{0,100})",
            flags=re.I,
        )
        if legal_test:
            page = _page_containing(spans, legal_test)
            if page is None:
                raise EvidenceResolutionError("legal test not located")
            legal_ref = next_ref("legal-test")
            propositions.append(
                _prop(
                    legal_ref,
                    "legal_test",
                    "interpretation",
                    "inferred",
                    legal_test,
                    0.65,
                    [quote_on(page, legal_test[:180])],
                    structured={"test_label": "standard_expected"},
                )
            )

        if finding_ref and charge_ref:
            relations.append(
                {
                    "relation_type": "finding_resolves_charge",
                    "from_ref": finding_ref,
                    "to_ref": charge_ref,
                }
            )
        if sanction_ref and charge_ref:
            relations.append(
                {
                    "relation_type": "sanction_applies_to_charge",
                    "from_ref": sanction_ref,
                    "to_ref": charge_ref,
                }
            )
        if rule_ref and charge_ref:
            relations.append(
                {
                    "relation_type": "rule_governs_charge",
                    "from_ref": rule_ref,
                    "to_ref": charge_ref,
                }
            )
        if authority_ref and legal_ref:
            relations.append(
                {
                    "relation_type": "authority_supports_legal_test",
                    "from_ref": authority_ref,
                    "to_ref": legal_ref,
                }
            )
        if factor_ref and sanction_ref:
            relations.append(
                {
                    "relation_type": "factor_affects_sanction",
                    "from_ref": factor_ref,
                    "to_ref": sanction_ref,
                }
            )

        missing = [
            field
            for field in ("charge", "finding", "sanction")
            if not any(p["prop_type"] == field for p in propositions)
        ]

        return {
            "schema_version": "2.0.0",
            "document_sha256": document_sha256,
            "extractor": {
                "pipeline_version": PIPELINE_VERSION,
                "model_provider": self.provider_name,
                "model_version": self.model_version,
                "prompt_version": self.prompt_version,
            },
            "decision_metadata": {
                "regulator_code": regulator_code,
                "profession": profession,
                "case_refs": [case_ref] if case_ref else [],
                "dates": {
                    "inquiry": inquiry_date,
                    "judgment": judgment_date,
                    "publication": None,
                    "conduct": None,
                    "order_effective": None,
                },
                "defendant_registration_no": reg_no,
                "defendant_name_as_published": defendant,
            },
            "propositions": propositions,
            "relations": relations,
            "coverage": {
                "missing_fields": missing,
                "warnings": ([] if propositions else ["no_propositions_extracted"]),
            },
        }


def _prop(
    client_ref: str,
    prop_type: str,
    epistemic_class: str,
    derivation: str,
    claim: str,
    confidence: float,
    evidence: list[dict[str, Any]],
    structured: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "client_ref": client_ref,
        "prop_type": prop_type,
        "epistemic_class": epistemic_class,
        "derivation": derivation,
        "claim_text": claim.strip()[:4000],
        "structured": structured,
        "confidence": confidence,
        "evidence": evidence,
    }


def _first_match(text: str, pattern: str, flags: int = 0) -> str | None:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    if m.lastindex:
        return m.group(m.lastindex).strip()
    return m.group(0).strip()


def _section_line(text: str, heading: str) -> str | None:
    m = re.search(rf"{heading}\s*[:.\-]\s*(.+)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None


def _iso_date(text: str) -> str | None:
    m = re.search(
        r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
        text,
        flags=re.I,
    )
    if not m:
        m2 = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
        return m2.group(0) if m2 else None
    months = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }
    day = int(m.group(1))
    month = months[m.group(2).lower()]
    year = m.group(3)
    return f"{year}-{month}-{day:02d}"


def _page_containing(spans: list[PageSpan], needle: str) -> int | None:
    for s in spans:
        if needle[:80] in s.text or needle in s.text:
            return s.page_no
    collapsed_needle = " ".join(needle.split()[:8])
    for s in spans:
        if collapsed_needle and collapsed_needle in " ".join(s.text.split()):
            return s.page_no
    return None
