"""Regression: metadata-only deltas must not be labelled text_changed."""

from __future__ import annotations

from lawtrace_worker.compare import classify_relationship


def test_start_period_only_is_status_changed() -> None:
    rel, classes = classify_relationship(
        text_equal=True,
        structure_equal=True,
        meta_ops=[{"field": "start_period", "a": "2020-03-29", "b": "2020-04-10"}],
        num_a="4.",
        num_b="4.",
        same_id=True,
    )
    assert rel == "status_changed"
    assert "other_metadata_changed" in classes
    assert "legal_text_changed" not in classes


def test_status_field_only_is_status_changed() -> None:
    rel, _ = classify_relationship(
        text_equal=True,
        structure_equal=True,
        meta_ops=[{"field": "status", "a": "operational", "b": "omitted"}],
        num_a="1.",
        num_b="1.",
        same_id=True,
    )
    assert rel == "status_changed"
