"""Safe, policy-aware HTTP client for RC3 source sync."""

from __future__ import annotations

import email.utils
import hashlib
import ipaddress
import random
import socket
import tempfile
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .policy import Policy, user_agent_for_policy

_LOCALHOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_PDF_MAGIC = b"%PDF"


class SafeHttpError(RuntimeError):
    """Base class for safe HTTP client failures."""


class UrlPolicyError(SafeHttpError):
    """Raised when a URL violates source policy."""


class SchemeNotAllowedError(UrlPolicyError):
    """Raised when a URL does not use HTTPS outside localhost tests."""


class HostNotAllowedError(UrlPolicyError):
    """Raised when a URL host is not in the source policy allow-list."""


class PathNotAllowedError(UrlPolicyError):
    """Raised when a URL path is outside allowed source prefixes."""


class SsrfProtectionError(UrlPolicyError):
    """Raised when a URL resolves to a private, loopback, or metadata address."""


class RedirectNotAllowedError(UrlPolicyError):
    """Raised when redirect target is disallowed."""


class RequestBudgetExceededError(SafeHttpError):
    """Raised when the per-run request budget is exhausted."""


class HttpStatusError(SafeHttpError):
    """Raised for non-retryable HTTP status errors."""


class RetryExhaustedError(SafeHttpError):
    """Raised when retryable failures exceed max attempts."""


class ContentTypeError(SafeHttpError):
    """Raised when response Content-Type is missing or not allowed."""


class ResponseTooLargeError(SafeHttpError):
    """Raised when a response exceeds the source size limit."""


class PdfMagicError(SafeHttpError):
    """Raised when a PDF response does not start with %PDF."""


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


@dataclass(frozen=True)
class FetchResult:
    """A safely streamed response saved to a temporary path."""

    url: str
    final_url: str
    status_code: int
    content_type: str
    byte_size: int
    sha256: str
    temp_path: Path
    retry_count: int
    redirect_count: int


@dataclass(frozen=True)
class _RetryableFailure:
    message: str
    retry_after_seconds: float | None = None


