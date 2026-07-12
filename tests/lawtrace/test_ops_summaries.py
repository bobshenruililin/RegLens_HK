"""Unit tests for human-readable LawTrace op summaries (mirrors lib/ops.ts)."""

from __future__ import annotations


def _join(tokens: list[str] | None) -> str:
    if not tokens:
        return ""
    out = []
    for t in tokens:
        for prefix in ("CONTENT|", "LEADIN|", "HEADING|", "NUM|", "STATUS|", "ATTR|"):
            if t.startswith(prefix):
                t = t[len(prefix) :]
                break
        out.append(t)
    return " ".join(out).replace("  ", " ").strip()


def summarize_metadata(ops: list[dict]) -> list[str]:
    if not ops:
        return ["No metadata/status token changes in this transition."]
    lines = []
    for op in ops:
        a, b = _join(op.get("a_tokens")), _join(op.get("b_tokens"))
        if op.get("op") == "replace" and (a or b):
            if a and b:
                lines.append(f"Status/metadata changed from “{a}” to “{b}”.")
            elif b:
                lines.append(f"Status/metadata became “{b}”.")
            else:
                lines.append(f"Status/metadata “{a}” was removed.")
        elif op.get("op") == "insert" and b:
            lines.append(f"Status/metadata added: “{b}”.")
        elif op.get("op") == "delete" and a:
            lines.append(f"Status/metadata removed: “{a}”.")
        else:
            lines.append(f"Metadata operation: {op.get('op') or 'change'}.")
    return lines


def test_status_only_summary_is_human_readable() -> None:
    lines = summarize_metadata(
        [
            {
                "op": "replace",
                "a_tokens": ["STATUS|in_operation"],
                "b_tokens": ["STATUS|omitted"],
            }
        ]
    )
    assert "Status/metadata changed from" in lines[0]
    assert "in_operation" in lines[0]
    assert "omitted" in lines[0]
    assert "{" not in lines[0]


def test_empty_metadata_has_clear_message() -> None:
    assert "No metadata" in summarize_metadata([])[0]
