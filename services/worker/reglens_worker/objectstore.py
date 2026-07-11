"""Content-addressed object storage (MVP-RC2 Checkpoint B).

Local and optional S3/MinIO backends. SHA-256 is verified before write and
after read. Existing blobs with a matching hash are no-ops; corrupt existing
blobs raise ObjectCorruptError.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Protocol

from .hashutil import sha256_bytes, sha256_file


class ObjectStoreError(Exception):
    """Base error for object-store operations."""


class ObjectNotFound(ObjectStoreError):
    """Requested object does not exist."""


class ObjectAuthError(ObjectStoreError):
    """Authentication / credential failure talking to the object store."""


class ObjectPermissionError(ObjectStoreError):
    """Caller is authenticated but not permitted for this object/bucket."""


class ObjectNetworkError(ObjectStoreError):
    """Transport / endpoint connectivity failure."""


class ObjectCorruptError(ObjectStoreError):
    """Stored bytes do not match the expected content-addressed hash."""


class ObjectHashMismatch(ObjectStoreError):
    """Caller-supplied or expected SHA-256 does not match computed bytes."""


def storage_key_for_sha256(sha256: str) -> str:
    digest = sha256.strip().lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ObjectHashMismatch(f"Invalid SHA-256 digest: {sha256!r}")
    return f"sha256/{digest[:2]}/{digest}"


class ObjectStore(Protocol):
    def put_immutable(self, src: Path, sha256: str) -> str:
        """Store bytes once under a content-addressed key; return storage_key."""

    def get(self, storage_key: str, *, expected_sha256: str | None = None) -> bytes:
        """Read object bytes; optionally verify against expected_sha256."""

    def exists(self, storage_key: str) -> bool: ...


class LocalObjectStore:
    """Content-addressed filesystem store under ``{root}/sha256/ab/abcd...``."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        # Reject path traversal; keys are always relative content-addressed paths.
        key = storage_key.lstrip("/")
        if ".." in Path(key).parts:
            raise ObjectStoreError(f"Invalid storage_key: {storage_key!r}")
        return self.root / key

    def put_immutable(self, src: Path, sha256: str) -> str:
        src = Path(src)
        if not src.is_file():
            raise ObjectNotFound(f"Source file not found: {src}")
        digest = sha256.strip().lower()
        actual = sha256_file(src)
        if actual != digest:
            raise ObjectHashMismatch(
                f"Source hash mismatch: expected={digest} actual={actual} path={src}"
            )
        storage_key = storage_key_for_sha256(digest)
        dest = self._path(storage_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            existing = sha256_file(dest)
            if existing != digest:
                raise ObjectCorruptError(
                    f"Corrupt or colliding blob at {dest}: expected={digest} actual={existing}"
                )
            return storage_key

        fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), prefix=f".{digest}.")
        tmp_path = Path(tmp_name)
        try:
            os.close(fd)
            shutil.copyfile(src, tmp_path)
            written = sha256_file(tmp_path)
            if written != digest:
                raise ObjectHashMismatch(
                    f"Post-copy hash mismatch: expected={digest} actual={written}"
                )
            os.replace(tmp_path, dest)
        except Exception:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return storage_key

    def get(self, storage_key: str, *, expected_sha256: str | None = None) -> bytes:
        path = self._path(storage_key)
        if not path.is_file():
            raise ObjectNotFound(storage_key)
        data = path.read_bytes()
        actual = sha256_bytes(data)
        expect = (expected_sha256 or _sha256_from_key(storage_key) or "").strip().lower()
        if expect and actual != expect:
            raise ObjectCorruptError(
                f"Corrupt blob at {storage_key}: expected={expect} actual={actual}"
            )
        return data

    def exists(self, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    def open_path(self, storage_key: str) -> Path:
        """Local path for reading when available."""
        path = self._path(storage_key)
        if not path.is_file():
            raise ObjectNotFound(storage_key)
        return path


def _sha256_from_key(storage_key: str) -> str | None:
    parts = storage_key.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "sha256" and len(parts[-1]) == 64:
        return parts[-1].lower()
    if len(parts) == 1 and len(parts[0]) == 64:
        return parts[0].lower()
    return None


def _env_flag(name: str) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _should_create_bucket() -> bool:
    return _env_flag("REG_LENS_CREATE_BUCKET") or _env_flag("OBJECT_STORE_CREATE_BUCKET")


def _map_s3_client_error(exc: BaseException, *, action: str) -> ObjectStoreError:
    """Map boto3 ClientError codes to typed errors. Never treat all errors as not-found."""
    response = getattr(exc, "response", None) or {}
    error = response.get("Error") or {}
    code = str(error.get("Code") or "")
    http_status = (response.get("ResponseMetadata") or {}).get("HTTPStatusCode")
    message = str(error.get("Message") or exc)

    not_found_codes = {
        "404",
        "NoSuchKey",
        "NotFound",
        "NoSuchBucket",
        "404 Not Found",
    }
    auth_codes = {
        "InvalidAccessKeyId",
        "SignatureDoesNotMatch",
        "ExpiredToken",
        "InvalidToken",
        "AuthFailure",
        "InvalidClientTokenId",
        "UnrecognizedClientException",
    }
    permission_codes = {
        "AccessDenied",
        "AllAccessDisabled",
        "AccessDeniedException",
        "UnauthorizedOperation",
    }

    if code in not_found_codes or http_status == 404:
        return ObjectNotFound(f"{action}: {message} (code={code})")
    if code in auth_codes or http_status == 401:
        return ObjectAuthError(f"{action}: {message} (code={code})")
    if code in permission_codes or http_status == 403:
        return ObjectPermissionError(f"{action}: {message} (code={code})")
    return ObjectStoreError(f"{action}: {message} (code={code or http_status})")


class S3ObjectStore:
    """Optional MinIO/S3 backend. Requires boto3 (optional dependency)."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str | None = None,
        create_bucket: bool | None = None,
    ):
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError
        except ImportError as exc:  # pragma: no cover - optional dep
            raise ObjectStoreError(
                "S3ObjectStore requires boto3; install via "
                "services/worker/requirements-s3.txt or pip install boto3"
            ) from exc

        self.bucket = bucket
        self._ClientError = ClientError
        self._BotoCoreError = BotoCoreError
        self._EndpointConnectionError = EndpointConnectionError
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name or os.environ.get("AWS_REGION") or "us-east-1",
        )
        if create_bucket is None:
            create_bucket = _should_create_bucket()
        self._ensure_bucket(create=create_bucket)

    def _ensure_bucket(self, *, create: bool) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return
        except self._EndpointConnectionError as exc:
            raise ObjectNetworkError(f"head_bucket({self.bucket}): {exc}") from exc
        except self._ClientError as exc:
            mapped = _map_s3_client_error(exc, action=f"head_bucket({self.bucket})")
            if isinstance(mapped, ObjectNotFound) and create:
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    return
                except self._EndpointConnectionError as net_exc:
                    raise ObjectNetworkError(
                        f"create_bucket({self.bucket}): {net_exc}"
                    ) from net_exc
                except self._ClientError as create_exc:
                    raise _map_s3_client_error(
                        create_exc, action=f"create_bucket({self.bucket})"
                    ) from create_exc
            if isinstance(mapped, ObjectNotFound):
                raise ObjectStoreError(
                    f"Bucket {self.bucket!r} does not exist; set REG_LENS_CREATE_BUCKET=1 "
                    "or OBJECT_STORE_CREATE_BUCKET=1 to allow auto-create (dev only)"
                ) from exc
            raise mapped from exc
        except self._BotoCoreError as exc:
            raise ObjectNetworkError(f"head_bucket({self.bucket}): {exc}") from exc

    def put_immutable(self, src: Path, sha256: str) -> str:
        src = Path(src)
        if not src.is_file():
            raise ObjectNotFound(f"Source file not found: {src}")
        digest = sha256.strip().lower()
        actual = sha256_file(src)
        if actual != digest:
            raise ObjectHashMismatch(
                f"Source hash mismatch: expected={digest} actual={actual} path={src}"
            )
        storage_key = storage_key_for_sha256(digest)

        try:
            head = self.client.head_object(Bucket=self.bucket, Key=storage_key)
        except self._EndpointConnectionError as exc:
            raise ObjectNetworkError(f"head_object({storage_key}): {exc}") from exc
        except self._ClientError as exc:
            mapped = _map_s3_client_error(exc, action=f"head_object({storage_key})")
            if not isinstance(mapped, ObjectNotFound):
                raise mapped from exc
            head = None
        except self._BotoCoreError as exc:
            raise ObjectNetworkError(f"head_object({storage_key}): {exc}") from exc

        if head is not None:
            meta = (head.get("Metadata") or {}).get("sha256")
            if meta and meta.lower() != digest:
                raise ObjectCorruptError(
                    f"Corrupt S3 object metadata at {storage_key}: "
                    f"expected={digest} metadata={meta}"
                )
            # Verify remote bytes match content address when object already exists.
            remote = self.get(storage_key, expected_sha256=digest)
            if sha256_bytes(remote) != digest:
                raise ObjectCorruptError(f"Corrupt S3 object at {storage_key}")
            return storage_key

        extra = {"Metadata": {"sha256": digest, "immutable": "true"}}
        try:
            self.client.upload_file(str(src), self.bucket, storage_key, ExtraArgs=extra)
        except self._EndpointConnectionError as exc:
            raise ObjectNetworkError(f"upload_file({storage_key}): {exc}") from exc
        except self._ClientError as exc:
            raise _map_s3_client_error(exc, action=f"upload_file({storage_key})") from exc
        except self._BotoCoreError as exc:
            raise ObjectNetworkError(f"upload_file({storage_key}): {exc}") from exc
        return storage_key

    def get(self, storage_key: str, *, expected_sha256: str | None = None) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
            data = response["Body"].read()
        except self._EndpointConnectionError as exc:
            raise ObjectNetworkError(f"get_object({storage_key}): {exc}") from exc
        except self._ClientError as exc:
            raise _map_s3_client_error(exc, action=f"get_object({storage_key})") from exc
        except self._BotoCoreError as exc:
            raise ObjectNetworkError(f"get_object({storage_key}): {exc}") from exc

        actual = sha256_bytes(data)
        expect = (expected_sha256 or _sha256_from_key(storage_key) or "").strip().lower()
        if expect and actual != expect:
            raise ObjectCorruptError(
                f"Corrupt blob at {storage_key}: expected={expect} actual={actual}"
            )
        return data

    def exists(self, storage_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except self._EndpointConnectionError as exc:
            raise ObjectNetworkError(f"head_object({storage_key}): {exc}") from exc
        except self._ClientError as exc:
            mapped = _map_s3_client_error(exc, action=f"head_object({storage_key})")
            if isinstance(mapped, ObjectNotFound):
                return False
            raise mapped from exc
        except self._BotoCoreError as exc:
            raise ObjectNetworkError(f"head_object({storage_key}): {exc}") from exc


def build_object_store(data_root: Path) -> ObjectStore:
    backend = (os.environ.get("OBJECT_STORE") or "local").strip().lower()
    if backend in {"s3", "minio"}:
        return S3ObjectStore(
            bucket=os.environ.get("S3_BUCKET", "reglens"),
            endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
            access_key=os.environ.get("S3_ACCESS_KEY", "reglens"),
            secret_key=os.environ.get("S3_SECRET_KEY", "reglenssecret"),
            region_name=os.environ.get("AWS_REGION"),
        )
    return LocalObjectStore(Path(data_root) / "objects")
