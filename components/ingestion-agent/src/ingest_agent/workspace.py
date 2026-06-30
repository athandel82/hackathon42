"""Working-tree model + finalize sinks (local dir or AWS S3/DynamoDB).

The agent works against a local tree under ``$KB_WORKDIR`` (``/tmp`` on Lambda):

    <workdir>/<repo_id>/src/   # extracted ARXML source
    <workdir>/<repo_id>/kb/    # Markdown KB authored by write_kb_file

On finalize the ``kb/`` tree is synced to the configured sink (a local output
directory, or ``s3://$KB_BUCKET/<repo_id>/kb/``). Ingestion status is written
through the same sink (a ``status.json`` file locally, or a DynamoDB item).

A per-run :class:`RunContext` is published in a ``contextvars.ContextVar`` so the
``@tool`` functions stay stateless — they just read the current context.
"""

from __future__ import annotations

import contextvars
import io
import json
import os
import shutil
import tarfile
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Sinks
# --------------------------------------------------------------------------- #


class Sink(ABC):
    """Destination for the finished KB tree and the ingestion status record."""

    @abstractmethod
    def write_status(self, repo_id: str, status: str, meta: dict) -> None: ...

    @abstractmethod
    def finalize(self, kb_dir: Path, repo_id: str) -> str:
        """Publish ``kb_dir`` and return a human-readable location string."""


class LocalSink(Sink):
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = Path(out_dir)

    def _repo_dir(self, repo_id: str) -> Path:
        d = self.out_dir / repo_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def write_status(self, repo_id: str, status: str, meta: dict) -> None:
        d = self._repo_dir(repo_id)
        payload = {
            "repo_id": repo_id,
            "status": status,
            "meta": meta,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        (d / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def finalize(self, kb_dir: Path, repo_id: str) -> str:
        dest = self._repo_dir(repo_id) / "kb"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(kb_dir, dest)
        return str(dest)


class AwsSink(Sink):
    def __init__(self, bucket: str, table: str, region: Optional[str] = None) -> None:
        import boto3  # lazy: keeps boto3 off the local/test path

        self.bucket = bucket
        self.table = table
        session = boto3.session.Session(region_name=region)
        self._s3 = session.client("s3")
        self._ddb = session.resource("dynamodb").Table(table)

    def write_status(self, repo_id: str, status: str, meta: dict) -> None:
        self._ddb.put_item(
            Item={
                "repo_id": repo_id,
                "status": status,
                "meta": meta,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def finalize(self, kb_dir: Path, repo_id: str) -> str:
        kb_dir = Path(kb_dir)
        prefix = f"{repo_id}/kb"
        for path in sorted(kb_dir.rglob("*")):
            if path.is_file():
                key = f"{prefix}/{path.relative_to(kb_dir).as_posix()}"
                self._s3.upload_file(str(path), self.bucket, key)
        return f"s3://{self.bucket}/{prefix}/"


# --------------------------------------------------------------------------- #
# Per-run context
# --------------------------------------------------------------------------- #


@dataclass
class RunContext:
    repo_id: str
    workdir: Path
    sink: Sink
    src_dir: Path = field(init=False)
    kb_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        base = Path(self.workdir) / self.repo_id
        self.src_dir = base / "src"
        self.kb_dir = base / "kb"
        self.src_dir.mkdir(parents=True, exist_ok=True)
        self.kb_dir.mkdir(parents=True, exist_ok=True)

    def cleanup(self) -> None:
        shutil.rmtree(Path(self.workdir) / self.repo_id, ignore_errors=True)


_CURRENT: contextvars.ContextVar[Optional[RunContext]] = contextvars.ContextVar(
    "ingest_run_context", default=None
)


def set_current(ctx: RunContext) -> None:
    _CURRENT.set(ctx)


def current() -> RunContext:
    ctx = _CURRENT.get()
    if ctx is None:
        raise RuntimeError("No active ingest run context; call run_ingest().")
    return ctx


# --------------------------------------------------------------------------- #
# GitHub tarball fetch (no clone)
# --------------------------------------------------------------------------- #


def download_and_extract(github_url: str, branch: str, dest: Path,
                         token: Optional[str] = None) -> Path:
    """Fetch the GitHub tarball for ``<branch>`` and extract it into ``dest``.

    Returns the extracted repository root. No ``git`` binary or clone is needed.
    """
    owner_repo = _owner_repo(github_url)
    tar_url = f"https://github.com/{owner_repo}/archive/refs/heads/{branch}.tar.gz"
    req = urllib.request.Request(tar_url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:  # noqa: S310 (trusted github host)
        data = resp.read()

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        _safe_extract(tar, dest)

    roots = [p for p in dest.iterdir() if p.is_dir()]
    return roots[0] if len(roots) == 1 else dest


def _owner_repo(github_url: str) -> str:
    s = github_url.strip().removesuffix(".git").rstrip("/")
    s = s.split("github.com/", 1)[-1]
    parts = [p for p in s.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Cannot parse owner/repo from URL: {github_url}")
    return f"{parts[0]}/{parts[1]}"


def _safe_extract(tar: tarfile.TarFile, dest: Path) -> None:
    """Guard against path-traversal entries in the tarball."""
    dest = dest.resolve()
    for member in tar.getmembers():
        target = (dest / member.name).resolve()
        if not str(target).startswith(str(dest)):
            raise RuntimeError(f"Unsafe path in tarball: {member.name}")
    tar.extractall(dest)  # noqa: S202 (members validated above)


def workdir_root() -> Path:
    return Path(os.environ.get("KB_WORKDIR", "/tmp"))
