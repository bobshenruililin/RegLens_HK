"""Conservative resource limits for LawTrace ZIP/XML ingestion.

Do not raise limits silently to make a fixture pass; document adjustments.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceLimits:
    # Largest planned official EN archive in this spike is Caps. 301–600 current
    # (~535 MiB compressed). Cap at 600 MiB per download.
    max_download_bytes: int = 600 * 1024 * 1024
    max_archive_entries: int = 50_000
    max_individual_file_bytes: int = 50 * 1024 * 1024
    max_total_uncompressed_bytes: int = 2 * 1024 * 1024 * 1024
    max_compression_ratio: float = 100.0
    max_xml_input_bytes: int = 50 * 1024 * 1024
    max_xml_depth: int = 64
    max_xml_elements: int = 2_000_000
    allowed_member_suffixes: tuple[str, ...] = (".xml", ".xsd", ".pdf", ".txt", ".md")


DEFAULT_LIMITS = ResourceLimits()
