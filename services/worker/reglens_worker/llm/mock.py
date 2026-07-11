from __future__ import annotations

import re
import uuid
from typing import Any

from .. import PIPELINE_VERSION
from ..segment import PageSpan
from .base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Deterministic, offline extractor for Milestone 1.
    Parses fixture HTML/PDF text heuristics only — no network calls.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_version(self) -> str:
        return "mock-1.0.0"

    @property
    def prompt_version(self) -> str:
        return "mock-prompt-1.0.0"

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

        def quote_on(page_no: int, needle: str) -> dict[str, Any]:
            text = page_for[page_no].text
            idx = text.find(needle)
            if idx < 0:
                # fall back to first non-empty line on that page
                needle = next((ln.strip() for ln in text.splitlines() if ln.strip()), text[:120])
                idx = text.find(needle)
            return {
                "span_id": None,
                "page_no": page_no,
                "quote": needle[:2000],
                "char_start": idx if idx >= 0 else None,
                "char_end": (idx + len(needle)) if idx >= 0 else None,
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
        decision_date = metadata.get("decision_date") or _iso_date(joined)

        profession = "dentist" if regulator_code == "DCHK" else "doctor"
        propositions: list[dict[str, Any]] = []

        charge = _section_line(joined, "Charge") or _first_match(
            joined, r"(?:amended\s+)?charge[:\s]+(.{20,240})", flags=re.I
        )
        if charge:
            page = _page_containing(spans, charge) or 1
            propositions.append(
                _prop("charge", "fact", charge, 0.85, [quote_on(page, charge[:180])])
            )

        rule = _first_match(
            joined,
            r"((?:Medical|Dentists?)\s+Registration\s+Ordinance[^\n.]{0,80}|Code of Professional[^.\n]{0,80})",
            flags=re.I,
        )
        if rule:
            page = _page_containing(spans, rule) or 1
            propositions.append(
                _prop("rule", "fact", rule, 0.8, [quote_on(page, rule[:180])])
            )

        finding = _section_line(joined, "Finding") or _first_match(
            joined, r"(guilty of misconduct[^\n.]{0,120}|charge is proved[^\n.]{0,80})", flags=re.I
        )
        if finding:
            page = _page_containing(spans, finding) or 1
            propositions.append(
                _prop("finding", "fact", finding, 0.82, [quote_on(page, finding[:180])])
            )

        sanction = _section_line(joined, "Order") or _first_match(
            joined,
            r"(removed from the (?:General Register|register)[^\n.]{0,100}|warning letter[^\n.]{0,80})",
            flags=re.I,
        )
        if sanction:
            page = _page_containing(spans, sanction) or 1
            propositions.append(
                _prop("sanction", "fact", sanction, 0.84, [quote_on(page, sanction[:180])])
            )

        mitigating = _first_match(
            joined, r"(clear disciplinary record|genuine remorse|admission of[^\n.]{0,60})", flags=re.I
        )
        if mitigating:
            page = _page_containing(spans, mitigating) or 1
            propositions.append(
                _prop(
                    "mitigating_factor",
                    "fact",
                    mitigating,
                    0.75,
                    [quote_on(page, mitigating[:180])],
                )
            )

        authority = _first_match(
            joined, r"(Dr\.?\s+[A-Z][a-z]+.?v\.?\s+The Medical Council[^\n.]{0,40})", flags=re.I
        )
        if authority:
            page = _page_containing(spans, authority) or 1
            propositions.append(
                _prop("authority", "fact", authority, 0.7, [quote_on(page, authority[:180])])
            )

        appeal = _first_match(joined, r"(no appeal|appeal (?:is|was)[^\n.]{0,80})", flags=re.I)
        if appeal:
            page = _page_containing(spans, appeal) or 1
            propositions.append(
                _prop("appeal_status", "fact", appeal, 0.7, [quote_on(page, appeal[:180])])
            )

        # Optional interpretive legal test only when fixture states a standard explicitly.
        legal_test = _first_match(
            joined,
            r"(conduct (?:which )?falls short of the standard expected[^\n.]{0,100})",
            flags=re.I,
        )
        if legal_test:
            page = _page_containing(spans, legal_test) or 1
            propositions.append(
                _prop(
                    "legal_test",
                    "interpretation",
                    legal_test,
                    0.65,
                    [quote_on(page, legal_test[:180])],
                )
            )

        missing = []
        for field in ("charge", "finding", "sanction"):
            if not any(p["prop_type"] == field for p in propositions):
                missing.append(field)

        return {
            "schema_version": "1.0.0",
            "document_sha256": document_sha256,
            "extractor": {
                "pipeline_version": PIPELINE_VERSION,
                "model_provider": self.provider_name,
                "model_version": self.model_version,
                "prompt_version": self.prompt_version,
            },
            "decision_metadata": {
                "case_ref": case_ref,
                "decision_date": decision_date,
                "regulator_code": regulator_code if regulator_code in {"MCHK", "DCHK"} else "MCHK",
                "profession": profession,
                "defendant_registration_no": reg_no,
                "defendant_name_as_published": defendant,
            },
            "propositions": propositions,
            "coverage": {
                "missing_fields": missing,
                "warnings": ([] if propositions else ["no_propositions_extracted"]),
            },
        }


def _prop(
    prop_type: str,
    epistemic_class: str,
    claim: str,
    confidence: float,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "prop_type": prop_type,
        "epistemic_class": epistemic_class,
        "claim_text": claim.strip()[:4000],
        "structured": None,
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
    m = re.search(
        rf"{heading}\s*[:.\-]\s*(.+)",
        text,
        flags=re.IGNORECASE,
    )
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
    # softer
    collapsed_needle = " ".join(needle.split()[:8])
    for s in spans:
        if collapsed_needle and collapsed_needle in " ".join(s.text.split()):
            return s.page_no
    return spans[0].page_no if spans else None
