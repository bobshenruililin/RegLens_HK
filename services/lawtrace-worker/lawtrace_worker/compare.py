"""Deterministic three-channel section comparison (Stage C)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any

from lawtrace_worker.canonical import (
    CANONICAL_FORMAT_VERSION,
    CanonicalSection,
    CanonToken,
    tokens_from_strings,
)

COMPARATOR_VERSION = "lawtrace-comparator/1.0.0"

SUPPORTED_RELATIONSHIPS = frozenset(
    {
        "unchanged",
        "text_changed",
        "status_changed",
        "text_and_status_changed",
        "added",
        "removed",
        "section_number_changed",
    }
)

UNSUPPORTED_OR_CANDIDATE = frozenset(
    {
        "split_candidate",
        "consolidation_candidate",
        "id_changed_unmatched",
        "ambiguous",
        "fuzzy_unsupported",
    }
)


@dataclass
class ChannelDiff:
    channel: str
    equal: bool
    opcodes: list[tuple[str, int, int, int, int]]
    operations: list[dict[str, Any]]
    a_hash: str
    b_hash: str


@dataclass
class SectionComparison:
    instrument: str
    version_a_id: str
    version_b_id: str
    section_id: str | None
    section_num_a: str | None
    section_num_b: str | None
    relationship: str
    relationship_supported: bool
    ordinary_redline_supported: bool
    limitation: str | None
    canonical_a: dict[str, Any]
    canonical_b: dict[str, Any]
    legal_text_diff: dict[str, Any]
    structural_diff: dict[str, Any]
    metadata_diff: dict[str, Any]
    full_token_diff: dict[str, Any]
    renderability_a: str
    renderability_b: str
    provenance_a: dict[str, Any]
    provenance_b: dict[str, Any]
    comparator_version: str
    normalization_version: str
    canonical_format_version: str
    reconstruction_ok: bool
    change_classifications: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def artifact_sha256(self) -> str:
        # Exclude non-deterministic fields if any; all fields here are deterministic.
        blob = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _hash_seq(seq: list[str]) -> str:
    blob = "\n".join(seq).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _opcodes_to_ops(
    opcodes: list[tuple[str, int, int, int, int]],
    a: list[str],
    b: list[str],
) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        ops.append(
            {
                "op": tag,
                "a_start": i1,
                "a_end": i2,
                "b_start": j1,
                "b_end": j2,
                "a_tokens": a[i1:i2],
                "b_tokens": b[j1:j2],
            }
        )
    return ops


def diff_sequences(a: list[str], b: list[str], *, channel: str) -> ChannelDiff:
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    opcodes = sm.get_opcodes()
    return ChannelDiff(
        channel=channel,
        equal=a == b,
        opcodes=opcodes,
        operations=_opcodes_to_ops(opcodes, a, b),
        a_hash=_hash_seq(a),
        b_hash=_hash_seq(b),
    )


def apply_opcodes(a: list[str], opcodes: list[tuple[str, int, int, int, int]], b: list[str]) -> list[str]:
    """Reconstruct B by applying SequenceMatcher opcodes to A.

    Uses B slices for insert/replace (the patch payload), proving the opcode
    stream is sufficient with B token material — standard reconstruction check:
    applying the recorded ops yields exactly B from A.
    """
    out: list[str] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            out.extend(a[i1:i2])
        elif tag == "delete":
            continue
        elif tag == "insert":
            out.extend(b[j1:j2])
        elif tag == "replace":
            out.extend(b[j1:j2])
        else:
            raise ValueError(f"unknown opcode {tag}")
    return out


def reconstruct_tokens(a_tokens: list[str], diff: ChannelDiff, b_tokens: list[str]) -> list[str]:
    return apply_opcodes(a_tokens, diff.opcodes, b_tokens)


def metadata_ops(a: dict[str, str | None], b: dict[str, str | None]) -> list[dict[str, Any]]:
    keys = sorted(set(a) | set(b))
    ops: list[dict[str, Any]] = []
    for k in keys:
        av, bv = a.get(k), b.get(k)
        if av != bv:
            ops.append({"field": k, "a": av, "b": bv})
    return ops


def _ordinary_redline_ok(rend_a: str, rend_b: str) -> tuple[bool, str | None]:
    blocked = {"potentially_lossy", "unsupported"}
    if rend_a in blocked or rend_b in blocked:
        return False, f"renderability_blocks_ordinary_redline:a={rend_a},b={rend_b}"
    if rend_a == "complete_with_nontext_metadata" or rend_b == "complete_with_nontext_metadata":
        return True, "complete_with_nontext_metadata_present"
    return True, None


def classify_relationship(
    *,
    text_equal: bool,
    structure_equal: bool,
    meta_ops: list[dict[str, Any]],
    num_a: str | None,
    num_b: str | None,
    same_id: bool,
) -> tuple[str, list[str]]:
    classifications: list[str] = []
    status_fields = {"status", "reason", "partial"}
    status_changed = any(op["field"] in status_fields for op in meta_ops)
    num_changed = (num_a or "") != (num_b or "")
    other_meta = [op for op in meta_ops if op["field"] not in status_fields and op["field"] != "section_num"]

    if not text_equal:
        classifications.append("legal_text_changed")
    if not structure_equal:
        classifications.append("structure_changed")
    if status_changed:
        classifications.append("status_metadata_changed")
    if num_changed and same_id:
        classifications.append("section_number_changed")
    if other_meta:
        classifications.append("other_metadata_changed")

    if text_equal and structure_equal and not meta_ops:
        return "unchanged", classifications or ["unchanged"]

    if same_id and num_changed and text_equal and not status_changed:
        # Pure renumber with stable @id
        return "section_number_changed", classifications

    if not text_equal and status_changed:
        return "text_and_status_changed", classifications
    if not text_equal:
        return "text_changed", classifications
    if status_changed and text_equal:
        return "status_changed", classifications
    if not structure_equal and text_equal:
        # Structural-only change still a supported comparison under text_changed? Plan lists
        # textually changed / status. Treat structure-only as text_changed channel aggregate
        # via legal_text false if structure markers are in full stream — structure_only label.
        return "text_changed", classifications
    if meta_ops and text_equal:
        # Any metadata-only delta (status, reason, start_period, etc.) is status/metadata —
        # never label it text_changed when legal text is identical.
        return "status_changed", classifications
    return "text_changed", classifications


def compare_sections(
    *,
    instrument: str,
    version_a_id: str,
    version_b_id: str,
    canon_a: CanonicalSection,
    canon_b: CanonicalSection,
    provenance_a: dict[str, Any],
    provenance_b: dict[str, Any],
) -> SectionComparison:
    a_full = canon_a.token_strings()
    b_full = canon_b.token_strings()
    a_text = canon_a.legal_text_tokens()
    b_text = canon_b.legal_text_tokens()
    a_struct = canon_a.structure_skeleton()
    b_struct = canon_b.structure_skeleton()
    meta_a = canon_a.metadata()
    meta_b = canon_b.metadata()

    full_diff = diff_sequences(a_full, b_full, channel="full_tokens")
    text_diff = diff_sequences(a_text, b_text, channel="legal_text")
    struct_diff = diff_sequences(a_struct, b_struct, channel="structure")
    m_ops = metadata_ops(meta_a, meta_b)
    meta_diff = {
        "channel": "metadata_status",
        "equal": not m_ops,
        "operations": m_ops,
        "a_hash": hashlib.sha256(
            json.dumps(meta_a, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "b_hash": hashlib.sha256(
            json.dumps(meta_b, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }

    reconstructed = reconstruct_tokens(a_full, full_diff, b_full)
    reconstruction_ok = reconstructed == b_full

    same_id = bool(canon_a.element_id) and canon_a.element_id == canon_b.element_id
    relationship, classifications = classify_relationship(
        text_equal=text_diff.equal and struct_diff.equal,
        structure_equal=struct_diff.equal,
        meta_ops=m_ops,
        num_a=canon_a.section_num,
        num_b=canon_b.section_num,
        same_id=same_id,
    )
    # Refine: text_equal for relationship should follow legal-text channel primarily;
    # structure-only still marks change.
    if text_diff.equal and struct_diff.equal and not m_ops:
        relationship = "unchanged"
    elif not text_diff.equal and any(op["field"] in {"status", "reason", "partial"} for op in m_ops):
        relationship = "text_and_status_changed"
    elif not text_diff.equal:
        relationship = "text_changed"
    elif any(op["field"] in {"status", "reason", "partial"} for op in m_ops) and text_diff.equal:
        relationship = "status_changed"
    elif same_id and (canon_a.section_num or "") != (canon_b.section_num or ""):
        relationship = "section_number_changed"
    elif not struct_diff.equal:
        relationship = "text_changed"
    elif m_ops and text_diff.equal:
        # Period / other metadata-only changes belong on the status/metadata channel.
        relationship = "status_changed"

    ordinary_ok, limitation = _ordinary_redline_ok(canon_a.renderability, canon_b.renderability)
    if not ordinary_ok:
        # Fail closed: comparison artifact retained, but not an ordinary complete redline.
        pass
    if canon_a.unsupported_structures or canon_b.unsupported_structures:
        ordinary_ok = False
        limitation = (
            (limitation + "; " if limitation else "")
            + "unsupported_structures_present"
        )

    return SectionComparison(
        instrument=instrument,
        version_a_id=version_a_id,
        version_b_id=version_b_id,
        section_id=canon_a.element_id or canon_b.element_id,
        section_num_a=canon_a.section_num,
        section_num_b=canon_b.section_num,
        relationship=relationship,
        relationship_supported=relationship in SUPPORTED_RELATIONSHIPS,
        ordinary_redline_supported=ordinary_ok and relationship in SUPPORTED_RELATIONSHIPS,
        limitation=limitation,
        canonical_a=canon_a.to_dict(),
        canonical_b=canon_b.to_dict(),
        legal_text_diff=asdict(text_diff),
        structural_diff=asdict(struct_diff),
        metadata_diff=meta_diff,
        full_token_diff=asdict(full_diff),
        renderability_a=canon_a.renderability,
        renderability_b=canon_b.renderability,
        provenance_a=provenance_a,
        provenance_b=provenance_b,
        comparator_version=COMPARATOR_VERSION,
        normalization_version=canon_a.normalization_version,
        canonical_format_version=CANONICAL_FORMAT_VERSION,
        reconstruction_ok=reconstruction_ok,
        change_classifications=classifications,
    )


def compare_added(
    *,
    instrument: str,
    version_a_id: str,
    version_b_id: str,
    canon_b: CanonicalSection,
    provenance_b: dict[str, Any],
) -> SectionComparison:
    empty = CanonicalSection(
        format_version=CANONICAL_FORMAT_VERSION,
        normalization_version=canon_b.normalization_version,
        parser_version=canon_b.parser_version,
        section_num=None,
        heading=None,
        element_id=None,
        temporal_id=None,
        status=None,
        reason=None,
        partial=None,
        start_period=None,
        end_period=None,
        renderability="complete",
        renderability_reasons=[],
        tokens=[],
    )
    cmp = compare_sections(
        instrument=instrument,
        version_a_id=version_a_id,
        version_b_id=version_b_id,
        canon_a=empty,
        canon_b=canon_b,
        provenance_a={"note": "no_prior_section"},
        provenance_b=provenance_b,
    )
    cmp.relationship = "added"
    cmp.relationship_supported = True
    cmp.reconstruction_ok = True  # trivial for add
    return cmp


def compare_removed(
    *,
    instrument: str,
    version_a_id: str,
    version_b_id: str,
    canon_a: CanonicalSection,
    provenance_a: dict[str, Any],
) -> SectionComparison:
    empty = CanonicalSection(
        format_version=CANONICAL_FORMAT_VERSION,
        normalization_version=canon_a.normalization_version,
        parser_version=canon_a.parser_version,
        section_num=None,
        heading=None,
        element_id=None,
        temporal_id=None,
        status=None,
        reason=None,
        partial=None,
        start_period=None,
        end_period=None,
        renderability="complete",
        renderability_reasons=[],
        tokens=[],
    )
    cmp = compare_sections(
        instrument=instrument,
        version_a_id=version_a_id,
        version_b_id=version_b_id,
        canon_a=canon_a,
        canon_b=empty,
        provenance_a=provenance_a,
        provenance_b={"note": "no_successor_section"},
    )
    cmp.relationship = "removed"
    cmp.relationship_supported = True
    cmp.reconstruction_ok = True
    return cmp


def highlight_ops(ops: list[dict[str, Any]], *, limit: int = 40) -> list[str]:
    lines: list[str] = []
    for op in ops[:limit]:
        tag = op["op"]
        if tag == "delete":
            for t in op["a_tokens"]:
                lines.append(f"- {t}")
        elif tag == "insert":
            for t in op["b_tokens"]:
                lines.append(f"+ {t}")
        elif tag == "replace":
            for t in op["a_tokens"]:
                lines.append(f"- {t}")
            for t in op["b_tokens"]:
                lines.append(f"+ {t}")
    if len(ops) > limit:
        lines.append(f"... ({len(ops) - limit} more ops truncated in viewer)")
    return lines


# Re-export helper for tests
__all__ = [
    "COMPARATOR_VERSION",
    "SectionComparison",
    "apply_opcodes",
    "compare_added",
    "compare_removed",
    "compare_sections",
    "diff_sequences",
    "highlight_ops",
    "reconstruct_tokens",
    "tokens_from_strings",
]
