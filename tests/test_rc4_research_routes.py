"""MVP-RC4 research route and public-site isolation checks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO_APP = ROOT / "apps" / "studio" / "app"
SITE = ROOT / "apps" / "site"


def test_studio_research_and_core10_routes_exist():
    required = [
        STUDIO_APP / "research" / "page.tsx",
        STUDIO_APP / "research" / "explore" / "page.tsx",
        STUDIO_APP / "research" / "explore" / "ExploreClient.tsx",
        STUDIO_APP / "research" / "compare" / "page.tsx",
        STUDIO_APP / "research" / "issues" / "page.tsx",
        STUDIO_APP / "research" / "issues" / "[code]" / "page.tsx",
        STUDIO_APP / "research" / "sanctions" / "page.tsx",
        STUDIO_APP / "research" / "rules" / "page.tsx",
        STUDIO_APP / "research" / "authorities" / "page.tsx",
        STUDIO_APP / "research" / "coverage" / "page.tsx",
        STUDIO_APP / "research" / "collections" / "page.tsx",
        STUDIO_APP / "research" / "collections" / "[id]" / "page.tsx",
        STUDIO_APP / "pilot" / "core10" / "page.tsx",
        STUDIO_APP / "pilot" / "core10" / "[decision-id]" / "page.tsx",
        STUDIO_APP / "api" / "research" / "collections" / "route.ts",
        STUDIO_APP / "api" / "research" / "collections" / "[id]" / "export" / "route.ts",
    ]
    missing = [path for path in required if not path.is_file()]
    assert not missing


def test_site_nav_includes_internal_research_links():
    nav = (ROOT / "apps" / "studio" / "components" / "SiteNav.tsx").read_text(encoding="utf-8")
    assert 'href="/research"' in nav
    assert 'href="/pilot/core10"' in nav


def test_public_site_does_not_include_research_route_or_links():
    assert not (SITE / "app" / "research").exists()
    assert not (SITE / "src" / "app" / "research").exists()
    offenders: list[Path] = []
    for path in SITE.rglob("*"):
        if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        if 'href="/research' in text or "'/research" in text or '"/research' in text:
            offenders.append(path)
    assert offenders == []


def test_core10_spec_contains_ten_synthetic_placeholders():
    spec = json.loads(
        (ROOT / "publications" / "pilot" / "core10.v1.json").read_text(encoding="utf-8")
    )
    assert spec["planned_total"] == 10
    assert "not representative" in spec["statistical_note"].lower()
    slots = spec["slots"]
    assert len(slots) == 10
    assert {slot["inclusion_status"] for slot in slots} <= {
        "planned",
        "included",
        "blocked",
    }
    assert all(slot["external_ref"].startswith("SYN-") for slot in slots)
