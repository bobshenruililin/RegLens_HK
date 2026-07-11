"""Unit tests for migration runner helpers (no live Postgres required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reglens_worker.migrate import file_checksum, migrations_dir
from reglens_worker.mode import assert_local_database_url, get_mode

ROOT = Path(__file__).resolve().parents[1]


def test_checksum_stability() -> None:
    path = migrations_dir() / "0001_rc2_baseline.sql"
    assert path.is_file()
    first = file_checksum(path)
    second = file_checksum(path)
    assert first == second
    assert len(first) == 64
    assert all(c in "0123456789abcdef" for c in first)


def test_migrations_dir_finds_baseline() -> None:
    directory = migrations_dir()
    assert directory == ROOT / "packages" / "db" / "migrations"
    baseline = directory / "0001_rc2_baseline.sql"
    assert baseline.is_file()
    names = sorted(p.name for p in directory.glob("*.sql"))
    assert "0001_rc2_baseline.sql" in names


def test_assert_local_database_url_accepts_loopback() -> None:
    url = "postgresql://reglens@127.0.0.1:5432/reglens"
    assert assert_local_database_url(url) == url


def test_assert_local_database_url_rejects_remote() -> None:
    with pytest.raises(ValueError, match="non-local"):
        assert_local_database_url("postgresql://user@db.example.com/reglens")


def test_get_mode_defaults_to_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REGLENS_MODE", raising=False)
    assert get_mode() == "demo"
    monkeypatch.setenv("REGLENS_MODE", "")
    assert get_mode() == "demo"
