from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from lawtrace_worker.limits import ResourceLimits
from lawtrace_worker.security.zip_safe import ZipSecurityError, inspect_zip, safe_extract


def _write_zip(path: Path, members: dict[str, bytes], *, compress: int = zipfile.ZIP_DEFLATED) -> None:
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
    # Highly compressible payload
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


def test_safe_extract_flattens_and_contains(tmp_path: Path) -> None:
    z = tmp_path / "ok.zip"
    _write_zip(z, {"dir\\cap_614_20200101000000_en_p.xml": b"<lawDoc/>"})
    dest = tmp_path / "out"
    written = safe_extract(z, dest, name_contains=("cap_614",), overwrite=True)
    assert len(written) == 1
    assert written[0].name == "cap_614_20200101000000_en_p.xml"
    assert written[0].read_bytes() == b"<lawDoc/>"


def test_refuses_overwrite(tmp_path: Path) -> None:
    z = tmp_path / "ok.zip"
    _write_zip(z, {"a.xml": b"<a/>"})
    dest = tmp_path / "out"
    safe_extract(z, dest, name_contains=("a.xml",), overwrite=True)
    with pytest.raises(ZipSecurityError, match="refusing_overwrite"):
        safe_extract(z, dest, name_contains=("a.xml",), overwrite=False)
