"""Safe ZIP extraction for untrusted LawTrace archives."""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath

from lawtrace_worker.limits import DEFAULT_LIMITS, ResourceLimits


class ZipSecurityError(ValueError):
    """Raised when an archive violates safety policy."""


def _normalize_zip_name(name: str) -> str:
    """Normalize ZIP member names to POSIX-style separators for policy checks."""
    return name.replace("\\", "/")


def _basename(name: str) -> str:
    return PurePosixPath(_normalize_zip_name(name)).name


def _is_dangerous_name(name: str) -> str | None:
    if not name or name.endswith("/") or name.endswith("\\"):
        return None
    norm = _normalize_zip_name(name)
    # Reject absolute paths and Windows drive paths.
    if norm.startswith("/"):
        return "absolute_path"
    first = norm.split("/", 1)[0]
    if len(first) == 2 and first[1] == ":":
        return "drive_path"
    parts = PurePosixPath(norm).parts
    if any(p in ("..", "") for p in parts):
        return "path_traversal"
    if any(p.startswith("/") for p in parts):
        return "absolute_path"
    return None


def inspect_zip(path: Path, limits: ResourceLimits = DEFAULT_LIMITS) -> dict:
    """Inspect archive metadata without extracting. Raises ZipSecurityError on policy breach."""
    if not path.is_file():
        raise ZipSecurityError(f"not a file: {path}")
    compressed_size = path.stat().st_size
    if compressed_size > limits.max_download_bytes:
        raise ZipSecurityError(
            f"archive compressed size {compressed_size} exceeds max_download_bytes"
        )
    if not zipfile.is_zipfile(path):
        raise ZipSecurityError("not a zip file")

    total_uncompressed = 0
    entries = 0
    members: list[dict] = []
    with zipfile.ZipFile(path) as zf:
        # Reject symlinks / special types when detectable.
        for info in zf.infolist():
            entries += 1
            if entries > limits.max_archive_entries:
                raise ZipSecurityError("too many archive entries")
            danger = _is_dangerous_name(info.filename)
            if danger:
                raise ZipSecurityError(f"{danger}: {info.filename!r}")
            # External attributes: high bits are unix mode; symlink bit 0o120000
            is_symlink = False
            if info.create_system == 3:  # Unix
                mode = (info.external_attr >> 16) & 0xFFFF
                if (mode & 0o170000) == 0o120000:
                    is_symlink = True
            if is_symlink:
                raise ZipSecurityError(f"symlink_forbidden: {info.filename!r}")
            if info.is_dir():
                continue
            if info.file_size > limits.max_individual_file_bytes:
                raise ZipSecurityError(
                    f"member too large: {info.filename!r} ({info.file_size})"
                )
            total_uncompressed += info.file_size
            if total_uncompressed > limits.max_total_uncompressed_bytes:
                raise ZipSecurityError("total uncompressed size exceeds limit")
            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > limits.max_compression_ratio and info.file_size > 1024 * 1024:
                    raise ZipSecurityError(
                        f"compression_ratio_too_high: {info.filename!r} ratio={ratio:.1f}"
                    )
            members.append(
                {
                    "name": info.filename,
                    "compress_size": info.compress_size,
                    "file_size": info.file_size,
                }
            )
    return {
        "path": str(path),
        "compressed_size": compressed_size,
        "entry_count": entries,
        "total_uncompressed": total_uncompressed,
        "members": members,
    }


def safe_extract(
    archive: Path,
    dest: Path,
    *,
    name_prefixes: tuple[str, ...] | None = None,
    name_contains: tuple[str, ...] | None = None,
    limits: ResourceLimits = DEFAULT_LIMITS,
    overwrite: bool = False,
) -> list[Path]:
    """Extract selected members into dest after safety checks.

    Only regular files with allowed suffixes are written. Destination must be empty
    or overwrite explicitly allowed for each target path.
    """
    meta = inspect_zip(archive, limits=limits)
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            norm = _normalize_zip_name(name)
            base = _basename(name)
            if not base or base in (".", ".."):
                raise ZipSecurityError(f"invalid_basename: {name!r}")
            if name_prefixes and not any(
                base.startswith(p) or norm.startswith(p) or p in norm for p in name_prefixes
            ):
                continue
            if name_contains and not any(s in norm for s in name_contains):
                continue
            suffix = Path(base).suffix.lower()
            if suffix and suffix not in limits.allowed_member_suffixes:
                # Skip unknown types when filtering; reject when extracting whole archive.
                if name_prefixes is None and name_contains is None:
                    raise ZipSecurityError(f"unexpected_file_type: {name!r}")
                continue
            # Flatten to basename under dest to eliminate nested traversal surprises.
            flat = (dest / base).resolve()
            if flat.parent != dest.resolve():
                raise ZipSecurityError(f"escape_detected: {name!r} -> {flat}")
            if flat.exists() and not overwrite:
                raise ZipSecurityError(f"refusing_overwrite: {flat}")
            with zf.open(info, "r") as src, flat.open("wb") as out:
                remaining = info.file_size
                while remaining > 0:
                    chunk = src.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    out.write(chunk)
                if remaining != 0:
                    raise ZipSecurityError(f"truncated_member: {name!r}")
            written.append(flat)
    _ = meta
    return written
