#!/usr/bin/env python3
"""LawTrace doctor — report dataset, build, and port readiness."""

from __future__ import annotations

import json
import socket
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "apps/lawtrace/public/data"
OUT = ROOT / "apps/lawtrace/out"
EXTRACT = ROOT / "data/lawtrace/extracted/cap599g"
PID_FILE = ROOT / "apps/lawtrace/.lawtrace-preview.pid"
PORT_FILE = ROOT / "apps/lawtrace/.lawtrace-preview.port"


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    print("LawTrace doctor")
    print("===============")
    print(f"repo: {ROOT}")

    # Dependencies
    missing = []
    for cmd in ("python3", "npm", "node"):
        from shutil import which

        ok = which(cmd) is not None
        print(f"dep {cmd}: {'ok' if ok else 'MISSING'}")
        if not ok:
            missing.append(cmd)

    xml_count = len(list(EXTRACT.rglob("*.xml"))) if EXTRACT.is_dir() else 0
    print(f"Cap. 599G extracts: {xml_count} XML under {EXTRACT}")

    mode = "unknown"
    instruments: list[dict] = []
    if (DATA / "manifest.json").is_file():
        root = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
        mode = root.get("dataset_mode", "unknown")
        instruments = root.get("instruments", [])
        print(f"generated dataset_mode: {mode}")
        print(f"generation_timestamp: {root.get('generation_timestamp')}")
        for inst in instruments:
            samp = inst.get("sampling") or {}
            print(
                f"  - {inst.get('slug')}: available={inst.get('available')} "
                f"versions={inst.get('version_count')} sections={inst.get('section_count')} "
                f"sampling={samp.get('versions_included')}/{samp.get('total_available_versions')} "
                f"complete={samp.get('complete')}"
            )
    else:
        print("generated data: ABSENT (run make lawtrace-web-data or lawtrace-web-data-local)")

    print(f"static build out/: {'present' if (OUT / 'index.html').is_file() else 'ABSENT'}")
    if (OUT / "instruments/cap-599g/index.html").is_file():
        print("out Cap. 599G page: present")
    else:
        print("out Cap. 599G page: absent (demo build or not built)")

    review_in_out = (OUT / "review").is_dir()
    print(f"review workspace in out/: {'yes' if review_in_out else 'no (expected for ordinary builds)'}")

    port = None
    if PORT_FILE.is_file():
        try:
            port = int(PORT_FILE.read_text().strip())
        except ValueError:
            port = None
    if port:
        print(f"recorded preview port: {port} ({'LISTENING' if port_open(port) else 'not listening'})")
        if port_open(port):
            print(f"Open: http://127.0.0.1:{port}/")
    else:
        print("recorded preview port: none")
        for candidate in (3010, 3011, 3012):
            if port_open(candidate):
                print(f"port {candidate}: in use")

    if missing:
        print("\nNext: install missing dependencies, then make lawtrace-open")
        return 1
    if xml_count > 0:
        print("\nNext: make lawtrace-open   # prefers complete Cap. 599G local-real")
    else:
        print("\nNext: make lawtrace-open-demo   # Cap. 614 demo only")
    print(f"checked_at: {datetime.now().isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
