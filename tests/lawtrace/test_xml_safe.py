from __future__ import annotations

from pathlib import Path

import pytest
from lawtrace_worker.security.xml_safe import XmlSecurityError, parse_xml_file


def test_rejects_doctype(tmp_path: Path) -> None:
    p = tmp_path / "xxe.xml"
    p.write_text(
        """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>
""",
        encoding="utf-8",
    )
    with pytest.raises(XmlSecurityError):
        parse_xml_file(p)


def test_rejects_external_entity_payload(tmp_path: Path) -> None:
    p = tmp_path / "ext.xml"
    p.write_text(
        """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY ent SYSTEM "http://127.0.0.1:9/xxe">]>
<root>&ent;</root>
""",
        encoding="utf-8",
    )
    with pytest.raises(XmlSecurityError):
        parse_xml_file(p)


def test_rejects_malformed(tmp_path: Path) -> None:
    p = tmp_path / "bad.xml"
    p.write_text("<root><x></root>", encoding="utf-8")
    with pytest.raises(XmlSecurityError, match="xml_parse_failed"):
        parse_xml_file(p)


def test_parses_simple_fixture(tmp_path: Path) -> None:
    p = tmp_path / "ok.xml"
    p.write_text(
        "<lawDoc><main><section id='s1'><num>1</num></section></main></lawDoc>", encoding="utf-8"
    )
    root = parse_xml_file(p)
    assert root.tag.endswith("lawDoc") or root.tag == "lawDoc"
