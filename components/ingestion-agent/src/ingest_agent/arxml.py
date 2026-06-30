"""Deterministic AUTOSAR ARXML extraction (standard library only).

This module does *all* the parsing work for the ingestion agent. The LLM never
reads raw XML; it only sequences tool calls and authors Markdown from the
structured, source-linked data produced here.

Two passes over each ``.arxml`` file:

1. :class:`LineIndex` — a cheap regex/line scan that records, for every typed
   element (one that owns a ``<SHORT-NAME>``), the *opening-tag line* and the
   element's full SHORT-NAME path (``sn_path``) and ``UUID``. This is the exact
   provenance the v3 skill needs (``file:line (sn_path)``) and mirrors the logic
   in the generated ``validate_kb.py`` so the two always agree.
2. :func:`parse_tree` — an ``ElementTree`` walk that builds a structured,
   classified model (components, interfaces, platform types, systems,
   communication, implementations) with ports, runnables, connectors, mappings
   and cross-references resolved to AUTOSAR paths. Line numbers are joined in
   from the :class:`LineIndex` by ``sn_path`` (falling back to ``UUID``).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- #
# Element classification (mirrors skill.md "Element Classification")
# --------------------------------------------------------------------------- #

COMPONENT_TAGS = {
    "APPLICATION-SW-COMPONENT-TYPE",
    "SERVICE-SW-COMPONENT-TYPE",
    "COMPOSITION-SW-COMPONENT-TYPE",
    "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
    "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE",
    "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
    "NV-BLOCK-SW-COMPONENT-TYPE",
}

INTERFACE_TAGS = {
    "SENDER-RECEIVER-INTERFACE",
    "CLIENT-SERVER-INTERFACE",
    "MODE-SWITCH-INTERFACE",
    "NV-DATA-INTERFACE",
    "PARAMETER-INTERFACE",
    "TRIGGER-INTERFACE",
}

PLATFORM_TAGS = {
    "SW-BASE-TYPE",
    "IMPLEMENTATION-DATA-TYPE",
    "COMPU-METHOD",
    "APPLICATION-PRIMITIVE-DATA-TYPE",
    "APPLICATION-RECORD-DATA-TYPE",
}

SYSTEM_TAGS = {"SYSTEM"}

COMMUNICATION_TAGS = {
    "I-SIGNAL",
    "SYSTEM-SIGNAL",
    "I-SIGNAL-I-PDU",
    "I-SIGNAL-GROUP",
    "I-PDU",
    "N-PDU",
    "FRAME",
    "CAN-FRAME",
    "CAN-CLUSTER",
    "ETHERNET-CLUSTER",
    "FLEXRAY-CLUSTER",
}

IMPLEMENTATION_TAGS = {"SWC-IMPLEMENTATION"}

# Top-level element tags that become their own classified record. We do not
# descend past these (their internals are captured inside the record's node).
TOP_LEVEL_TAGS = (
    COMPONENT_TAGS
    | INTERFACE_TAGS
    | PLATFORM_TAGS
    | SYSTEM_TAGS
    | COMMUNICATION_TAGS
    | IMPLEMENTATION_TAGS
)

# Tags that earn a row in source-map.md / path-index.md (curated provenance set).
SIGNIFICANT_TAGS = TOP_LEVEL_TAGS | {
    "P-PORT-PROTOTYPE",
    "R-PORT-PROTOTYPE",
    "PR-PORT-PROTOTYPE",
    "SWC-INTERNAL-BEHAVIOR",
    "RUNNABLE-ENTITY",
    "SW-COMPONENT-PROTOTYPE",
    "ROOT-SW-COMPOSITION-PROTOTYPE",
    "VARIABLE-DATA-PROTOTYPE",
    "PARAMETER-DATA-PROTOTYPE",
    "ARGUMENT-DATA-PROTOTYPE",
    "CLIENT-SERVER-OPERATION",
    "MODE-DECLARATION-GROUP",
}

_NS_RE = re.compile(r"\{[^}]*\}")


def _local(tag: str) -> str:
    """Strip an ``{namespace}`` prefix from an ElementTree tag."""
    return _NS_RE.sub("", tag)


# --------------------------------------------------------------------------- #
# Pass 1 — line / provenance index
# --------------------------------------------------------------------------- #

SHORT_NAME_RE = re.compile(r"<SHORT-NAME>([^<]+)</SHORT-NAME>")
UUID_RE = re.compile(r'UUID="([0-9a-fA-F-]+)"')
TAG_RE = re.compile(r"<(/?)([A-Z][A-Z0-9-]*)\b([^>]*?)(/?)>")


@dataclass
class SourceElement:
    sn_path: str
    uuid: Optional[str]
    tag: str
    file: str
    line: int


class LineIndex:
    """Indexes every typed element by ``sn_path`` and ``UUID`` with its
    opening-tag line. AUTOSAR emits ``<SHORT-NAME>`` as the first child of its
    owning element, so we keep a stack of open elements and, on each SHORT-NAME,
    bind it to the innermost still-unnamed element."""

    def __init__(self) -> None:
        self.by_path: Dict[str, SourceElement] = {}
        self.by_uuid: Dict[str, SourceElement] = {}

    def index_file(self, fname: str, text: str) -> None:
        stack: List[dict] = []
        for idx, line in enumerate(text.splitlines(), start=1):
            for m in TAG_RE.finditer(line):
                closing = m.group(1) == "/"
                tag = m.group(2)
                attrs = m.group(3) or ""
                self_close = m.group(4) == "/"
                if tag == "SHORT-NAME":
                    continue
                if closing:
                    for i in range(len(stack) - 1, -1, -1):
                        if stack[i]["tag"] == tag:
                            del stack[i:]
                            break
                elif not self_close:
                    uuid_m = UUID_RE.search(attrs)
                    stack.append(
                        {"tag": tag, "line": idx,
                         "uuid": uuid_m.group(1) if uuid_m else None,
                         "name": None}
                    )
            sn = SHORT_NAME_RE.search(line)
            if sn and stack and stack[-1]["name"] is None:
                stack[-1]["name"] = sn.group(1)
                path = "/" + "/".join(e["name"] for e in stack if e["name"])
                top = stack[-1]
                el = SourceElement(path, top["uuid"], top["tag"], fname, top["line"])
                self.by_path[path] = el
                if top["uuid"]:
                    self.by_uuid[top["uuid"]] = el

    def line_for(self, sn_path: str, uuid: Optional[str]) -> Optional[int]:
        el = self.by_path.get(sn_path)
        if el is None and uuid:
            el = self.by_uuid.get(uuid)
        return el.line if el else None


# --------------------------------------------------------------------------- #
# Pass 2 — structured tree
# --------------------------------------------------------------------------- #


@dataclass
class Ref:
    role: str           # the *-REF / *-TREF tag, e.g. PROVIDED-INTERFACE-TREF
    dest: Optional[str]  # DEST attribute (target element type)
    target: str          # the referenced AUTOSAR path


@dataclass
class Node:
    tag: str
    name: str
    path: str
    uuid: Optional[str]
    file: str
    line: Optional[int]
    fields: Dict[str, str] = field(default_factory=dict)
    refs: List[Ref] = field(default_factory=list)
    children: List["Node"] = field(default_factory=list)

    def source_ref(self) -> str:
        loc = f"{self.file}:{self.line}" if self.line is not None else self.file
        return f"{loc} ({self.path})"


def _direct_short_name(elem: ET.Element) -> Optional[str]:
    for child in elem:
        if _local(child.tag) == "SHORT-NAME":
            return (child.text or "").strip()
    return None


def _build_node(elem: ET.Element, parent_path: str, fname: str,
                lines: LineIndex) -> Node:
    name = _direct_short_name(elem) or ""
    path = f"{parent_path}/{name}" if name else parent_path
    tag = _local(elem.tag)
    uuid = elem.get("UUID")
    node = Node(tag=tag, name=name, path=path, uuid=uuid, file=fname,
                line=lines.line_for(path, uuid))
    _collect(elem, node, path, fname, lines)
    return node


def _collect(elem: ET.Element, node: Node, path: str, fname: str,
             lines: LineIndex) -> None:
    """Populate ``node`` from ``elem``'s descendants, stopping at the next
    named element (which becomes a child node)."""
    for child in elem:
        ctag = _local(child.tag)
        if ctag == "SHORT-NAME":
            continue
        if _direct_short_name(child) is not None:
            node.children.append(_build_node(child, path, fname, lines))
            continue
        if ctag.endswith("-REF") or ctag.endswith("-TREF"):
            target = (child.text or "").strip()
            if target:
                node.refs.append(Ref(role=ctag, dest=child.get("DEST"), target=target))
            continue
        if len(child) == 0:
            text = (child.text or "").strip()
            if text:
                node.fields[ctag] = text
            continue
        # Wrapper / container element (PORTS, EVENTS, IREFs, ...): descend,
        # attributing its refs/fields/children to the current named element.
        _collect(child, node, path, fname, lines)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def _classify(tag: str) -> Optional[str]:
    if tag in COMPONENT_TAGS:
        return "components"
    if tag in INTERFACE_TAGS:
        return "interfaces"
    if tag in PLATFORM_TAGS:
        return "platform_types"
    if tag in SYSTEM_TAGS:
        return "systems"
    if tag in COMMUNICATION_TAGS:
        return "communication"
    if tag in IMPLEMENTATION_TAGS:
        return "implementations"
    return None


def _walk(elem: ET.Element, parent_path: str, fname: str, lines: LineIndex,
          buckets: Dict[str, List[Node]]) -> None:
    """Descend through packages/wrappers; emit a classified node when a
    top-level element is reached (without descending past it)."""
    for child in elem:
        ctag = _local(child.tag)
        if ctag == "SHORT-NAME":
            continue
        bucket = _classify(ctag)
        if bucket is not None:
            buckets[bucket].append(_build_node(child, parent_path, fname, lines))
            continue
        # Carry the AUTOSAR path through named packages (AR-PACKAGE), descend
        # through wrappers (AR-PACKAGES, ELEMENTS).
        name = _direct_short_name(child)
        next_path = f"{parent_path}/{name}" if name else parent_path
        _walk(child, next_path, fname, lines, buckets)


def parse_file(path: Path, lines: LineIndex) -> Dict[str, List[Node]]:
    buckets: Dict[str, List[Node]] = {
        "components": [], "interfaces": [], "platform_types": [],
        "systems": [], "communication": [], "implementations": [],
    }
    root = ET.parse(path).getroot()
    _walk(root, "", path.name, lines, buckets)
    return buckets


def parse_repo(src_dir: Path) -> dict:
    """Parse every ``.arxml`` under ``src_dir`` (recursively) into the
    structured, source-linked model the agent turns into Markdown.

    Returns a JSON-serialisable dict (see :func:`scan_repo` in ``tools.py``)."""
    src_dir = Path(src_dir)
    arxml_files = sorted(src_dir.rglob("*.arxml"))

    lines = LineIndex()
    source_files = []
    for f in arxml_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        lines.index_file(f.name, text)
        source_files.append({"file": f.name, "lines": len(text.splitlines())})

    buckets: Dict[str, List[Node]] = {
        "components": [], "interfaces": [], "platform_types": [],
        "systems": [], "communication": [], "implementations": [],
    }
    for f in arxml_files:
        for key, nodes in parse_file(f, lines).items():
            buckets[key].extend(nodes)

    # Flat, sorted source map (durable provenance table).
    source_map = [
        {"path": el.sn_path, "uuid": el.uuid or "_none_", "type": el.tag,
         "file": el.file, "line": el.line}
        for el in lines.by_path.values()
        if el.tag in SIGNIFICANT_TAGS
    ]
    source_map.sort(key=lambda r: (r["file"], r["path"]))

    elements = {k: [asdict(n) for n in v] for k, v in buckets.items()}
    stats = {
        "source_files": len(source_files),
        "total_lines": sum(s["lines"] for s in source_files),
        "components": len(buckets["components"]),
        "interfaces": len(buckets["interfaces"]),
        "platform_types": len(buckets["platform_types"]),
        "systems": len(buckets["systems"]),
        "communication": len(buckets["communication"]),
        "implementations": len(buckets["implementations"]),
        "indexed_elements": len(source_map),
    }
    return {
        "source_files": source_files,
        "stats": stats,
        "source_map": source_map,
        "elements": elements,
    }