class SafeHttpClient:
    """HTTP client that enforces source policy before and during fetches."""

    def __init__(
        self,
        policy: Policy,
        *,
        temp_dir: str | Path | None = None,
        opener: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        max_attempts: int = 3,
        backoff_base_seconds: float = 0.5,
        jitter_seconds: float = 0.25,
        resolve_dns: bool = True,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._policy = dict(policy)
        self._allowed_hosts = _normalise_hosts(self._policy["official_hosts"])
        self._path_prefixes = tuple(str(p) for p in self._policy["allowed_path_prefixes"])
        self._allowed_mime_types = {
            _normalise_mime(mime) for mime in self._policy["allowed_mime_types"]
        }
        self._max_document_bytes = int(self._policy["max_document_bytes"])
        self._min_delay_seconds = float(self._policy.get("min_delay_seconds", 0))
        self._max_requests = int(self._policy["max_requests_per_run"])
        self._redirect_policy = str(self._policy.get("redirect_policy", "deny"))
        self._user_agent = user_agent_for_policy(self._policy)
        self._temp_dir = Path(temp_dir) if temp_dir is not None else None
        self._opener = opener or build_opener(_NoRedirectHandler)
        self._sleep = sleep
        self._monotonic = monotonic
        self._max_attempts = max(1, max_attempts)
        self._backoff_base_seconds = max(0.0, backoff_base_seconds)
        self._jitter_seconds = max(0.0, jitter_seconds)
        self._resolve_dns = resolve_dns
        self._timeout_seconds = timeout_seconds
        self._lock = threading.Lock()
        self._last_request_at: float | None = None
        self._request_count = 0

    @property
    def request_count(self) -> int:
        """Return the number of HTTP requests consumed from the budget."""
        return self._request_count

    def fetch(self, url: str, *, purpose: str = "document") -> FetchResult:
        """Fetch `url`, following only policy-approved redirects."""
        _ = purpose
        with self._lock:
            retry_count = 0
            last_failure: _RetryableFailure | None = None
            for attempt in range(self._max_attempts):
                try:
                    return self._fetch_once_with_redirects(url, retry_count=retry_count)
                except _RetryableSafeHttpError as exc:
                    last_failure = _RetryableFailure(str(exc), exc.retry_after_seconds)
                    if attempt == self._max_attempts - 1:
                        break
                    self._sleep(self._retry_delay(attempt, last_failure.retry_after_seconds))
                    retry_count += 1

            message = last_failure.message if last_failure else "retry attempts exhausted"
            raise RetryExhaustedError(message)

    def _fetch_once_with_redirects(self, url: str, *, retry_count: int) -> FetchResult:
        current_url = url
        redirect_count = 0
        while True:
            self._validate_url(current_url)
            self._consume_budget()
            self._respect_min_delay()
            try:
                request = Request(current_url, headers={"User-Agent": self._user_agent})
                response = self._opener.open(request, timeout=self._timeout_seconds)
            except HTTPError as exc:
                if 300 <= exc.code < 400:
                    location = exc.headers.get("Location")
                    if not location:
                        raise HttpStatusError(
                            f"redirect status {exc.code} without Location"
                        ) from exc
                    if self._redirect_policy == "deny":
                        raise RedirectNotAllowedError(
                            "redirects are denied by source policy"
                        ) from exc
                    redirect_count += 1
                    if redirect_count > 5:
                        raise RedirectNotAllowedError("too many redirects") from exc
                    current_url = urljoin(current_url, location)
                    self._validate_redirect(current_url)
                    continue
                if exc.code in {429, 500, 502, 503, 504}:
                    raise _RetryableSafeHttpError(
                        f"retryable HTTP status {exc.code}",
                        retry_after_seconds=_parse_retry_after(exc.headers.get("Retry-After")),
                    ) from exc
                raise HttpStatusError(f"HTTP status {exc.code}") from exc
            except URLError as exc:
                raise _RetryableSafeHttpError(f"network error: {exc.reason}") from exc
            finally:
                self._last_request_at = self._monotonic()

            with response:
                status_code = int(getattr(response, "status", response.getcode()))
                return self._stream_response(
                    response,
                    requested_url=url,
                    final_url=response.geturl() or current_url,
                    status_code=status_code,
                    retry_count=retry_count,
                    redirect_count=redirect_count,
                )

    def _stream_response(
        self,
        response: Any,
        *,
        requested_url: str,
        final_url: str,
        status_code: int,
        retry_count: int,
        redirect_count: int,
    ) -> FetchResult:
        content_type = _normalise_mime(response.headers.get("Content-Type", ""))
        if content_type not in self._allowed_mime_types:
            raise ContentTypeError(f"Content-Type is not allowed: {content_type or '<missing>'}")

        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > self._max_document_bytes:
            raise ResponseTooLargeError("Content-Length exceeds source policy limit")

        temp = tempfile.NamedTemporaryFile(
            prefix="reglens-source-",
            suffix=".tmp",
            dir=self._temp_dir,
            delete=False,
        )
        path = Path(temp.name)
        digest = hashlib.sha256()
        total = 0
        first_bytes = b""
        try:
            with temp:
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > self._max_document_bytes:
                        raise ResponseTooLargeError("response exceeds source policy limit")
                    if len(first_bytes) < len(_PDF_MAGIC):
                        needed = len(_PDF_MAGIC) - len(first_bytes)
                        first_bytes += chunk[:needed]
                    digest.update(chunk)
                    temp.write(chunk)

            if content_type == "application/pdf" and not first_bytes.startswith(_PDF_MAGIC):
                raise PdfMagicError("application/pdf response did not start with %PDF")

            return FetchResult(
                url=requested_url,
                final_url=final_url,
                status_code=status_code,
                content_type=content_type,
                byte_size=total,
                sha256=digest.hexdigest(),
                temp_path=path,
                retry_count=retry_count,
                redirect_count=redirect_count,
            )
        except Exception:
            path.unlink(missing_ok=True)
            raise

    def _validate_redirect(self, url: str) -> None:
        try:
            self._validate_url(url)
        except UrlPolicyError as exc:
            raise RedirectNotAllowedError(str(exc)) from exc

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").strip().lower().rstrip(".")
        if not host:
            raise HostNotAllowedError("URL host is required")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and host in _LOCALHOSTS):
            raise SchemeNotAllowedError("HTTPS is required outside localhost tests")
        if host not in self._allowed_hosts:
            raise HostNotAllowedError(f"host is not in source allow-list: {host}")

        path = parsed.path or "/"
        if not any(path.startswith(prefix) for prefix in self._path_prefixes):
            raise PathNotAllowedError(f"path is outside source allow-list: {path}")

        if host not in _LOCALHOSTS:
            _reject_private_addresses(host, resolve_dns=self._resolve_dns)

    def _consume_budget(self) -> None:
        if self._request_count >= self._max_requests:
            raise RequestBudgetExceededError("source request budget exhausted")
        self._request_count += 1

    def _respect_min_delay(self) -> None:
        if self._last_request_at is None or self._min_delay_seconds <= 0:
            return
        elapsed = self._monotonic() - self._last_request_at
        remaining = self._min_delay_seconds - elapsed
        if remaining > 0:
            self._sleep(remaining)

    def _retry_delay(self, attempt: int, retry_after_seconds: float | None) -> float:
        if retry_after_seconds is not None:
            return max(0.0, min(retry_after_seconds, 60.0))
        exponential = self._backoff_base_seconds * (2**attempt)
        jitter = random.uniform(0, self._jitter_seconds) if self._jitter_seconds else 0.0
        return exponential + jitter


class _RetryableSafeHttpError(SafeHttpError):
    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def _normalise_hosts(hosts: Iterable[str]) -> frozenset[str]:
    return frozenset(str(host).strip().lower().rstrip(".") for host in hosts if str(host).strip())


def _normalise_mime(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    stripped = value.strip()
    if stripped.isdigit():
        return float(stripped)
    try:
        parsed = email.utils.parsedate_to_datetime(stripped)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return max(0.0, (parsed - datetime.now(UTC)).total_seconds())


def _reject_private_addresses(host: str, *, resolve_dns: bool) -> None:
    addresses = _addresses_for_host(host, resolve_dns=resolve_dns)
    for address in addresses:
        if _is_blocked_address(address):
            raise SsrfProtectionError(f"host resolves to disallowed address: {address}")


def _addresses_for_host(
    host: str,
    *,
    resolve_dns: bool,
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass

    if not resolve_dns:
        return []

    addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SsrfProtectionError(f"could not resolve host for SSRF checks: {host}") from exc
    for info in infos:
        sockaddr = info[4]
        if sockaddr:
            addresses.add(ipaddress.ip_address(sockaddr[0]))
    return sorted(addresses, key=str)


def _is_blocked_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )
