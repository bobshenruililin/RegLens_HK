"""Public Observatory (apps/site) must be a static export — no server middleware/API."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "apps" / "site"


def test_site_next_config_has_output_export():
    config = (SITE / "next.config.js").read_text(encoding="utf-8")
    assert 'output: "export"' in config or "output: 'export'" in config


def test_site_has_no_middleware():
    assert not (SITE / "middleware.ts").exists()
    assert not (SITE / "middleware.js").exists()
    assert not (SITE / "src" / "middleware.ts").exists()


def test_site_has_no_app_api_directory():
    assert not (SITE / "app" / "api").exists()
    assert not (SITE / "src" / "app" / "api").exists()
