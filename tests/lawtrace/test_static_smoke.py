"""Smoke-test LawTrace static export routes (no browser required)."""

from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "apps/lawtrace/out"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def test_static_routes_and_trust_copy(tmp_path_factory=None) -> None:
    assert (OUT / "index.html").is_file(), "Run make lawtrace-build first"
    review_built = (OUT / "review").exists()
    if not review_built:
        assert not (OUT / "audit").exists()
    else:
        # Local-review builds may include /review, but never /audit.
        assert not (OUT / "audit").exists()

    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts/lawtrace_static_server.py"),
            "--dir",
            str(OUT),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        base = f"http://127.0.0.1:{port}"
        for _ in range(40):
            try:
                code, _ = _get(base + "/")
                if code == 200:
                    break
            except Exception:
                time.sleep(0.1)
        else:
            raise AssertionError("static server failed to start")

        # Deep-link refresh behaviour for nested routes
        routes = [
            "/",
            "/collections/",
            "/insights/",
            "/methodology/",
            "/instruments/cap-614/",
        ]
        manifest = json.loads(
            (ROOT / "apps/lawtrace/public/data/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        for inst in manifest.get("instruments", []):
            if not inst.get("available"):
                continue
            ex = inst.get("example_comparison")
            if not ex:
                continue
            slug = inst["slug"]
            routes.append(
                f"/instruments/{slug}/sections/{ex['section_id']}/"
                f"compare/{ex['from_version']}/{ex['to_version']}/"
            )
            routes.append(
                f"/instruments/{slug}/sections/{ex['section_id']}/"
            )
            break

        bodies: dict[str, str] = {}
        for route in routes:
            code, html = _get(base + route)
            assert code == 200, f"{route} -> {code}"
            bodies[route] = html
            # Must not be a directory listing
            assert "Directory listing" not in html

        landing = bodies["/"]
        assert "See exactly how Hong Kong legislation changed" in landing
        # Ordinary navigation must never link the local review workspace.
        assert 'href="/review/"' not in landing
        assert "LawTrace HK" in landing
        if not review_built:
            assert not (OUT / "review").exists()

        # Trust / date language
        forbidden_claim = re.compile(
            r"was the law in force on|is the law in force on|"
            r"commencement date of this snapshot|effective date of this snapshot|"
            r"LawTrace(?: output)? is a verified copy",
            re.I,
        )
        for route, html in bodies.items():
            assert not forbidden_claim.search(html), f"overclaim on {route}"

        method = bodies["/methodology/"]
        assert "Official XML" in method or "official open-data" in method.lower()
        assert "reconstruction" in method.lower()

        compare = next(v for k, v in bodies.items() if "/compare/" in k)
        assert "Official open-data snapshot dated" in compare
        assert "<ins" in compare or "<del" in compare or "Added section" in compare
        assert "Provenance" in compare or "provenance" in compare
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
