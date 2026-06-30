"""KB source abstraction (S3 prefix or local dir) + tiny Markdown parsers.

The Ingestion Agent persists each repo's KB under
``s3://$KB_BUCKET/<repo_id>/kb/`` (or ``<kb_dir>/<repo_id>/kb/`` locally). This
module binds one read-only source per run (published in a ``contextvars`` var so
the ``@tool`` functions stay stateless) and provides minimal regex/section
helpers over the deterministic Markdown tables — not a general Markdown parser.
"""

from __future__ import annotations

import contextvars
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #


class KBSource(ABC):
    """Read-only access to a single repo's KB tree, with an in-run cache."""

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}

    def read(self, rel_path: str) -> str:
        rel_path = rel_path.lstrip("/")
        if rel_path in self._cache:
            return self._cache[rel_path]
        text = self._fetch(rel_path)
        self._cache[rel_path] = text
        return text

    @abstractmethod
    def _fetch(self, rel_path: str) -> str:
        """Fetch ``rel_path`` or raise ``FileNotFoundError``."""


class LocalKBSource(KBSource):
    def __init__(self, kb_dir: Path, repo_id: str) -> None:
        super().__init__()
        self.root = Path(kb_dir) / repo_id / "kb"

    def _fetch(self, rel_path: str) -> str:
        target = (self.root / rel_path).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise FileNotFoundError(f"path escapes KB tree: {rel_path}")
        if not target.is_file():
            raise FileNotFoundError(f"KB file not found: {rel_path}")
        return target.read_text(encoding="utf-8")


class S3KBSource(KBSource):
    def __init__(self, bucket: str, repo_id: str, region: Optional[str] = None) -> None:
        super().__init__()
        import boto3  # lazy

        self.bucket = bucket
        self.prefix = f"{repo_id}/kb/"
        self._s3 = boto3.session.Session(region_name=region).client("s3")

    def _fetch(self, rel_path: str) -> str:
        import botocore.exceptions

        key = self.prefix + rel_path
        try:
            obj = self._s3.get_object(Bucket=self.bucket, Key=key)
        except botocore.exceptions.ClientError as e:  # pragma: no cover - aws path
            raise FileNotFoundError(f"KB file not found: s3://{self.bucket}/{key}") from e
        return obj["Body"].read().decode("utf-8")


_CURRENT: contextvars.ContextVar[Optional[KBSource]] = contextvars.ContextVar(
    "analyze_kb_source", default=None
)


def set_current(source: KBSource) -> None:
    _CURRENT.set(source)


def current() -> KBSource:
    src = _CURRENT.get()
    if src is None:
        raise RuntimeError("No active KB source; call run_analyze().")
    return src


# --------------------------------------------------------------------------- #
# Markdown helpers (deterministic tables, parent §5)
# --------------------------------------------------------------------------- #

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def parse_link(cell: str) -> Optional[Tuple[str, str]]:
    """Return ``(text, target)`` for the first Markdown link in ``cell``."""
    m = _LINK_RE.search(cell)
    return (m.group(1), m.group(2)) if m else None


def table_rows(markdown: str) -> List[List[str]]:
    """Yield non-header cell rows from every Markdown pipe table in ``markdown``."""
    rows: List[List[str]] = []
    for line in markdown.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        # Skip separator rows (---, :---) and obvious header rows handled by caller.
        if all(set(c) <= set(":- ") and c for c in cells):
            continue
        rows.append(cells)
    return rows


def section(markdown: str, heading: str) -> str:
    """Return the body under a ``##``/``###`` heading matching ``heading``
    (case-insensitive substring), up to the next heading of the same or higher
    level. Empty string if not found."""
    lines = markdown.splitlines()
    want = heading.lower()
    start = None
    start_level = 0
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and want in m.group(2).strip().lower():
            start = i + 1
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    out: List[str] = []
    for line in lines[start:]:
        m = re.match(r"^(#{1,6})\s+", line)
        if m and len(m.group(1)) <= start_level:
            break
        out.append(line)
    return "\n".join(out).strip()


def short_name(autosar_path: str) -> str:
    """Last segment of an AUTOSAR path, e.g. ``/Demo/Door/Door`` -> ``Door``."""
    return autosar_path.rstrip("/").rsplit("/", 1)[-1]
