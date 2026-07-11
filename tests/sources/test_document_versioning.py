"""Document version / URL alias behaviour (unit-level, no live network)."""

from __future__ import annotations

from reglens_worker.hashutil import sha256_bytes


def test_same_bytes_same_hash() -> None:
    a = sha256_bytes(b"%PDF-1.4 synthetic")
    b = sha256_bytes(b"%PDF-1.4 synthetic")
    assert a == b


def test_changed_bytes_new_hash() -> None:
    a = sha256_bytes(b"%PDF-1.4 version-a")
    b = sha256_bytes(b"%PDF-1.4 version-b")
    assert a != b


def test_url_alias_concept_same_hash_different_url() -> None:
    """Different URLs with identical bytes share content identity (hash), not URL identity."""
    digest = sha256_bytes(b"%PDF-1.4 same-bytes")
    url_a = "https://www.mchk.org.hk/english/complaint/a.pdf"
    url_b = "https://www.mchk.org.hk/english/complaint/b.pdf"
    assert url_a != url_b
    assert digest == sha256_bytes(b"%PDF-1.4 same-bytes")
