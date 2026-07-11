"""Local ObjectStore unit tests (no Postgres / S3 required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from reglens_worker.hashutil import sha256_file
from reglens_worker.objectstore import (
    LocalObjectStore,
    ObjectCorruptError,
    ObjectHashMismatch,
    ObjectNotFound,
    build_object_store,
    storage_key_for_sha256,
)


def test_local_put_get_roundtrip(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    src = tmp_path / "doc.bin"
    src.write_bytes(b"reglens-blob-bytes")
    digest = sha256_file(src)

    key = store.put_immutable(src, digest)
    assert key == storage_key_for_sha256(digest)
    assert store.exists(key)

    data = store.get(key, expected_sha256=digest)
    assert data == b"reglens-blob-bytes"
    assert store.get(key) == b"reglens-blob-bytes"


def test_local_put_idempotent_same_hash(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    src = tmp_path / "a.txt"
    src.write_text("same", encoding="utf-8")
    digest = sha256_file(src)
    key1 = store.put_immutable(src, digest)
    key2 = store.put_immutable(src, digest)
    assert key1 == key2


def test_local_put_rejects_hash_mismatch(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    src = tmp_path / "a.txt"
    src.write_text("payload", encoding="utf-8")
    with pytest.raises(ObjectHashMismatch):
        store.put_immutable(src, "0" * 64)


def test_local_corrupt_existing_rejected(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    src = tmp_path / "good.txt"
    src.write_text("good-bytes", encoding="utf-8")
    digest = sha256_file(src)
    key = store.put_immutable(src, digest)

    dest = store.open_path(key)
    dest.write_text("tampered", encoding="utf-8")

    with pytest.raises(ObjectCorruptError):
        store.put_immutable(src, digest)

    with pytest.raises(ObjectCorruptError):
        store.get(key, expected_sha256=digest)


def test_local_get_missing(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    with pytest.raises(ObjectNotFound):
        store.get(storage_key_for_sha256("a" * 64))


def test_build_object_store_local_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OBJECT_STORE", raising=False)
    store = build_object_store(tmp_path)
    assert isinstance(store, LocalObjectStore)
    assert store.root == tmp_path / "objects"
