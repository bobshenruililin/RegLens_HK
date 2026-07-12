from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from lawtrace_worker.limits import ResourceLimits
from lawtrace_worker.security.zip_safe import ZipSecurityError, inspect_zip, safe_extract


def _write_zip(
    path: Path, members: dict[str, bytes], *, compress: int = zipfile.ZIP_DEFLATED
) -> None:
    with zipfile.ZipFile(path, "w", compression=compress) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def test_rejects_path_traversal(tmp_path: Path) -> None:
    z = tmp_path / "bad.zip"
    _write_zip(z, {"../../etc/passwd": b"nope"})
    with pytest.raises(ZipSecurityError, match="path_traversal"):
        inspect_zip(z)


def test_rejects_absolute_path(tmp_path: Path) -> None:
    z = tmp_path / "abs.zip"
    _write_zip(z, {"/tmp/evil.xml": b"<a/>"})
    with pytest.raises(ZipSecurityError, match="absolute_path"):
        inspect_zip(z)


def test_rejects_windows_traversal(tmp_path: Path) -> None:
    z = tmp_path / "win.zip"
    _write_zip(z, {"..\\..\\evil.xml": b"<a/>"})
    with pytest.raises(ZipSecurityError, match="path_traversal"):
        inspect_zip(z)


def test_rejects_bomb_ratio(tmp_path: Path) -> None:
    z = tmp_path / "bomb.zip"
    data = b"0" * (2 * 1024 * 1024)
    _write_zip(z, {"big.xml": data})
    limits = ResourceLimits(max_compression_ratio=5.0, max_individual_file_bytes=10 * 1024 * 1024)
    with pytest.raises(ZipSecurityError, match="compression_ratio"):
        inspect_zip(z, limits=limits)


def test_rejects_too_many_entries(tmp_path: Path) -> None:
    z = tmp_path / "many.zip"
    members = {f"f{i}.xml": b"<a/>" for i in range(20)}
    _write_zip(z, members)
    limits = ResourceLimits(max_archive_entries=10)
    with pytest.raises(ZipSecurityError, match="too many"):
        inspect_zip(z, limits=limits)


def test_safe_extract_preserves_windows_relative_path(tmp_path: Path) -> None:
    z = tmp_path / "ok.zip"
    _write_zip(z, {"dir\\cap_614_20200101000000_en_p.xml": b"<lawDoc/>"})
    dest = tmp_path / "out"
    result = safe_extract(z, dest, name_contains=("cap_614",), overwrite=False)
    assert len(result.written) == 1
    assert result.written[0].name == "cap_614_20200101000000_en_p.xml"
    assert result.written[0].parent.name == "dir"
    assert result.written[0].read_bytes() == b"<lawDoc/>"


def test_refuses_overwrite_preexisting(tmp_path: Path) -> None:
    z = tmp_path / "ok.zip"
    _write_zip(z, {"a.xml": b"<a/>"})
    dest = tmp_path / "out"
    safe_extract(z, dest, name_contains=("a.xml",), overwrite=True)
    with pytest.raises(ZipSecurityError, match="refusing_overwrite"):
        safe_extract(z, dest, name_contains=("a.xml",), overwrite=False)


def test_duplicate_basenames_different_windows_paths_no_silent_overwrite(
    tmp_path: Path,
) -> None:
    """Regression: distinct members sharing a basename must not clobber."""
    z = tmp_path / "dup.zip"
    _write_zip(
        z,
        {
            "cap_599_en_p\\v1\\same.xml": b"<a id='1'/>",
            "cap_599_en_p\\v2\\same.xml": b"<a id='2'/>",
        },
    )
    dest = tmp_path / "out"
    # Default: preserve relative paths — both survive.
    result = safe_extract(z, dest, name_contains=("same.xml",), overwrite=False)
    assert len(result.written) == 2
    texts = sorted(p.read_bytes() for p in result.written)
    assert texts == [b"<a id='1'/>", b"<a id='2'/>"]

    # Flatten mode must fail explicitly rather than silently overwrite.
    dest2 = tmp_path / "out_flat"
    with pytest.raises(ZipSecurityError, match="destination_collision"):
        safe_extract(
            z,
            dest2,
            name_contains=("same.xml",),
            overwrite=False,
            preserve_archive_relative_path=False,
            on_collision="fail",
        )


def test_identical_duplicate_can_be_recorded_not_hidden(tmp_path: Path) -> None:
    z = tmp_path / "ident.zip"
    payload = b"<a/>"
    _write_zip(
        z,
        {
            "p1\\same.xml": payload,
            "p2\\same.xml": payload,
        },
    )
    dest = tmp_path / "out"
    result = safe_extract(
        z,
        dest,
        name_contains=("same.xml",),
        overwrite=False,
        preserve_archive_relative_path=False,
        on_collision="skip_identical",
    )
    assert len(result.written) == 1
    assert len(result.identical_duplicate_skips) == 1
    assert result.identical_duplicate_skips[0]["bytes_identical"] is True
    assert len(result.collisions) == 1
