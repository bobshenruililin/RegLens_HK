"""XXE-safe XML parsing helpers for LawTrace."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml.common import DTDForbidden, EntitiesForbidden, ExternalReferenceForbidden
from defusedxml.ElementTree import parse as defused_parse

from lawtrace_worker.limits import DEFAULT_LIMITS, ResourceLimits

# Prefer defusedxml; also fail closed on oversized inputs before parse.


class XmlSecurityError(ValueError):
    """Raised when XML violates safety policy or cannot be parsed safely."""


def _count_depth(elem: Element, depth: int = 1, limits: ResourceLimits = DEFAULT_LIMITS) -> int:
    if depth > limits.max_xml_depth:
        raise XmlSecurityError(f"xml_depth_exceeded: {depth}")
    max_d = depth
    for child in list(elem):
        max_d = max(max_d, _count_depth(child, depth + 1, limits))
    return max_d


def _count_elements(elem: Element, limits: ResourceLimits = DEFAULT_LIMITS) -> int:
    n = 1
    stack = [elem]
    while stack:
        cur = stack.pop()
        kids = list(cur)
        n += len(kids)
        if n > limits.max_xml_elements:
            raise XmlSecurityError("xml_element_count_exceeded")
        stack.extend(kids)
    return n


def parse_xml_file(path: Path, limits: ResourceLimits = DEFAULT_LIMITS) -> Element:
    """Parse XML from path with external entities/DTD forbidden and size caps."""
    size = path.stat().st_size
    if size > limits.max_xml_input_bytes:
        raise XmlSecurityError(f"xml_too_large: {size}")
    # Quick reject of DOCTYPE before full parse (defense in depth).
    head = path.read_bytes()[:4096]
    if b"<!DOCTYPE" in head.upper() or b"<!ENTITY" in head.upper():
        # Still attempt defused parse which should forbid; treat as security error.
        raise XmlSecurityError("doctype_or_entity_declaration_forbidden")
    try:
        tree = defused_parse(str(path), forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except (DTDForbidden, EntitiesForbidden, ExternalReferenceForbidden) as exc:
        raise XmlSecurityError(f"forbidden_xml_construct: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — surface as safe failure
        raise XmlSecurityError(f"xml_parse_failed: {exc}") from exc
    root = tree.getroot()
    _count_depth(root, limits=limits)
    _count_elements(root, limits=limits)
    return root


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def iter_elements(root: Element) -> Any:
    yield root
    for el in root.iter():
        if el is not root:
            yield el
