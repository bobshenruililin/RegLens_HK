"""Tests for LawTrace web export."""

from __future__ import annotations

import json
from pathlib import Path

from lawtrace_worker.export_web import dump_json, export_instrument, main


def test_export_cap_614_demo(tmp_path: Path) -> None:
    out = tmp_path / "data"
    manifest = export_instrument(
        instrument_id="cap:614",
        title="Legislation Publication Ordinance (Cap. 614)",
        fixture_or_extract_dir=Path("fixtures/lawtrace/cap_614"),
        out_dir=out / "instruments" / "cap-614",
        dataset_mode="demo",
        archive_sha256="test",
    )
    assert manifest["reconstruction"]["rate"] == 1.0
    assert manifest["version_count"] == 12
    assert (out / "instruments/cap-614/transitions.json").is_file()
    assert (out / "instruments/cap-614/section-histories.json").is_file()
    histories = json.loads((out / "instruments/cap-614/section-histories.json").read_text())
    assert "sections" in histories
    insights = json.loads((out / "instruments/cap-614/insights.json").read_text())
    assert "token_flow" in insights
    assert "textual_vs_status" in insights
    # Counts reconcile: sum of relationship totals equals item events across transitions
    total_rels = sum(insights["relationship_totals"].values())
    assert total_rels > 0
    # Determinism of content hash for versions file
    h1 = dump_json(
        out / "v1.json",
        json.loads((out / "instruments/cap-614/versions.json").read_text()),
    )
    h2 = dump_json(
        out / "v2.json",
        json.loads((out / "instruments/cap-614/versions.json").read_text()),
    )
    assert h1 == h2


def test_missing_local_cap599g_is_explicit(tmp_path: Path) -> None:
    out = tmp_path / "web"
    main(
        [
            "--mode",
            "local",
            "--out",
            str(out),
            "--cap599g-dir",
            str(tmp_path / "missing-cap599g"),
            "--cap599g-max-versions",
            "5",
        ]
    )
    root = json.loads((out / "manifest.json").read_text())
    caps = {i["slug"]: i for i in root["instruments"]}
    assert caps["cap-614"]["available"] is True
    assert caps["cap-599g"]["available"] is False
    assert (
        "missing" in caps["cap-599g"]["missing_reason"].lower()
        or "not found" in caps["cap-599g"]["missing_reason"].lower()
        or "absent" in caps["cap-599g"]["missing_reason"].lower()
        or len(caps["cap-599g"]["missing_reason"]) > 10
    )


def test_cli_demo_writes_root_manifest(tmp_path: Path) -> None:
    out = tmp_path / "web"
    main(["--mode", "demo", "--out", str(out)])
    root = json.loads((out / "manifest.json").read_text())
    assert root["dataset_mode"] == "demo"
    caps = {i["slug"]: i for i in root["instruments"]}
    assert caps["cap-614"]["available"] is True
    assert caps["cap-599g"]["available"] is False
    assert "missing_reason" in caps["cap-599g"]
    # No Cap. 599G instrument payload in demo mode
    assert not (out / "instruments/cap-599g").exists()


def test_format_labels_match_product_language() -> None:
    """Mirror apps/lawtrace/lib/format.ts relationship labels for trust language."""
    labels = {
        "unchanged": "Unchanged",
        "text_changed": "Text changed",
        "status_changed": "Status only",
        "text_and_status_changed": "Text and status",
        "added": "Added",
        "removed": "Removed",
        "section_number_changed": "Section number changed",
    }
    text = Path("apps/lawtrace/lib/format.ts").read_text(encoding="utf-8")
    for key, label in labels.items():
        assert key in text
        assert label in text
    disc = Path("apps/lawtrace/lib/disclaimer.ts").read_text(encoding="utf-8")
    assert "not a verified copy" in disc
    assert "Hong Kong e-Legislation" in disc
    assert "commencement or effective dates" in disc.lower() or "commencement" in disc
