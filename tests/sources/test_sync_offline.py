from __future__ import annotations

from pathlib import Path

import pytest

from reglens_worker.sources.policy import AcquisitionNotAllowedError
from reglens_worker.sources.sync import sync_source

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "source_html"


def test_sync_source_offline_metadata_dry_run_mchk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REGLENS_MODE", "demo")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = sync_source("mchk_judgments", dry_run=True, fixture_dir=FIXTURE_DIR)

    assert result.source_id == "mchk_judgments"
    assert result.mode == "metadata_dry_run"
    assert result.dry_run is True
    assert result.live is False
    assert result.discovered_count == 2
    assert result.persisted_count == 0
    assert result.parser_health["ok"] is True


def test_sync_source_offline_metadata_dry_run_dchk() -> None:
    result = sync_source("dchk_judgments", dry_run=True, fixture_dir=FIXTURE_DIR)

    assert result.source_id == "dchk_judgments"
    assert result.discovered_count == 2
    assert result.parser_health["case_ref_ratio"] == 1.0


def test_sync_source_acquire_respects_manual_only_policy() -> None:
    with pytest.raises(AcquisitionNotAllowedError):
        sync_source("dchk_judgments", dry_run=True, acquire=True, fixture_dir=FIXTURE_DIR)
