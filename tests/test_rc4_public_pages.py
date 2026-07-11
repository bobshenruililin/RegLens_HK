"""RC4 public Observatory routes stay synthetic-only and static."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_APP = ROOT / "apps" / "site" / "app"


def test_rc4_public_pages_exist():
    for route in ("tour", "questions", "roadmap"):
        page = SITE_APP / route / "page.tsx"
        assert page.exists(), f"missing public RC4 route: /{route}/"


def test_research_routes_not_in_public_site():
    forbidden = [
        SITE_APP / "research",
        SITE_APP / "internal-research",
        SITE_APP / "core10",
        SITE_APP / "core50",
    ]
    for path in forbidden:
        assert not path.exists(), f"internal research route must not be public: {path}"


def test_rc4_pages_disclose_synthetic_or_public_boundary():
    required = {
        "tour": "synthetic",
        "questions": "synthetic",
        "roadmap": "GitHub Pages is public",
    }
    for route, needle in required.items():
        text = (SITE_APP / route / "page.tsx").read_text(encoding="utf-8")
        assert needle in text
