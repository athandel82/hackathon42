"""The three deterministic agent tools.

Per the component architecture (§3) the LLM is given only three tools. Download,
list, read and parse are collapsed into a single ``scan_repo`` call so the model
spends its turns authoring the index, graph, signal chains and detail files
rather than walking files one by one.

Each ``@tool`` is a thin wrapper over a plain ``*_impl`` function so the core
pipeline (and unit tests) can call the logic directly without going through the
agent loop. The tools read the active :class:`~ingest_agent.workspace.RunContext`
from a context variable, so they stay stateless.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from . import workspace
from .arxml import parse_repo

# strands' @tool turns docstring + type hints into the schema the model sees.
# Fall back to a transparent decorator when strands is unavailable (e.g. unit
# tests that exercise the *_impl functions directly).
try:  # pragma: no cover - import shim
    from strands import tool
except Exception:  # pragma: no cover
    def tool(fn=None, **_kw):
        def wrap(f):
            return f
        return wrap(fn) if callable(fn) else wrap


# --------------------------------------------------------------------------- #
# Implementations (directly callable / unit-testable)
# --------------------------------------------------------------------------- #


def scan_source_impl(src_dir: Path) -> dict:
    """Parse an already-extracted ARXML source tree into the structured model."""
    return parse_repo(Path(src_dir))


def scan_repo_impl(github_url: str, branch: str) -> dict:
    """Download + extract the GitHub tarball into the run's source tree, then
    parse every ``.arxml`` file."""
    ctx = workspace.current()
    root = workspace.download_and_extract(
        github_url, branch, ctx.src_dir, token=_github_token()
    )
    return scan_source_impl(root)


def write_kb_file_impl(rel_path: str, markdown: str) -> str:
    ctx = workspace.current()
    target = (ctx.kb_dir / rel_path).resolve()
    if not str(target).startswith(str(ctx.kb_dir.resolve())):
        raise ValueError(f"rel_path escapes the KB tree: {rel_path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if markdown and not markdown.endswith("\n"):
        markdown += "\n"
    target.write_text(markdown, encoding="utf-8")
    return f"wrote {rel_path} ({len(markdown)} bytes)"


def record_status_impl(repo_id: str, status: str, meta: Optional[dict] = None) -> str:
    ctx = workspace.current()
    ctx.sink.write_status(repo_id, status, meta or {})
    return f"status[{repo_id}] = {status}"


def read_status_impl(repo_id: str) -> Optional[dict]:
    """Return the stored status record for ``repo_id`` (or ``None`` if the repo
    has never been ingested). Used to short-circuit a redundant re-ingest."""
    ctx = workspace.current()
    return ctx.sink.read_status(repo_id)


def _github_token() -> Optional[str]:
    arn = os.environ.get("GITHUB_TOKEN_SECRET_ARN")
    if not arn:
        return None
    import boto3  # lazy

    secret = boto3.client("secretsmanager").get_secret_value(SecretId=arn)
    return secret.get("SecretString")


# --------------------------------------------------------------------------- #
# Tool wrappers (registered with the agent)
# --------------------------------------------------------------------------- #


@tool
def scan_repo(github_url: str, branch: str) -> dict:
    """Fetch an AUTOSAR repository and extract every element from its ARXML.

    Downloads the GitHub tarball for the given branch (no clone), extracts it,
    enumerates all ``.arxml`` files and parses every element deterministically.

    Args:
        github_url: HTTPS URL of the GitHub repository (e.g.
            ``https://github.com/patrikja/autosar``).
        branch: Branch to fetch (e.g. ``master``).

    Returns:
        A dict with:
          - ``source_files``: ``[{file, lines}]`` for each parsed ARXML file.
          - ``stats``: element counts (components, interfaces, platform types,
            systems, communication elements, implementations).
          - ``source_map``: a sorted list of ``{path, uuid, type, file, line}``
            for every significant element — the durable provenance table. Use it
            verbatim for ``_index/source-map.md`` and the Source Ref column of
            ``_index/path-index.md``.
          - ``elements``: classified, source-linked element trees grouped into
            ``components``, ``interfaces``, ``platform_types``, ``systems``,
            ``communication`` and ``implementations``. Each node carries
            ``tag``, ``name``, ``path``, ``uuid``, ``file``, ``line``, scalar
            ``fields``, resolved ``refs`` (``role``/``dest``/``target`` AUTOSAR
            paths) and nested ``children`` (ports, runnables, connectors, ...).
            Every ``line`` is the element's opening-tag line in ``file`` — emit
            it as ``<file>:<line> (<path>)`` for the Source Reference.
    """
    return scan_repo_impl(github_url, branch)


@tool
def write_kb_file(rel_path: str, markdown: str) -> str:
    """Write one Markdown file into the knowledge-base working tree.

    Args:
        rel_path: Path relative to the KB root (e.g. ``_index/path-index.md`` or
            ``components/Door.md``). Parent directories are created as needed.
        markdown: Full Markdown content of the file.

    Returns:
        A short confirmation string. The tree is synced to its final destination
        (S3 or a local directory) when the run finalizes.
    """
    return write_kb_file_impl(rel_path, markdown)


@tool
def record_status(repo_id: str, status: str, meta: Optional[dict] = None) -> str:
    """Update the ingestion status / metadata for a repository.

    Args:
        repo_id: The repository slug for this run.
        status: One of ``PENDING``, ``READY`` or ``FAILED``.
        meta: Optional metadata dict (counts, error message, ...).

    Returns:
        A short confirmation string.
    """
    return record_status_impl(repo_id, status, meta)
