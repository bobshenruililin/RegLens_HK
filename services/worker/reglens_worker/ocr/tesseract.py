from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from reglens_worker.hashutil import sha256_text

OCR_PROVIDER_ENV = "OCR_PROVIDER"
DEFAULT_PROVIDER = "none"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_PAGES = 25


class OCRConfigurationError(RuntimeError):
    """Raised when an explicitly requested OCR provider is unavailable or unsafe."""


class OCRExecutionError(RuntimeError):
    """Raised when a local OCR process fails."""


@dataclass(frozen=True)
class OCRSpan:
    page_no: int
    span_type: str
    text: str
    char_start: int | None
    char_end: int | None
    text_hash: str
    source_page_no: int
    provider: str
    quality: str = "ocr"


@dataclass(frozen=True)
class OCRReport:
    provider: str
    spans: tuple[OCRSpan, ...]
    warnings: tuple[str, ...] = ()


def ocr_document(
    path: Path | str,
    *,
    provider: str | None = None,
    timeout_seconds: int | None = None,
    max_pages: int | None = None,
    page_count: int | None = None,
    tesseract_bin: str | None = None,
) -> OCRReport:
    """Run optional local OCR and return separate OCR spans.

    The default provider is ``none`` and returns no spans. OCR never mutates or
    replaces source text spans; callers decide whether and how to use OCR spans.
    """

    selected = (provider or os.environ.get(OCR_PROVIDER_ENV, DEFAULT_PROVIDER)).strip().lower()
    if selected not in {"none", "tesseract"}:
        raise OCRConfigurationError(f"unsupported OCR_PROVIDER: {selected!r}")

    if selected == "none":
        return OCRReport(provider="none", spans=(), warnings=("ocr_disabled",))

    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(str(input_path))

    limit = (
        max_pages
        if max_pages is not None
        else _env_int("REGLENS_OCR_MAX_PAGES", DEFAULT_MAX_PAGES)
    )
    if page_count is not None and page_count > limit:
        raise OCRConfigurationError(f"OCR page count {page_count} exceeds max page limit {limit}")

    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else _env_int("REGLENS_OCR_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    )
    binary = tesseract_bin or os.environ.get("TESSERACT_BIN") or "tesseract"
    executable = shutil.which(binary)
    if executable is None:
        raise OCRConfigurationError(
            "OCR_PROVIDER=tesseract requires the tesseract binary on PATH "
            "or TESSERACT_BIN to point to it"
        )

    cmd = [executable, str(input_path), "stdout"]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise OCRExecutionError(f"tesseract timed out after {timeout} seconds") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        detail = f": {stderr[:300]}" if stderr else ""
        raise OCRExecutionError(f"tesseract failed with exit code {completed.returncode}{detail}")

    spans = _spans_from_stdout(completed.stdout, provider="tesseract", max_pages=limit)
    return OCRReport(provider="tesseract", spans=spans)


def _spans_from_stdout(stdout: str, *, provider: str, max_pages: int) -> tuple[OCRSpan, ...]:
    pages = stdout.split("\f") if "\f" in stdout else [stdout]
    if len(pages) > max_pages:
        raise OCRConfigurationError(
            f"OCR output page count {len(pages)} exceeds max page limit {max_pages}"
        )

    spans: list[OCRSpan] = []
    for page_no, raw in enumerate(pages, start=1):
        text = _normalize_ws(raw)
        if not text:
            continue
        spans.append(
            OCRSpan(
                page_no=page_no,
                span_type="ocr_page",
                text=text,
                char_start=0,
                char_end=len(text),
                text_hash=sha256_text(text),
                source_page_no=page_no,
                provider=provider,
            )
        )
    return tuple(spans)


def _normalize_ws(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise OCRConfigurationError(f"{name} must be an integer") from exc
    if value < 1:
        raise OCRConfigurationError(f"{name} must be >= 1")
    return value
