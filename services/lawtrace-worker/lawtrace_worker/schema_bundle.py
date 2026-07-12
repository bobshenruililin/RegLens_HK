"""Offline XSD bundle acquisition and validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lawtrace_worker.acquire import utc_now_iso

# Official entrypoint documented on HKeL How to Use (Version 1.0, 138 KB).
# Programmatic fetch via /file/get?openfile=hklm redirects to a client-config
# interstitial and does not yield the XSD bytes without interactive browser config.
HKLM_ENTRYPOINT_EXPECTED_SHA256 = "4B0BA06E45F33BF97AC2C11CF9325764E8FCC92DE38E64FBD0ED8ED358DDB3BD"
HKLM_ENTRYPOINT_URL = "https://www.elegislation.gov.hk/file/get?openfile=hklm"
HKLM_HOWTO_URL = "https://www.elegislation.gov.hk/howtouseeleg"


def write_schema_acquisition_failure(dest_dir: Path, detail: dict[str, Any]) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "bundle_status": "incomplete_acquisition_blocked",
        "entrypoint_url": HKLM_ENTRYPOINT_URL,
        "howto_url": HKLM_HOWTO_URL,
        "expected_entrypoint_sha256": HKLM_ENTRYPOINT_EXPECTED_SHA256,
        "expected_entrypoint_size_bytes": 138 * 1024,
        "offline_validation_possible": False,
        "recorded_at": utc_now_iso(),
        "files": [],
        "dependency_graph": {},
        "acquisition_failures": [detail],
        "manual_acquisition_procedure": [
            "Open https://www.elegislation.gov.hk/howtouseeleg in a browser.",
            "Locate Hong Kong Legislation Model (HKLM) Version 1.0 download.",
            "Download the schema package after any official client-config checks complete.",
            "Verify SHA-256 of the entrypoint equals " + HKLM_ENTRYPOINT_EXPECTED_SHA256 + ".",
            "Place all schema files (including include/import closure) under "
            "fixtures/lawtrace/schema/hklm/ and regenerate BUNDLE_MANIFEST.json.",
            "Validate fixtures offline with network disabled.",
        ],
        "notes": (
            "Do not substitute GitHub or unofficial mirrors. "
            "Do not claim XSD validation passed without the official bundle."
        ),
    }
    path = dest_dir / "BUNDLE_MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def try_fetch_hklm_entrypoint(session_path: Path | None = None) -> dict[str, Any]:
    """Attempt non-interactive fetch; record failure without bypassing controls."""
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        HKLM_ENTRYPOINT_URL,
        headers={"User-Agent": "LawTraceHK-FeasibilitySpike/0.1 (research; non-interactive)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — allowlisted official host
            final_url = resp.geturl()
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read(200_000)
    except urllib.error.URLError as exc:
        return {
            "status": "error",
            "error": str(exc),
            "url": HKLM_ENTRYPOINT_URL,
        }
    is_xml = b"<xs:schema" in data[:5000] or b"<schema" in data[:5000]
    is_zip = data[:2] == b"PK"
    if is_xml or is_zip:
        return {
            "status": "ok",
            "final_url": final_url,
            "content_type": content_type,
            "bytes": len(data),
            "sha256": __import__("hashlib").sha256(data).hexdigest().upper(),
        }
    return {
        "status": "blocked_by_client_config",
        "final_url": final_url,
        "content_type": content_type,
        "bytes_received": len(data),
        "sha256_of_response": __import__("hashlib").sha256(data).hexdigest().upper(),
        "error": (
            "Response is HTML client-config interstitial, not XSD/ZIP. "
            "Non-interactive acquisition cannot complete without bypassing controls."
        ),
    }
