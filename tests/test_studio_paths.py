"""Studio path safety: never read/write fixtures/seed (source inspection, node-free)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO_DATA_TS = ROOT / "apps" / "studio" / "lib" / "data.ts"


def test_studio_data_ts_exists():
    assert STUDIO_DATA_TS.is_file()


def test_studio_data_ts_does_not_contain_fixtures_seed():
    """apps/studio/lib/data.ts must not reference fixtures/seed as a data root."""
    source = STUDIO_DATA_TS.read_text(encoding="utf-8")
    assert "fixtures/seed" not in source
    # Positive signal: Studio targets data/seed only
    assert "data/seed" in source
    assert "assertNotFixturesPath" in source
