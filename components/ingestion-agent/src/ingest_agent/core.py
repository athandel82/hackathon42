"""Shared core: configuration, the ``repo_id`` slug, and ``run_ingest``.

Every entry point (Lambda worker, local CLI) is a thin adapter over
:func:`run_ingest`, so behaviour is identical whether the pipeline runs in
Lambda or on a laptop. The storage mode (``aws`` vs ``local``) is resolved once
by :meth:`Config.from_env` and bound to a per-run working tree + sink.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import workspace
from .tools import record_status_impl

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug(github_url: str, branch: str) -> str:
    """Human-readable, idempotent repo id, e.g. ``patrikja__autosar__master``."""
    s = github_url.strip().removesuffix(".git").rstrip("/")
    s = s.split("github.com/", 1)[-1]
    parts = [p for p in s.split("/") if p][:2]
    tokens = parts + [branch]
    clean = [_SLUG_RE.sub("_", t.lower()).strip("_") for t in tokens]
    return "__".join(c for c in clean if c) or "repo"


@dataclass
class Config:
    """Resolved storage configuration for a run."""

    mode: str                       # "aws" | "local"
    workdir: Path
    out_dir: Optional[Path] = None  # local mode
    bucket: Optional[str] = None    # aws mode
    table: Optional[str] = None     # aws mode
    region: Optional[str] = None

    @classmethod
    def from_env(cls, out_dir: Optional[str] = None) -> "Config":
        workdir = workspace.workdir_root()
        region = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION")
        bucket = os.environ.get("KB_BUCKET")
        table = os.environ.get("REPOS_TABLE")
        # Explicit --out forces local mode; otherwise AWS if both resources set.
        if out_dir is None and bucket and table:
            return cls(mode="aws", workdir=workdir, bucket=bucket,
                       table=table, region=region)
        out = Path(out_dir) if out_dir else Path(os.environ.get("KB_OUT_DIR", "./out"))
        return cls(mode="local", workdir=workdir, out_dir=out, region=region)

    def make_sink(self) -> workspace.Sink:
        if self.mode == "aws":
            return workspace.AwsSink(self.bucket, self.table, self.region)
        return workspace.LocalSink(self.out_dir)

    def bind_run(self, repo_id: str) -> workspace.RunContext:
        ctx = workspace.RunContext(repo_id=repo_id, workdir=self.workdir,
                                   sink=self.make_sink())
        workspace.set_current(ctx)
        return ctx


def run_ingest(github_url: str, branch: str, repo_id: Optional[str] = None,
               cfg: Optional[Config] = None, cleanup: bool = True) -> dict:
    """Generate the knowledge base for ``github_url@branch``.

    Builds the agent, runs the skill procedure to completion, syncs the KB tree
    to the configured sink and records ``READY`` (or ``FAILED`` on error).
    """
    from .agent import build_agent  # lazy: avoids importing Strands too early

    cfg = cfg or Config.from_env()
    repo_id = repo_id or slug(github_url, branch)
    ctx = cfg.bind_run(repo_id)

    record_status_impl(repo_id, "PENDING", {"github_url": github_url, "branch": branch})
    try:
        agent = build_agent()
        agent(
            f"Generate the AUTOSAR ARXML knowledge base for repository "
            f"{github_url} (branch {branch}, repo_id={repo_id}). "
            f"Call scan_repo first, then author the index, relationship graph, "
            f"signal chains and per-element detail files with write_kb_file, "
            f"following the skill exactly."
        )
        location = ctx.sink.finalize(ctx.kb_dir, repo_id)
        record_status_impl(repo_id, "READY", {
            "github_url": github_url, "branch": branch, "location": location,
        })
        return {"repo_id": repo_id, "status": "READY", "location": location}
    except Exception as e:  # noqa: BLE001 - record and re-raise
        record_status_impl(repo_id, "FAILED", {"error": str(e)})
        raise
    finally:
        if cleanup:
            ctx.cleanup()
