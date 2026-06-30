"""Unit tests for the read-only KB navigation tools (no AWS / Bedrock)."""

from __future__ import annotations

from pathlib import Path

import pytest

from analyze_agent import kb
from analyze_agent.core import Config
from analyze_agent.tools import (
    blast_radius_impl,
    kb_read_impl,
    resolve_path_impl,
    trace_signals_impl,
)

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ID = "demo__repo__main"


@pytest.fixture(autouse=True)
def bound_kb():
    cfg = Config(mode="local", kb_dir=FIXTURES)
    cfg.bind_kb_source(REPO_ID)
    yield


def test_resolve_exact_path():
    res = resolve_path_impl("/Demo/Door/Door")
    assert res["resolved"]["path"] == "/Demo/Door/Door"
    assert res["resolved"]["type"] == "APPLICATION-SW-COMPONENT-TYPE"
    assert res["resolved"]["file"] == "components/Door.md"


def test_resolve_fuzzy_name():
    res = resolve_path_impl("rear-door")
    paths = [m["path"] for m in res["matches"]]
    assert "/Demo/Door/Door" in paths


def test_blast_radius_door():
    res = blast_radius_impl("Door")
    assert res["target"] == "/Demo/Door/Door"
    assert set(res["depended_on_by"]) == {"DoorControl", "EDC"}
    # Quick-reference note for Door is surfaced.
    assert any("door" in n.lower() for n in res["notes"])


def test_blast_radius_by_path():
    res = blast_radius_impl("/Demo/Services/IoHwAb/IoHwAb")
    assert "DoorControl" in res["depended_on_by"]


def test_trace_signals_door():
    res = trace_signals_impl("Door")
    assert res["count"] >= 4  # four CombinedStatus chains mention Door instances
    titles = " ".join(c["title"] for c in res["chains"]).lower()
    assert "combined" in titles
    assert any(c["endpoints"] for c in res["chains"])


def test_kb_read_and_missing():
    md = kb_read_impl("components/Door.md")
    assert md.startswith("# Door")
    assert kb_read_impl("does/not/exist.md").startswith("ERROR:")


def test_section_and_table_helpers():
    md = kb.current().read("_index/dependency-graph.md")
    reverse = kb.section(md, "Reverse Dependencies")
    assert "Depended On By" in reverse
    # The forward-deps table must not leak into the reverse section.
    assert "Forward Dependencies" not in reverse
