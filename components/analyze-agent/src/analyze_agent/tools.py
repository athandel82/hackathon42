"""The four read-only KB navigation tools (§3).

Each ``@tool`` is a thin wrapper over a plain ``*_impl`` function so the logic is
directly unit-testable without the agent loop. Tools read the active KB source
from a context variable (set by ``run_analyze``) and never mutate the KB or call
the model. Parsing is minimal section/table slicing over the deterministic
Markdown the Ingestion Agent emits (parent §5).
"""

from __future__ import annotations

from typing import List, Optional

from . import kb

# strands' @tool turns docstring + type hints into the schema the model sees.
# Fall back to a transparent decorator when strands is unavailable (unit tests).
try:  # pragma: no cover - import shim
    from strands import tool
except Exception:  # pragma: no cover
    def tool(fn=None, **_kw):
        def wrap(f):
            return f
        return wrap(fn) if callable(fn) else wrap


PATH_INDEX = "_index/path-index.md"
COMPONENTS_INDEX = "_index/components.md"
INTERFACES_INDEX = "_index/interfaces.md"
DEP_GRAPH = "_index/dependency-graph.md"
SIGNAL_CHAINS = "_index/signal-chains.md"


def _norm_kb_path(target: str) -> str:
    """Normalize a Markdown link target (``../components/Door.md``) to a
    KB-relative path (``components/Door.md``)."""
    parts = [p for p in target.split("/") if p not in ("", ".", "..")]
    return "/".join(parts)


def _matches(ref: str, path: str) -> int:
    """Match score of ``ref`` against an AUTOSAR ``path`` (higher = better)."""
    ref_l = ref.strip().lower()
    path_l = path.lower()
    name = kb.short_name(path).lower()
    if ref_l == path_l:
        return 100
    if ref_l == name:
        return 80
    # token overlap on the last segment (handles "rear-door" ~ "Door").
    tokens = [t for t in ref_l.replace("-", " ").replace("_", " ").split() if t]
    if any(t in name or name in t for t in tokens):
        return 50
    if ref_l in path_l:
        return 30
    return 0


# --------------------------------------------------------------------------- #
# Implementations
# --------------------------------------------------------------------------- #


def resolve_path_impl(ref: str) -> dict:
    src = kb.current()
    candidates: List[dict] = []
    try:
        rows = kb.table_rows(src.read(PATH_INDEX))
    except FileNotFoundError as e:
        return {"query": ref, "error": str(e), "matches": []}

    for cells in rows:
        if not cells or not cells[0].startswith("/"):
            continue
        path = cells[0]
        etype = cells[1] if len(cells) > 1 else ""
        file_link = kb.parse_link(cells[2]) if len(cells) > 2 else None
        detail = _norm_kb_path(file_link[1]) if file_link else ""
        score = _matches(ref, path)
        if score:
            candidates.append({"path": path, "type": etype, "file": detail, "_score": score})

    candidates.sort(key=lambda c: c["_score"], reverse=True)
    matches = [{k: v for k, v in c.items() if k != "_score"} for c in candidates[:10]]
    return {"query": ref, "resolved": matches[0] if matches else None, "matches": matches}


def blast_radius_impl(component: str) -> dict:
    src = kb.current()
    try:
        md = src.read(DEP_GRAPH)
    except FileNotFoundError as e:
        return {"target": component, "error": str(e), "depended_on_by": []}

    reverse = kb.section(md, "Reverse Dependencies")
    best: Optional[dict] = None
    best_score = 0
    for cells in kb.table_rows(reverse):
        if len(cells) < 2:
            continue
        link = kb.parse_link(cells[0])
        path = link[0] if link else cells[0]
        if not path.startswith("/"):
            continue
        score = _matches(component, path)
        if score > best_score:
            dependents = [
                d.strip() for d in cells[1].split(",")
                if d.strip() and not d.strip().startswith("_None_") and "None" not in d
            ]
            best = {"target": path, "depended_on_by": dependents}
            best_score = score

    target_name = kb.short_name(best["target"]).lower() if best else kb.short_name(component).lower()
    notes = [
        ln.strip().lstrip("-").strip()
        for ln in kb.section(md, "Blast-Radius Quick Reference").splitlines()
        if ln.strip().startswith("-") and target_name in ln.lower()
    ]
    if best is None:
        return {"target": component, "depended_on_by": [],
                "note": "target not found in reverse-dependency table", "notes": notes}
    best["notes"] = notes
    return best


def trace_signals_impl(element: str) -> dict:
    src = kb.current()
    try:
        md = src.read(SIGNAL_CHAINS)
    except FileNotFoundError as e:
        return {"element": element, "error": str(e), "chains": []}

    name = kb.short_name(element).lower()
    chains: List[dict] = []
    current_title: Optional[str] = None
    buf: List[str] = []

    def flush() -> None:
        if current_title is None:
            return
        body = "\n".join(buf).strip()
        if name and name in (current_title + "\n" + body).lower():
            endpoints = next(
                (ln.split("**Endpoints:**", 1)[1].strip()
                 for ln in body.splitlines() if "**Endpoints:**" in ln), "")
            chains.append({"title": current_title, "endpoints": endpoints, "body": body})

    for line in md.splitlines():
        m = line.strip()
        if m.startswith("## "):
            flush()
            current_title = m[3:].strip()
            buf = []
        else:
            buf.append(line)
    flush()
    return {"element": element, "chains": chains, "count": len(chains)}


def kb_read_impl(path: str) -> str:
    try:
        return kb.current().read(path)
    except FileNotFoundError as e:
        return f"ERROR: {e}"


# --------------------------------------------------------------------------- #
# Tool wrappers
# --------------------------------------------------------------------------- #


@tool
def resolve_path(ref: str) -> dict:
    """Resolve an AUTOSAR path or element name to its KB detail file.

    Looks the reference up in ``_index/path-index.md`` (with fuzzy name matching
    for free-text targets, e.g. "rear-door" → Door).

    Args:
        ref: An AUTOSAR path (``/Demo/Door/Door``) or a name fragment (``Door``).

    Returns:
        ``{query, resolved, matches}`` where each match is
        ``{path, type, file}`` and ``file`` is the KB-relative detail file
        (e.g. ``components/Door.md``). ``resolved`` is the best match or null.
    """
    return resolve_path_impl(ref)


@tool
def blast_radius(component: str) -> dict:
    """List the components that break if ``component`` changes or is removed.

    Reads the **Reverse Dependencies** section of
    ``_index/dependency-graph.md`` (precomputed at ingestion — never re-derived).

    Args:
        component: AUTOSAR path or name of the target component.

    Returns:
        ``{target, depended_on_by, notes}`` — the dependents and any matching
        Blast-Radius Quick Reference bullets.
    """
    return blast_radius_impl(component)


@tool
def trace_signals(element: str) -> dict:
    """Find the signal/data-flow chains an element participates in.

    Reads ``_index/signal-chains.md`` and returns every chain whose hops mention
    the element, so you can see which signals/PDUs it feeds and where a cut
    severs the chain.

    Args:
        element: AUTOSAR path or name of the element (component, port, signal...).

    Returns:
        ``{element, chains, count}`` where each chain is
        ``{title, endpoints, body}``.
    """
    return trace_signals_impl(element)


@tool
def kb_read(path: str) -> str:
    """Read any Markdown file from the knowledge base.

    Args:
        path: KB-relative path, e.g. ``components/Door.md`` or
            ``_index/stats.md``.

    Returns:
        The raw Markdown content (or an ``ERROR: ...`` string if not found).
    """
    return kb_read_impl(path)
