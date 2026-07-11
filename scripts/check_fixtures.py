#!/usr/bin/env python3
"""CI guard: tracked fixtures must be synthetic; reject likely real regulator PDFs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
MANIFESTS = FIXTURES / "manifests"
SYNTHETIC = FIXTURES / "synthetic"

# Filenames that look like published MCHK/DCHK judgment dumps (heuristic).
SUSPICIOUS = (
    "DISCIPLINARY_INQUIRY",
    "DISCIPLINARYINQUIRY",
    "judgment_handed",
)


def main() -> int:
    errors: list[str] = []
    if (FIXTURES / "raw").exists():
        errors.append("fixtures/raw must not exist; use fixtures/synthetic/ or private-data/")

    seed_dir = FIXTURES / "seed"
    if seed_dir.exists():
        errors.append(
            "fixtures/seed must not exist; generated decisions belong under data/ "
            "(gitignored), not fixtures/"
        )

    for decision_json in FIXTURES.rglob("decision.json"):
        errors.append(
            f"generated decision artifact must not be committed under fixtures/: "
            f"{decision_json.relative_to(ROOT)}"
        )

    for manifest in MANIFESTS.glob("*.jsonl"):
        for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.strip().startswith("#"):
                continue
            row = json.loads(line)
            kind = row.get("fixture_kind")
            if kind != "synthetic":
                errors.append(
                    f"{manifest.name}:{line_no} fixture_kind must be synthetic in tracked manifests"
                )
            rel = row.get("relative_path", "")
            if not rel.startswith("synthetic/"):
                errors.append(f"{manifest.name}:{line_no} relative_path must be under synthetic/")
            path = FIXTURES / rel
            if not path.is_file():
                errors.append(f"{manifest.name}:{line_no} missing file {rel}")

    for pdf in SYNTHETIC.rglob("*.pdf"):
        name = pdf.name.upper()
        if any(tok in name for tok in SUSPICIOUS) and not name.startswith("SYN-"):
            errors.append(f"suspicious non-synthetic PDF name under fixtures/synthetic: {pdf}")

    if (ROOT / "private-data").exists():
        # Ensure private-data is not accidentally tracked via git ls-files in CI later
        pass

    if errors:
        print("Fixture safety check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("Fixture safety check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
