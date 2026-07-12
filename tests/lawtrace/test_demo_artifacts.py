"""Integration checks for committed LawTrace demo web artifacts."""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path("apps/lawtrace/public/data")


def test_committed_demo_manifest_is_demo_mode() -> None:
    root = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    assert root["dataset_mode"] == "demo"
    by_slug = {i["slug"]: i for i in root["instruments"]}
    assert by_slug["cap-614"]["available"] is True
    assert by_slug["cap-599g"]["available"] is False
    assert "missing_reason" in by_slug["cap-599g"]


def test_cap614_reconstruction_and_provenance() -> None:
    man = json.loads((DATA / "instruments/cap-614/manifest.json").read_text(encoding="utf-8"))
    assert man["reconstruction"]["rate"] == 1.0
    assert man["version_count"] == 12
    transitions = json.loads(
        (DATA / "instruments/cap-614/transitions.json").read_text(encoding="utf-8")
    )["transitions"]
    assert transitions
    sample = None
    for t in transitions:
        payload = json.loads(
            (DATA / "instruments/cap-614/transitions" / f"{t['transition_id']}.json").read_text(
                encoding="utf-8"
            )
        )
        for item in payload["items"]:
            if item["relationship"] in {
                "text_changed",
                "status_changed",
                "text_and_status_changed",
            }:
                sample = item
                break
        if sample:
            break
    assert sample is not None
    assert sample["provenance_a"]["source_file_sha256"]
    assert sample["provenance_b"]["source_file_sha256"]
    assert sample["comparator_version"]
    assert sample["reconstruction_ok"] is True


def test_insights_reconcile_with_transition_counts() -> None:
    insights = json.loads((DATA / "instruments/cap-614/insights.json").read_text(encoding="utf-8"))
    transitions = json.loads(
        (DATA / "instruments/cap-614/transitions.json").read_text(encoding="utf-8")
    )["transitions"]
    assert len(insights["transitions"]) == len(transitions)
    for a, b in zip(insights["transitions"], transitions, strict=True):
        assert a["changed_count"] == b["changed_count"]
    assert "token_flow" in insights
    assert "textual_vs_status" in insights


def test_no_raw_zip_in_public_data() -> None:
    zips = list(DATA.rglob("*.zip"))
    xmls = [p for p in DATA.rglob("*.xml") if "cap-599g" in str(p) or "bulk" in str(p).lower()]
    assert zips == []
    assert xmls == []
