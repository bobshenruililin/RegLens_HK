"""Object storage abstractions (Milestone 2B)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Protocol

from .hashutil import sha256_file


class ObjectStore(Protocol):
    def put_immutable(self, src: Path, sha256: str) -> str:
        """Store bytes once under a content-addressed key; return storage_key."""

    def exists(self, storage_key: str) -> bool: ...

    def open_path(self, storage_key: str) -> Path:
        """Local path for reading when available (local store / downloaded cache)."""


class LocalObjectStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        return self.root / storage_key

    def put_immutable(self, src: Path, sha256: str) -> str:
        storage_key = f"sha256/{sha256[:2]}/{sha256}"
        dest = self._path(storage_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if sha256_file(dest) != sha256:
                raise RuntimeError(f"Corrupt or colliding blob at {dest}")
            return storage_key
        shutil.copy2(src, dest)
        (dest.parent / f"{sha256}.immutable").write_text("1", encoding="utf-8")
        return storage_key

    def exists(self, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def open_path(self, storage_key: str) -> Path:
        path = self._path(storage_key)
        if not path.is_file():
            raise FileNotFoundError(storage_key)
        return path


class S3ObjectStore:
    """Optional MinIO/S3 backend. Requires boto3 and env credentials."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        cache_dir: Path | None = None,
    ):
        import boto3

        self.bucket = bucket
        self.cache_dir = cache_dir or Path("data/s3-cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    def put_immutable(self, src: Path, sha256: str) -> str:
        storage_key = f"sha256/{sha256[:2]}/{sha256}"
        try:
            self.client.head_object(Bucket=self.bucket, Key=storage_key)
            return storage_key
        except Exception:
            pass
        extra = {"Metadata": {"sha256": sha256, "immutable": "true"}}
        self.client.upload_file(str(src), self.bucket, storage_key, ExtraArgs=extra)
        return storage_key

    def exists(self, storage_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except Exception:
            return False

    def open_path(self, storage_key: str) -> Path:
        local = self.cache_dir / storage_key
        local.parent.mkdir(parents=True, exist_ok=True)
        if not local.exists():
            self.client.download_file(self.bucket, storage_key, str(local))
        return local


def build_object_store(data_root: Path) -> ObjectStore:
    backend = os.environ.get("OBJECT_STORE", "local").lower()
    if backend in {"s3", "minio"}:
        return S3ObjectStore(
            bucket=os.environ.get("S3_BUCKET", "reglens"),
            endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
            access_key=os.environ.get("S3_ACCESS_KEY", "reglens"),
            secret_key=os.environ.get("S3_SECRET_KEY", "reglenssecret"),
            cache_dir=data_root / "s3-cache",
        )
    return LocalObjectStore(data_root / "objects")
