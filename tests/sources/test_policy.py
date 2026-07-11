from __future__ import annotations

import pytest

from reglens_worker.sources.policy import (
    AcquisitionNotAllowedError,
    LivePrerequisiteError,
    SourceDisabledError,
    assert_enabled,
    assert_live_prerequisites,
    assert_mode_allows_acquire,
    get_policy,
    load_policy_document,
    user_agent_for_policy,
)


def test_policy_document_loads_and_validates() -> None:
    document = load_policy_document()
    assert document["schema_version"] == "1.0.0"
    assert {policy["source_id"] for policy in document["policies"]} == {
        "mchk_judgments",
        "dchk_judgments",
    }


def test_disabled_policy_cannot_be_overridden_by_mode_flags() -> None:
    policy = get_policy("mchk_judgments")
    policy["enabled"] = False
    with pytest.raises(SourceDisabledError):
        assert_enabled(policy)
    with pytest.raises(SourceDisabledError):
        assert_mode_allows_acquire(policy)


def test_manual_only_source_does_not_allow_acquire() -> None:
    with pytest.raises(AcquisitionNotAllowedError):
        assert_mode_allows_acquire("dchk_judgments")


def test_live_prerequisites_require_mode_database_and_contact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REGLENS_MODE", "demo")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REGLENS_HTTP_CONTACT", raising=False)
    with pytest.raises(LivePrerequisiteError, match="REGLENS_MODE=postgres"):
        assert_live_prerequisites("mchk_judgments")

    monkeypatch.setenv("REGLENS_MODE", "postgres")
    with pytest.raises(LivePrerequisiteError, match="DATABASE_URL"):
        assert_live_prerequisites("mchk_judgments")

    monkeypatch.setenv("DATABASE_URL", "postgresql://reglens@localhost/reglens")
    with pytest.raises(LivePrerequisiteError, match="REGLENS_HTTP_CONTACT"):
        assert_live_prerequisites("mchk_judgments")

    monkeypatch.setenv("REGLENS_HTTP_CONTACT", "https://reglens.hk/contact")
    assert assert_live_prerequisites("mchk_judgments")["source_id"] == "mchk_judgments"
    assert user_agent_for_policy("mchk_judgments") == (
        "RegLensHK/RC3 (+https://reglens.hk/contact)"
    )
