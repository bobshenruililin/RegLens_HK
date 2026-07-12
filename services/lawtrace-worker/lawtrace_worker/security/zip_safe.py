"""Safe ZIP extraction for untrusted LawTrace archives."""

from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass, field
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


def _safe_rel_parts(norm_name: str) -> tuple[str, ...]:
    """Return sanitized relative path parts for preserving archive structure."""
    parts = tuple(p for p in PurePosixPath(norm_name).parts if p not in ("", "."))
    if not parts or any(p == ".." for p in parts):
        raise ZipSecurityError(f"invalid_relative_path: {norm_name!r}")
    return parts


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
        for info in zf.infolist():
            entries += 1
            if entries > limits.max_archive_entries:
                raise ZipSecurityError("too many archive entries")
            danger = _is_dangerous_name(info.filename)
            if danger:
                raise ZipSecurityError(f"{danger}: {info.filename!r}")
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
                raise ZipSecurityError(f"member too large: {info.filename!r} ({info.file_size})")
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
                    "normalized_name": _normalize_zip_name(info.filename),
                    "basename": _basename(info.filename),
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


@dataclass
class ExtractResult:
    written: list[Path] = field(default_factory=list)
    accepted_members: list[dict] = field(default_factory=list)
    rejected_members: list[dict] = field(default_factory=list)
    collisions: list[dict] = field(default_factory=list)
    identical_duplicate_skips: list[dict] = field(default_factory=list)


def _sha256_stream(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    h = hashlib.sha256()
    with zf.open(info, "r") as src:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def safe_extract(
    archive: Path,
    dest: Path,
    *,
    name_prefixes: tuple[str, ...] | None = None,
    name_contains: tuple[str, ...] | None = None,
    limits: ResourceLimits = DEFAULT_LIMITS,
    overwrite: bool = False,
    preserve_archive_relative_path: bool = True,
    on_collision: str = "fail",
) -> ExtractResult:
    """Extract selected members into dest after safety checks.

    Distinct archive members must never silently overwrite one another after
    path normalization.

    Strategies:
    - preserve_archive_relative_path=True (default, option A): write under
      dest/<normalized-archive-relative-path>.
    - on_collision:
        - "fail" (option C, default): raise with both member names recorded
        - "collision_safe_name" (option B): deterministic dest name using
          SHA-256 of the normalized member path
        - "skip_identical": if bytes identical, skip and record; else fail

    `overwrite` only allows replacing an existing on-disk file when the
    incoming member is the same archived path already recorded for that
    destination in this run, or when explicitly re-extracting the same
    member. It never authorizes silent cross-member clobbering.
    """
    if on_collision not in {"fail", "collision_safe_name", "skip_identical"}:
        raise ValueError(f"unsupported on_collision: {on_collision}")

    meta = inspect_zip(archive, limits=limits)
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    result = ExtractResult()
    # Map destination path -> first member that claimed it in this extraction.
    claimed: dict[Path, str] = {}

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
                if name_prefixes is None and name_contains is None:
                    raise ZipSecurityError(f"unexpected_file_type: {name!r}")
                result.rejected_members.append(
                    {
                        "member": name,
                        "reason": "unexpected_file_type",
                        "normalized_name": norm,
                    }
                )
                continue

            if preserve_archive_relative_path:
                rel_parts = _safe_rel_parts(norm)
                target = (dest.joinpath(*rel_parts)).resolve()
            else:
                target = (dest / base).resolve()

            if dest not in target.parents and target != dest:
                raise ZipSecurityError(f"escape_detected: {name!r} -> {target}")

            # Destination already claimed by a different member in this run.
            if target in claimed and claimed[target] != name:
                other = claimed[target]
                collision = {
                    "destination": str(target.relative_to(dest)),
                    "member_a": other,
                    "member_b": name,
                    "member_a_normalized": _normalize_zip_name(other),
                    "member_b_normalized": norm,
                }
                if on_collision == "fail":
                    collision["resolution"] = "fail"
                    result.collisions.append(collision)
                    raise ZipSecurityError(
                        "destination_collision: "
                        f"{other!r} and {name!r} both map to {target}"
                    )
                if on_collision == "skip_identical":
                    sha_a = None
                    # Recompute from archive for both
                    info_a = next(i for i in zf.infolist() if i.filename == other)
                    sha_a = _sha256_stream(zf, info_a)
                    sha_b = _sha256_stream(zf, info)
                    collision["member_a_sha256"] = sha_a
                    collision["member_b_sha256"] = sha_b
                    collision["bytes_identical"] = sha_a == sha_b
                    if sha_a == sha_b:
                        collision["resolution"] = "skip_identical_duplicate"
                        result.identical_duplicate_skips.append(collision)
                        result.collisions.append(collision)
                        continue
                    collision["resolution"] = "fail_divergent_duplicate"
                    result.collisions.append(collision)
                    raise ZipSecurityError(
                        "destination_collision_divergent_bytes: "
                        f"{other!r} and {name!r} both map to {target}"
                    )
                # collision_safe_name
                digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
                safe_name = f"{Path(base).stem}__{digest}{Path(base).suffix}"
                target = (dest / "_collision_safe" / safe_name).resolve()
                if dest not in target.parents:
                    raise ZipSecurityError(f"escape_detected: {name!r} -> {target}")
                collision["resolution"] = "collision_safe_name"
                collision["resolved_destination"] = str(target.relative_to(dest))
                result.collisions.append(collision)

            if target.exists() and not overwrite:
                # Existing file from a prior run / other archive.
                if on_collision == "collision_safe_name":
                    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
                    safe_name = f"{Path(base).stem}__{digest}{Path(base).suffix}"
                    target = (dest / "_collision_safe" / safe_name).resolve()
                    result.collisions.append(
                        {
                            "destination": str(target.relative_to(dest)),
                            "member_a": f"<preexisting {target.name}>",
                            "member_b": name,
                            "resolution": "collision_safe_name_preexisting",
                        }
                    )
                else:
                    raise ZipSecurityError(f"refusing_overwrite: {target}")

            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, target.open("wb") as out:
                remaining = info.file_size
                while remaining > 0:
                    chunk = src.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    out.write(chunk)
                if remaining != 0:
                    raise ZipSecurityError(f"truncated_member: {name!r}")

            claimed[target] = name
            result.written.append(target)
            result.accepted_members.append(
                {
                    "member": name,
                    "normalized_name": norm,
                    "destination": str(target.relative_to(dest)),
                    "file_size": info.file_size,
                }
            )

    _ = meta
    return result
