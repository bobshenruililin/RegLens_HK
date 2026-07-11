from __future__ import annotations

import pytest

from reglens_worker.llm.openai_gate import (
    OPENAI_RUNTIME_OPTIONS,
    OpenAIGateError,
    build_openai_payload,
    evaluate_openai_gate,
    pseudonymization_preview,
)


def test_api_key_alone_does_not_enable_openai():
    decision = evaluate_openai_gate(env={"OPENAI_API_KEY": "sk-test"})

    assert decision.provider == "mock"
    assert decision.openai_enabled is False


def test_openai_requires_all_gate_checks():
    env = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
    decision = evaluate_openai_gate(
        env=env,
        source_policy={"llm_processing_allowed": True},
        path_exists=lambda _: True,
    )

    assert decision.openai_enabled is False
    assert "REAL_LLM_PROCESSING_APPROVED is not true" in decision.reasons
    assert "REAL_LLM_APPROVAL_RECORD_PATH is not set" in decision.reasons
    assert "OPENAI_PINNED_MODEL is not set" in decision.reasons
    assert "REGLENS_PRIVACY_MODE is not set" in decision.reasons


def test_openai_enabled_when_all_checks_pass():
    env = {
        "LLM_PROVIDER": "openai",
        "REAL_LLM_PROCESSING_APPROVED": "true",
        "REAL_LLM_APPROVAL_RECORD_PATH": "/approvals/rc3.md",
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_PINNED_MODEL": "gpt-4.1-mini-2025-04-14",
        "REGLENS_PRIVACY_MODE": "pseudonymized",
    }

    decision = evaluate_openai_gate(
        env=env,
        source_policy={
            "policies": [
                {
                    "source_id": "mchk_judgments",
                    "llm_processing_allowed": True,
                    "allowed_llm_processors": ["openai"],
                }
            ]
        },
        source_id="mchk_judgments",
        path_exists=lambda path: path == "/approvals/rc3.md",
    )

    assert decision.openai_enabled is True
    assert decision.model == "gpt-4.1-mini-2025-04-14"
    assert decision.runtime_options is OPENAI_RUNTIME_OPTIONS


def test_openai_payload_disables_storage_and_tools():
    payload = build_openai_payload(model="pinned", input_text="safe text")

    assert payload["store"] is False
    assert payload["tools"] == []
    assert payload["parallel_tool_calls"] is False
    assert payload["background"] is False
    assert "file" not in payload


def test_require_enabled_raises_with_reasons():
    decision = evaluate_openai_gate(env={"LLM_PROVIDER": "openai"})

    with pytest.raises(OpenAIGateError, match="OPENAI_API_KEY"):
        decision.require_openai_enabled()


def test_pseudonymization_preview_replaces_patient_and_contact_tokens():
    preview = pseudonymization_preview(
        "Patient A emailed patient@example.com and called 9123-4567."
    )

    assert "Patient A" not in preview.text
    assert "patient@example.com" not in preview.text
    assert "9123-4567" not in preview.text
    assert "[PATIENT_1]" in preview.text
    assert "[CONTACT_1]" in preview.text
    assert len(preview.replacements) == 3
