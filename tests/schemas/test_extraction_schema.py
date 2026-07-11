from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "worker"))

from reglens_worker.schema_validate import validate_extraction  # noqa: E402


def test_legal_test_must_be_interpretation():
    payload = {
        "schema_version": "1.0.0",
        "document_sha256": "b" * 64,
        "extractor": {
            "pipeline_version": "m1",
            "model_provider": "mock",
            "model_version": "1",
            "prompt_version": "1",
        },
        "propositions": [
            {
                "id": "00000000-0000-4000-8000-000000000002",
                "prop_type": "legal_test",
                "epistemic_class": "fact",
                "claim_text": "A legal test claim",
                "confidence": 0.4,
                "evidence": [{"page_no": 1, "quote": "A legal test claim"}],
            }
        ],
    }
    errors = validate_extraction(payload)
    assert errors, "legal_test labelled as fact should fail schema"
