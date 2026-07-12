"""Deterministic canonical section representation (Stage C).

Preserves top-level section structure and text-bearing content without
assigning independent temporal identity to nested subsections/paragraphs.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any
from xml.etree.ElementTree import Element

from lawtrace_worker import NORMALIZATION_VERSION, PARSER_VERSION
from lawtrace_worker.security.xml_safe import local_name
from lawtrace_worker.stage_b import classify_renderability

CANONICAL_FORMAT_VERSION = "lawtrace-canonical/1.0.0"

# Tags skipped from the operative token stream (recorded as skipped_tags).
_SKIP_TAGS = frozenset({"editorialNote"})

# Structural containers that emit open/close markers.
_CONTAINER_TAGS = frozenset(
    {
        "subsection",
        "paragraph",
        "subparagraph",
        "def",
        "amendingFormula",
        "quotedStructure",
        "quotedText",
        "action",
        "continued",
    }
)

# Leaf-ish text carriers emitted as typed content tokens.
_TEXT_TAGS = frozenset(
    {
        "num",
        "heading",
        "leadIn",
        "content",
        "term",
        "text",
        "shortTitle",
        "b",
        "i",
        "inline",
        "ref",
        "sup",
        "sub",
        "marker",
        "sourceNote",
    }
)


def _nfc(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _ws(s: str) -> str:
    """Collapse horizontal whitespace only; preserve newlines."""
    return re.sub(r"[ \t]+", " ", s)


@dataclass(frozen=True)
class CanonToken:
    kind: str
    text: str = ""

    def serialize(self) -> str:
        # Deterministic single-line encoding for hashing/diff.
        safe = self.text.replace("\\", "\\\\").replace("\n", "\\n")
        return f"{self.kind}|{safe}"


@dataclass
class CanonicalSection:
    format_version: str
    normalization_version: str
    parser_version: str
    section_num: str | None
    heading: str | None
    element_id: str | None
    temporal_id: str | None
    status: str | None
    reason: str | None
    partial: str | None
    start_period: str | None
    end_period: str | None
    renderability: str
    renderability_reasons: list[str]
    tokens: list[CanonToken]
    skipped_tags: list[str] = field(default_factory=list)
    unsupported_structures: list[str] = field(default_factory=list)

    def token_strings(self) -> list[str]:
        return [t.serialize() for t in self.tokens]

    def structure_skeleton(self) -> list[str]:
        return [t.kind for t in self.tokens if t.kind.endswith("_OPEN") or t.kind.endswith("_CLOSE") or t.kind in {"SECTION_OPEN", "SECTION_CLOSE"}]

    def legal_text_tokens(self) -> list[str]:
        text_kinds = {
            "NUM",
            "HEADING",
            "LEADIN",
            "CONTENT",
            "TERM",
            "TEXT",
            "SHORTTITLE",
            "B",
            "I",
            "INLINE",
            "REF",
            "SUP",
            "SUB",
            "MARKER",
            "SOURCENOTE",
        }
        return [t.serialize() for t in self.tokens if t.kind in text_kinds]

    def metadata(self) -> dict[str, str | None]:
        return {
            "section_num": self.section_num,
            "heading": self.heading,
            "element_id": self.element_id,
            "temporal_id": self.temporal_id,
            "status": self.status,
            "reason": self.reason,
            "partial": self.partial,
            "start_period": self.start_period,
            "end_period": self.end_period,
        }

    def sha256(self) -> str:
        payload = {
            "format_version": self.format_version,
            "normalization_version": self.normalization_version,
            "tokens": self.token_strings(),
            "metadata": self.metadata(),
            "renderability": self.renderability,
            "skipped_tags": self.skipped_tags,
            "unsupported_structures": self.unsupported_structures,
        }
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tokens"] = [{"kind": t.kind, "text": t.text} for t in self.tokens]
        d["canonical_sha256"] = self.sha256()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CanonicalSection:
        tokens = [CanonToken(kind=t["kind"], text=t.get("text", "")) for t in d["tokens"]]
        return cls(
            format_version=d["format_version"],
            normalization_version=d["normalization_version"],
            parser_version=d["parser_version"],
            section_num=d.get("section_num"),
            heading=d.get("heading"),
            element_id=d.get("element_id"),
            temporal_id=d.get("temporal_id"),
            status=d.get("status"),
            reason=d.get("reason"),
            partial=d.get("partial"),
            start_period=d.get("start_period"),
            end_period=d.get("end_period"),
            renderability=d["renderability"],
            renderability_reasons=list(d.get("renderability_reasons") or []),
            tokens=tokens,
            skipped_tags=list(d.get("skipped_tags") or []),
            unsupported_structures=list(d.get("unsupported_structures") or []),
        )


def _child_text(el: Element, name: str) -> str | None:
    for c in el:
        if local_name(c.tag) == name:
            t = _nfc(_ws("".join(c.itertext()).strip()))
            return t or None
    return None


def _emit_text_nodes(el: Element, tokens: list[CanonToken], skipped: list[str]) -> None:
    """Emit direct text + children of a mixed-content element in document order."""
    if el.text and el.text.strip():
        tokens.append(CanonToken("CONTENT", _nfc(_ws(el.text.strip()))))
    for child in el:
        _walk(child, tokens, skipped)
        if child.tail and child.tail.strip():
            tokens.append(CanonToken("CONTENT", _nfc(_ws(child.tail.strip()))))


def _walk(el: Element, tokens: list[CanonToken], skipped: list[str]) -> None:
    ln = local_name(el.tag)
    if ln in _SKIP_TAGS:
        skipped.append(ln)
        return

    if ln in _CONTAINER_TAGS:
        tokens.append(CanonToken(f"{ln.upper()}_OPEN", ""))
        # Prefer structured children; also capture leading text.
        if el.text and el.text.strip():
            tokens.append(CanonToken("CONTENT", _nfc(_ws(el.text.strip()))))
        for child in el:
            _walk(child, tokens, skipped)
            if child.tail and child.tail.strip():
                tokens.append(CanonToken("CONTENT", _nfc(_ws(child.tail.strip()))))
        tokens.append(CanonToken(f"{ln.upper()}_CLOSE", ""))
        return

    if ln in _TEXT_TAGS:
        kind = ln.upper()
        # For ref/sup/sub/b/i/inline keep nested text flattened into the token
        # while still walking children if they introduce structure.
        if list(el) and any(local_name(c.tag) in _CONTAINER_TAGS for c in el):
            tokens.append(CanonToken(f"{kind}_OPEN", ""))
            _emit_text_nodes(el, tokens, skipped)
            tokens.append(CanonToken(f"{kind}_CLOSE", ""))
        else:
            text = _nfc(_ws("".join(el.itertext()).strip()))
            tokens.append(CanonToken(kind, text))
        return

    # Unknown / other tags: fail-closed recording + best-effort child walk.
    if ln not in {"section"}:
        tokens.append(CanonToken("UNKNOWN_OPEN", ln))
    if el.text and el.text.strip():
        tokens.append(CanonToken("CONTENT", _nfc(_ws(el.text.strip()))))
    for child in el:
        _walk(child, tokens, skipped)
        if child.tail and child.tail.strip():
            tokens.append(CanonToken("CONTENT", _nfc(_ws(child.tail.strip()))))
    if ln not in {"section"}:
        tokens.append(CanonToken("UNKNOWN_CLOSE", ln))


def canonicalize_section(elem: Element) -> CanonicalSection:
    if local_name(elem.tag) != "section":
        raise ValueError(f"expected section element, got {local_name(elem.tag)}")

    rend, reasons = classify_renderability(elem)
    unsupported: list[str] = []
    for el in elem.iter():
        ln = local_name(el.tag)
        if ln in {"img", "fillIn", "checkBox"}:
            unsupported.append(ln)
        if ln in {"layout", "header", "row", "column"}:
            unsupported.append(f"table_or_layout:{ln}")

    tokens: list[CanonToken] = [CanonToken("SECTION_OPEN", "")]
    skipped: list[str] = []
    if elem.text and elem.text.strip():
        tokens.append(CanonToken("CONTENT", _nfc(_ws(elem.text.strip()))))
    for child in elem:
        _walk(child, tokens, skipped)
        if child.tail and child.tail.strip():
            tokens.append(CanonToken("CONTENT", _nfc(_ws(child.tail.strip()))))
    tokens.append(CanonToken("SECTION_CLOSE", ""))

    return CanonicalSection(
        format_version=CANONICAL_FORMAT_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        parser_version=PARSER_VERSION,
        section_num=_child_text(elem, "num"),
        heading=_child_text(elem, "heading"),
        element_id=elem.attrib.get("id"),
        temporal_id=elem.attrib.get("temporalId"),
        status=elem.attrib.get("status"),
        reason=elem.attrib.get("reason"),
        partial=elem.attrib.get("partial"),
        start_period=elem.attrib.get("startPeriod"),
        end_period=elem.attrib.get("endPeriod"),
        renderability=rend,
        renderability_reasons=list(reasons),
        tokens=tokens,
        skipped_tags=sorted(set(skipped)),
        unsupported_structures=sorted(set(unsupported)),
    )


def tokens_from_strings(rows: list[str]) -> list[CanonToken]:
    out: list[CanonToken] = []
    for row in rows:
        kind, _, rest = row.partition("|")
        text = rest.replace("\\n", "\n").replace("\\\\", "\\")
        out.append(CanonToken(kind=kind, text=text))
    return out
