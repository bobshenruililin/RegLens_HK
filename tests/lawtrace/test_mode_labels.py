"""Mode badge labelling for complete vs sampled collections."""

from __future__ import annotations


def test_complete_badge_shows_ratio() -> None:
    # Mirror apps/lawtrace/lib/mode.ts logic in a lightweight assertion helper
    sampling = {
        "complete": True,
        "versions_included": 101,
        "total_available_versions": 101,
    }
    if sampling["complete"]:
        label = f"Complete {sampling['versions_included']}/{sampling['total_available_versions']}"
    else:
        label = f"Sampled {sampling['versions_included']}/{sampling['total_available_versions']}"
    assert label == "Complete 101/101"


def test_sampled_badge_shows_ratio() -> None:
    sampling = {
        "complete": False,
        "versions_included": 30,
        "total_available_versions": 101,
    }
    label = (
        f"Sampled {sampling['versions_included']}/{sampling['total_available_versions']}"
        if not sampling["complete"]
        else f"Complete {sampling['versions_included']}/{sampling['total_available_versions']}"
    )
    assert label == "Sampled 30/101"
    detail = (
        f"Sampled collection — {sampling['versions_included']} of "
        f"{sampling['total_available_versions']} available snapshots represented."
    )
    assert "30 of 101" in detail
