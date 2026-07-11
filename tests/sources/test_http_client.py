from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from reglens_worker.sources.http_client import (
    PdfMagicError,
    RedirectNotAllowedError,
    SafeHttpClient,
    SchemeNotAllowedError,
    SsrfProtectionError,
)


def _policy(**overrides: Any) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "source_id": "test_source",
        "official_hosts": ["localhost"],
        "allowed_path_prefixes": ["/allowed/"],
        "allowed_mime_types": ["application/pdf", "text/html"],
        "max_document_bytes": 128,
        "min_delay_seconds": 0,
        "max_requests_per_run": 5,
        "redirect_policy": "same_host_allowlist",
        "require_user_agent_contact": False,
    }
    policy.update(overrides)
    return policy


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        responses = self.server.responses  # type: ignore[attr-defined]
        status, headers, body = responses[self.path]
        self.server.user_agents.append(self.headers.get("User-Agent"))  # type: ignore[attr-defined]
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)


@contextmanager
def _server(responses: dict[str, tuple[int, dict[str, str], bytes]]) -> Iterator[str]:
    httpd = ThreadingHTTPServer(("localhost", 0), _Handler)
    httpd.responses = responses  # type: ignore[attr-defined]
    httpd.user_agents = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://localhost:{httpd.server_port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=2)


def test_fetch_streams_pdf_from_localhost(tmp_path: Path) -> None:
    with _server(
        {
            "/allowed/doc.pdf": (
                200,
                {"Content-Type": "application/pdf"},
                b"%PDF-1.7\nsynthetic",
            )
        }
    ) as base_url:
        client = SafeHttpClient(_policy(), temp_dir=tmp_path, resolve_dns=False)
        result = client.fetch(f"{base_url}/allowed/doc.pdf")

    try:
        assert result.status_code == 200
        assert result.content_type == "application/pdf"
        assert result.byte_size == len(b"%PDF-1.7\nsynthetic")
        assert result.temp_path.read_bytes().startswith(b"%PDF")
    finally:
        result.temp_path.unlink(missing_ok=True)


def test_rejects_plain_http_for_remote_hosts() -> None:
    client = SafeHttpClient(
        _policy(official_hosts=["example.com"], allowed_path_prefixes=["/allowed/"]),
        resolve_dns=False,
    )
    with pytest.raises(SchemeNotAllowedError):
        client._validate_url("http://example.com/allowed/doc.pdf")


def test_rejects_metadata_ip_even_when_allowlisted() -> None:
    client = SafeHttpClient(
        _policy(official_hosts=["169.254.169.254"], allowed_path_prefixes=["/"]),
        resolve_dns=False,
    )
    with pytest.raises(SsrfProtectionError):
        client._validate_url("https://169.254.169.254/latest/meta-data")


def test_redirect_target_must_remain_on_allowed_path(tmp_path: Path) -> None:
    with _server(
        {
            "/allowed/redirect": (302, {"Location": "/blocked/doc.pdf"}, b""),
            "/blocked/doc.pdf": (200, {"Content-Type": "application/pdf"}, b"%PDF"),
        }
    ) as base_url:
        client = SafeHttpClient(_policy(), temp_dir=tmp_path, resolve_dns=False)
        with pytest.raises(RedirectNotAllowedError):
            client.fetch(f"{base_url}/allowed/redirect")


def test_pdf_content_must_have_pdf_magic(tmp_path: Path) -> None:
    with _server(
        {
            "/allowed/not-pdf.pdf": (
                200,
                {"Content-Type": "application/pdf"},
                b"not actually a pdf",
            )
        }
    ) as base_url:
        client = SafeHttpClient(_policy(), temp_dir=tmp_path, resolve_dns=False)
        with pytest.raises(PdfMagicError):
            client.fetch(f"{base_url}/allowed/not-pdf.pdf")
