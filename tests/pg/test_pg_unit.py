"""Unit tests for pg helpers that do not require a live database."""

from __future__ import annotations

import uuid

import pytest

from reglens_worker.pg.decisions import (
    DECISION_NAMESPACE,
    DecisionError,
    decision_id_for,
    public_slug_from_external_ref,
)
from reglens_worker.pg.users import hash_password, hash_session_token, verify_password


def test_decision_id_for_stability() -> None:
    first = decision_id_for("mchk_judgments", "SYN-MCHK-2024-001")
    second = decision_id_for("mchk_judgments", "SYN-MCHK-2024-001")
    assert first == second
    assert isinstance(first, uuid.UUID)
    assert first.version == 5
    # Different source or ref ⇒ different id
    assert decision_id_for("dchk_judgments", "SYN-MCHK-2024-001") != first
    assert decision_id_for("mchk_judgments", "SYN-MCHK-2024-002") != first
    # Explicit namespace material
    expected = uuid.uuid5(
        DECISION_NAMESPACE,
        "reglens:decision:mchk_judgments:SYN-MCHK-2024-001",
    )
    assert first == expected


def test_decision_id_for_rejects_empty() -> None:
    with pytest.raises(DecisionError):
        decision_id_for("", "ref")
    with pytest.raises(DecisionError):
        decision_id_for("mchk_judgments", "  ")


def test_public_slug_from_external_ref() -> None:
    assert public_slug_from_external_ref("SYN-MCHK-2024-001") == "syn-mchk-2024-001"
    with pytest.raises(DecisionError):
        public_slug_from_external_ref("Bad Slug!")


def test_password_hash_verify_roundtrip() -> None:
    stored = hash_password("correct horse battery")
    assert stored.startswith("scrypt$")
    parts = stored.split("$")
    assert len(parts) == 6
    assert parts[0] == "scrypt"
    assert parts[1].isdigit()
    assert verify_password("correct horse battery", stored) is True
    assert verify_password("wrong-password", stored) is False
    # Fresh hash uses a new salt
    other = hash_password("correct horse battery")
    assert other != stored
    assert verify_password("correct horse battery", other) is True


def test_session_token_hash_stability() -> None:
    token = "unit-test-session-token-value"
    first = hash_session_token(token)
    second = hash_session_token(token)
    assert first == second
    assert len(first) == 64
    assert all(c in "0123456789abcdef" for c in first)
    assert hash_session_token(token + "x") != first
