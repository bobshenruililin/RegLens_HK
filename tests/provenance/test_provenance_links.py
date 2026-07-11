from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.ingest import ingest_fixture, load_manifest  # noqa: E402
from reglens_worker.store import LocalArtifactStore  # noqa: E402


def test_published_proposition_has_span(tmp_path: Path):
    fixtures = ROOT / "fixtures"
    row = load_manifest(fixtures / "manifests/m1.jsonl")[0]
    decision = ingest_fixture(
        fixtures_root=fixtures,
        store=LocalArtifactStore(tmp_path),
        row=row,
        review_accept=True,
    )
    for prop in decision["propositions"]:
        assert prop["published"] is True
        assert prop["review_status"] == "accepted"
        assert len(prop["evidence"]) >= 1
