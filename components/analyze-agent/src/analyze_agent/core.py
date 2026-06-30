"""Shared core: configuration + ``run_analyze`` (one structured-output call).

Every entry point (Lambda, CLI) is a thin adapter over :func:`run_analyze`. The
KB source (s3 | local) and cache (ddb | file) are resolved once by
:meth:`Config.from_env`; the rest is identical in cloud and on a laptop.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import kb
from .cache import Cache, DdbCache, FileCache


@dataclass
class Config:
    mode: str                       # "aws" | "local"
    kb_dir: Optional[Path] = None   # local mode
    bucket: Optional[str] = None    # aws mode
    table: Optional[str] = None     # aws mode
    region: Optional[str] = None

    @classmethod
    def from_env(cls, kb_dir: Optional[str] = None) -> "Config":
        region = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION")
        bucket = os.environ.get("KB_BUCKET")
        table = os.environ.get("RESULTS_TABLE")
        if kb_dir is None and bucket and table:
            return cls(mode="aws", bucket=bucket, table=table, region=region)
        out = Path(kb_dir) if kb_dir else Path(os.environ.get("KB_DIR", "./out"))
        return cls(mode="local", kb_dir=out, region=region)

    def make_cache(self) -> Cache:
        if self.mode == "aws":
            return DdbCache(self.table, self.region)
        return FileCache(self.kb_dir)

    def bind_kb_source(self, repo_id: str) -> kb.KBSource:
        if self.mode == "aws":
            source: kb.KBSource = kb.S3KBSource(self.bucket, repo_id, self.region)
        else:
            source = kb.LocalKBSource(self.kb_dir, repo_id)
        kb.set_current(source)
        return source


def run_analyze(repo_id: str, change_request: str,
                cfg: Optional[Config] = None, use_cache: bool = True) -> dict:
    """Answer ``change_request`` against repo ``repo_id``'s KB.

    Returns the result envelope as a plain dict (parent §7). Raises
    ``FileNotFoundError`` if the repo's KB is missing (no ``path-index.md``).
    """
    cfg = cfg or Config.from_env()
    cache = cfg.make_cache()

    if use_cache:
        hit = cache.get(repo_id, change_request)
        if hit is not None:
            return hit

    source = cfg.bind_kb_source(repo_id)
    # Fail fast with a clear error if the KB was never built / not READY.
    source.read("_index/path-index.md")

    from .agent import build_agent
    from .models import ResultEnvelope

    result = build_agent().structured_output(
        ResultEnvelope,
        f'Change request for repo "{repo_id}": {change_request}',
    )
    out = result.model_dump()
    cache.put(repo_id, change_request, out)
    return out
