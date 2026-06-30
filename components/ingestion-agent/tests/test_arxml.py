"""Unit tests for the deterministic ARXML parser (no AWS / Bedrock)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ingest_agent.arxml import LineIndex, parse_repo

FIXTURES = Path(__file__).parent / "fixtures"
# The demo ARXML submodule, relative to the component root.
DEMO_ARXML = (
    Path(__file__).resolve().parents[3]
    / "knowledge_base" / "input" / "autosar" / "ARXML"
)


def test_line_index_points_at_opening_tag():
    text = (FIXTURES / "mini.arxml").read_text(encoding="utf-8")
    idx = LineIndex()
    idx.index_file("mini.arxml", text)

    el = idx.by_path["/Demo/Door/Door"]
    assert el.tag == "APPLICATION-SW-COMPONENT-TYPE"
    assert el.uuid == "2dbc5fd9-e3c1-3151-a0e4-b723a660be32"
    # The recorded line must contain the element's opening tag.
    line = text.splitlines()[el.line - 1]
    assert "APPLICATION-SW-COMPONENT-TYPE" in line


def test_parse_repo_classification():
    model = parse_repo(FIXTURES)
    elements = model["elements"]

    comp_paths = [c["path"] for c in elements["components"]]
    assert "/Demo/Door/Door" in comp_paths

    iface_paths = [i["path"] for i in elements["interfaces"]]
    assert "/Demo/Interfaces/DoorStatus" in iface_paths

    plat_paths = [p["path"] for p in elements["platform_types"]]
    assert "/ArcCore/Platform/ImplementationDataTypes/boolean" in plat_paths


def test_parse_repo_component_detail():
    model = parse_repo(FIXTURES)
    door = next(c for c in model["elements"]["components"] if c["path"] == "/Demo/Door/Door")

    assert door["tag"] == "APPLICATION-SW-COMPONENT-TYPE"
    assert door["line"] is not None
    # Port is captured as a child with its resolved interface reference.
    status = next(ch for ch in door["children"] if ch["name"] == "Status")
    assert status["tag"] == "P-PORT-PROTOTYPE"
    tref = next(r for r in status["refs"] if r["role"] == "PROVIDED-INTERFACE-TREF")
    assert tref["target"] == "/Demo/Interfaces/DoorStatus"
    assert tref["dest"] == "SENDER-RECEIVER-INTERFACE"


def test_source_map_is_sorted_and_significant():
    model = parse_repo(FIXTURES)
    smap = model["source_map"]
    # Sorted by (file, path):
    assert smap == sorted(smap, key=lambda r: (r["file"], r["path"]))
    # Every entry has an integer line.
    assert all(isinstance(r["line"], int) for r in smap)


@pytest.mark.skipif(not DEMO_ARXML.exists(), reason="demo ARXML submodule not present")
def test_demo_repo_known_lines():
    model = parse_repo(DEMO_ARXML)
    by_path = {r["path"]: r for r in model["source_map"]}

    # Cross-checked against sample_4_skill/_index/source-map.md.
    assert by_path["/Demo/Door/Door"]["line"] == 10
    assert by_path["/Demo/Door/Door"]["file"] == "EcuExtract.arxml"
    assert by_path["/Demo/Interfaces/DoorCommands"]["line"] == 348
    assert by_path["/ArcCore/Platform/BaseTypes/boolean"]["line"] == 14

    stats = model["stats"]
    assert stats["components"] >= 4   # Door, DoorControl, IoHwAb, EDC
    assert stats["systems"] == 1
