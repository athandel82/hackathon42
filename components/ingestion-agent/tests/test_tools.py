"""Unit tests for the tools + workspace plumbing (no AWS / Bedrock).

These exercise the local sink, the per-run context, and the file-writing /
status / scan tools via their directly-callable ``*_impl`` functions.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ingest_agent import workspace
from ingest_agent.core import Config, slug
from ingest_agent.tools import (
    record_status_impl,
    scan_source_impl,
    write_kb_file_impl,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def run_ctx(tmp_path):
    cfg = Config(mode="local", workdir=tmp_path / "work", out_dir=tmp_path / "out")
    ctx = cfg.bind_run("acme__widgets__main")
    yield ctx
    ctx.cleanup()


def test_slug():
    assert slug("https://github.com/patrikja/autosar", "master") == "patrikja__autosar__master"
    assert slug("https://github.com/patrikja/autosar.git", "main") == "patrikja__autosar__main"


def test_write_kb_file_writes_into_tree(run_ctx):
    msg = write_kb_file_impl("_index/path-index.md", "# Path Index\n")
    assert "_index/path-index.md" in msg
    written = (run_ctx.kb_dir / "_index" / "path-index.md").read_text(encoding="utf-8")
    assert written.startswith("# Path Index")


def test_write_kb_file_rejects_traversal(run_ctx):
    with pytest.raises(ValueError):
        write_kb_file_impl("../escape.md", "nope")


def test_record_status_local_sink(run_ctx, tmp_path):
    record_status_impl("acme__widgets__main", "READY", {"n": 3})
    status = json.loads((tmp_path / "out" / "acme__widgets__main" / "status.json").read_text())
    assert status["status"] == "READY"
    assert status["meta"] == {"n": 3}


def test_finalize_copies_kb_tree(run_ctx, tmp_path):
    write_kb_file_impl("README.md", "# KB\n")
    location = run_ctx.sink.finalize(run_ctx.kb_dir, "acme__widgets__main")
    assert Path(location, "README.md").exists()


def test_scan_source_impl(run_ctx):
    model = scan_source_impl(FIXTURES)
    assert model["stats"]["components"] >= 1
    assert any(c["path"] == "/Demo/Door/Door" for c in model["elements"]["components"])
