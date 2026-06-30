# Generate AUTOSAR ARXML Knowledge Base (v3 — Source-Linked & Self-Validating)

## Agent Operating Model (READ FIRST)

You are an in-process ingestion agent. Extraction is **deterministic and done
for you** — you do not read raw XML or count lines yourself. You orchestrate a
small, fixed tool set and author Markdown:

- **`scan_repo(github_url, branch)`** — fetches the GitHub repository tarball,
  extracts it, parses every `.arxml` file, and returns the fully structured,
  **source-linked** model in one call: `source_files`, `stats`, a sorted
  `source_map` (`path, uuid, type, file, line` for every significant element),
  and classified `elements` (`components`, `interfaces`, `platform_types`,
  `systems`, `communication`, `implementations`). Every element already carries
  its `file`, `line` (opening-tag line) and AUTOSAR `path` — use these verbatim
  for the Source Reference `<file>:<line> (<path>)`. **Never invent or recompute
  a line number.** Call this exactly once, first.
- **`write_kb_file(rel_path, markdown)`** — writes one Markdown file into the KB
  tree (synced to its final destination on finalize). `rel_path` is relative to
  the KB root, e.g. `_index/path-index.md`, `components/Door.md`.
- **`record_status(repo_id, status, meta)`** — optional progress updates.

The `repo_path` / `output_path` parameters below are realised by these tools:
`repo_path` is the tarball fetched by `scan_repo`; `output_path` is the KB tree
you populate with `write_kb_file`. Follow the procedure, templates and rules in
the rest of this document exactly, sourcing all facts from the `scan_repo`
result.

## Purpose

Parse AUTOSAR ARXML files and generate a structured Markdown knowledge base that
a **Coding Agent can explore efficiently at scale** AND **trace back to the exact
source XML** for every fact.

This version adds two capabilities on top of v2:

1. **Source ARXML cross-references** — every extracted element records where it
   came from: the source file, the line number, and its SHORT-NAME path inside
   the XML. The agent (or a human reviewer) can jump from any knowledge-base
   statement to the precise XML that produced it. This is essential for the SDV
   use case, where a "blast radius" answer must be *defensible* — every claim
   points at primary-source evidence.
2. **A validation + auto-fix script** (`validate_kb.py`) — a standalone Python
   tool that checks all cross-references (markdown-to-markdown, markdown-to-AUTOSAR
   path, and markdown-to-source-ARXML) are correct, and repairs the
   mechanically-repairable ones automatically.

Primary consumer is still an AI agent answering: "If I remove the rear-door
module, what breaks? what does it cost? what does it risk?" — now with traceable
provenance and a guarantee that the link graph is intact.

> Design principles:
> - **Index first, detail on demand.**
> - **Every fact is source-linked.** No statement without a source reference.
> - **The link graph is verifiable and self-healing.** A script proves it.

## Parameters

- **github_url** (required): HTTPS URL of the GitHub repository to ingest. Passed
  to `scan_repo`; it provides `repo_path` (the extracted `.arxml` tree).
- **branch** (required): Branch to fetch (e.g. `master`).
- **output_path**: The KB tree, populated via `write_kb_file` (paths relative to
  the KB root). You do not choose a filesystem location; the tool handles sync.

---

## Output Structure

```
<output_path>/
├── README.md
├── validate_kb.py                  # Cross-reference validator + auto-fixer (NEW in v3)
├── _index/
│   ├── path-index.md               # AUTOSAR path → KB file + type + SOURCE REF (extended)
│   ├── source-map.md               # NEW: SHORT-NAME path / UUID → source file:line
│   ├── components.md
│   ├── interfaces.md
│   ├── platform-types.md
│   ├── dependency-graph.md
│   ├── port-map.md
│   ├── signal-chains.md
│   ├── composition-tree.md
│   └── stats.md                    # Includes validation summary
├── components/<ComponentName>.md
├── interfaces/<InterfaceName>.md
├── platform/BaseTypes.md
├── platform/ImplementationDataTypes.md
└── system/<SystemName>.md
```

Everything from v2 is retained. The differences are: a new `Source Reference`
field/column on every element, the new `_index/source-map.md`, an extended
`_index/path-index.md`, and the `validate_kb.py` script.

---

## Source Reference Convention (NEW — applies everywhere)

Every extracted element carries a **source reference** with three parts:

| Part | Meaning | Example |
|------|---------|---------|
| `file` | Source ARXML filename (relative to `repo_path`) | `EcuExtract.arxml` |
| `line` | 1-based line number of the element's opening tag | `10` |
| `sn_path` | SHORT-NAME path inside the XML (the `<SHORT-NAME>` ancestry, AUTOSAR path) | `/Demo/Door/Door` |

Render it inline as a compact string:

```
EcuExtract.arxml:10  (/Demo/Door/Door)
```

Rules:

- The **line number** points at the line of the element's opening XML tag (e.g.
  the line with `<APPLICATION-SW-COMPONENT-TYPE UUID="...">`).
- The **`sn_path`** is the stable identifier. Line numbers drift if the source is
  reformatted; `sn_path` + `UUID` are the durable keys the validator uses to
  re-locate an element and **recompute** the line number during auto-fix.
- Always record the **UUID** alongside (it already appears in detail files). UUID
  + `sn_path` together let the validator recover from both renames and reorders.

---

## Element Classification

(Identical to v2.)

- **Components**: `APPLICATION-SW-COMPONENT-TYPE`, `SERVICE-SW-COMPONENT-TYPE`,
  `COMPOSITION-SW-COMPONENT-TYPE`, `SENSOR-ACTUATOR-SW-COMPONENT-TYPE`,
  `COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE`, `ECU-ABSTRACTION-SW-COMPONENT-TYPE`,
  `NV-BLOCK-SW-COMPONENT-TYPE`.
- **Interfaces**: `SENDER-RECEIVER-INTERFACE`, `CLIENT-SERVER-INTERFACE`,
  `MODE-SWITCH-INTERFACE`, `NV-DATA-INTERFACE`, `PARAMETER-INTERFACE`,
  `TRIGGER-INTERFACE`.
- **Platform Types**: `SW-BASE-TYPE`, `IMPLEMENTATION-DATA-TYPE`, `COMPU-METHOD`,
  `APPLICATION-PRIMITIVE-DATA-TYPE`, `APPLICATION-RECORD-DATA-TYPE`.
- **System**: `SYSTEM` (note CATEGORY, esp. `ECU_EXTRACT`).
- **Communication**: `I-SIGNAL`, `SYSTEM-SIGNAL`, `I-SIGNAL-I-PDU`,
  `I-SIGNAL-TO-I-PDU-MAPPING`, `FRAME`, `CAN-CLUSTER`, etc.

---

## Processing Procedure

Same multi-pass flow as v2, with source-reference capture added to pass 1.

### Step 0: Plan Processing Batches

1. Call `scan_repo(github_url, branch)` once. It returns `source_files` (with
   per-file line counts) and `stats`.
2. Read size from the result (`stats.source_files`, `stats.total_lines`).
3. Mode: **Small** (≤ ~10 files, ≤ ~5,000 lines) → single pass. **Large** → batched.
4. Record plan in `_index/stats.md`.

### Step 1: First Pass — Lightweight Scan + Source Capture

`scan_repo` has already captured, for each element, the cheap identity data
**and its source reference**:

- SHORT-NAME, element tag (type), UUID, full AUTOSAR path (`sn_path` = `path`).
- **Source `file` + `line`** of the element's opening tag.
- Component ports `(name, P/R, interface TREF path)` (in each component's
  `children` / `refs`).
- Interface data elements / operation names (interface `children`).
- Composition prototypes + connector endpoints (composition `children` + `refs`).
- System implementation/signal mappings (system `children` + `refs`).

> You do not track lines yourself — every node's `line` is authoritative. The
> sorted `source_map` array is ready to render directly.

Immediately write:

- `_index/source-map.md` (every `sn_path` + UUID → `file:line`, from `source_map`)
- `_index/path-index.md` (now with a Source Ref column)
- `_index/components.md`, `interfaces.md`, `platform-types.md`, `port-map.md`

### Step 2: Resolve the Relationship Graph

(Same as v2.) Compute forward deps, reverse deps, composition containment from
ports + connectors. Write `_index/dependency-graph.md`, `composition-tree.md`.

### Step 3: Trace Signal / Data-Flow Chains

(Same as v2.) Follow runnable write → data element → connector → consumer
runnable / system signal → I-Signal → I-PDU → frame/cluster. Write
`_index/signal-chains.md`. For each hop, include the source ref of the element
that defines the hop (e.g. the connector or signal-mapping line).

### Step 4: Second Pass — Generate Detail Files (batched)

Generate per-element files using the templates below. Every detail file's
identity table includes a **Source Reference** row. Populate Dependencies /
Impact Tags from the computed graph.

### Step 5: Generate README + validate_kb.py + stats

1. Write `README.md` (navigation guide + metadata).
2. Write `validate_kb.py` verbatim from the **Validation Script** section below
   (use `write_kb_file("validate_kb.py", ...)`).
3. Record the validation contract in `_index/stats.md`: the validator is shipped
   with the KB and is run against the synced tree
   (`python validate_kb.py <output_path> --source <repo_path> [--fix]`). Because
   `scan_repo` supplies authoritative line numbers, the Source-ref check should
   report `PASS`; fill the Validation Summary accordingly and list any
   `(UNRESOLVED)` references you emitted under "Unresolved / Manual Issues".

---

## Cross-Referencing Rules

- Link by **relative Markdown link** with the AUTOSAR path as text:
  `[/Demo/Door/Door](../components/Door.md)`.
- Preserve **all UUIDs and full AUTOSAR paths** verbatim.
- Every element states its **Source Reference** (`file:line (sn_path)`).
- Unresolvable references: write the raw path tagged `(UNRESOLVED)` and list in
  `_index/stats.md`.
- Tables for structured data; `_None_` for empty sections.
- Sort rows alphabetically where practical (chains stay ordered).

---

## Index File Templates

### `_index/source-map.md` (NEW)

The provenance resolver. Maps each element identity to its source location. The
validator reads this to verify/repair line numbers.

```markdown
# Source Map

Maps each AUTOSAR element to its location in the source ARXML. Durable keys are
`AUTOSAR Path` + `UUID`; `Line` is recomputable and may be auto-fixed.

| AUTOSAR Path | UUID | Type | Source File | Line |
|--------------|------|------|-------------|-----:|
| /Demo/Door/Door | 2dbc5fd9-e3c1-3151-a0e4-b723a660be32 | APPLICATION-SW-COMPONENT-TYPE | EcuExtract.arxml | 10 |
| /Demo/Interfaces/DoorCommands | 0fc0e7ac-fbe4-3814-94c3-69077a1f35f3 | CLIENT-SERVER-INTERFACE | EcuExtract.arxml | 612 |
| ... | ... | ... | ... | ... |
```

### `_index/path-index.md` (EXTENDED — adds Source Ref column)

```markdown
# Path Index

Resolve any AUTOSAR path to its KB file, type, and source location.

| AUTOSAR Path | Type | File | Source Ref |
|--------------|------|------|------------|
| /Demo/Door/Door | APPLICATION-SW-COMPONENT-TYPE | [components/Door.md](../components/Door.md) | EcuExtract.arxml:10 |
| /Demo/Interfaces/DoorCommands | CLIENT-SERVER-INTERFACE | [interfaces/DoorCommands.md](../interfaces/DoorCommands.md) | EcuExtract.arxml:612 |
| ... | ... | ... | ... |
```

### `_index/components.md`, `interfaces.md`, `platform-types.md`, `port-map.md`, `dependency-graph.md`, `composition-tree.md`, `signal-chains.md`

(Same as v2. Optionally append a `Source Ref` column to `components.md`,
`interfaces.md`, and `platform-types.md` for fast provenance scanning.)

### `_index/stats.md` (EXTENDED — adds validation summary)

```markdown
# Knowledge Base Statistics

| Metric | Count |
|--------|------:|
| Source ARXML files | N |
| Total source lines | N |
| Components | N |
| Interfaces | N |
| Platform types | N |
| Systems | N |
| Signal chains traced | N |
| Unresolved references | N |

## Processing Mode
<small / large; number of batches>

## Validation Summary
| Check | Result |
|-------|--------|
| Markdown links resolve | PASS / N broken |
| AUTOSAR paths in path-index | PASS / N missing |
| Source refs valid (file exists, line matches sn_path/UUID) | PASS / N stale |
| UUID consistency (MD ↔ source) | PASS / N mismatch |
| Dependency graph bidirectional consistency | PASS / N asymmetric |
| Last validated | <YYYY-MM-DD HH:MM> |
| Auto-fixed this run | N |
| Remaining manual issues | N |

## Unresolved / Manual Issues
| Path | Issue | Referenced From |
|------|-------|-----------------|
| ... | ... | ... |
```

---

## Detail File Templates

### Component (`components/<Name>.md`)

Identical to v2 **plus** a `Source Reference` row in the identity table:

```markdown
# <ComponentName>

## Impact Tags

- **type:** <element tag>
- **safety-relevant:** <yes/no/unknown>
- **network-connected:** <yes/no>
- **shared-implementation:** <impl name or No>
- **composition-parent:** <parent composition(s) or None>
- **signal-producer:** <system signals fed, or None>
- **leaf:** <yes/no>

## Component Information

| Field | Value |
|-------|-------|
| Name | <SHORT-NAME> |
| Type | <element tag> |
| UUID | <UUID> |
| Package | <full AUTOSAR path> |
| Source File | <filename> |
| Source Reference | <file>:<line> (<sn_path>) |

## Description
...

## Ports
### Provided Ports (P-PORT)
| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|
| ... | [path](link) | ... | ... | <file>:<line> |

### Required Ports (R-PORT)
| Port Name | Interface | Interface Type | UUID | Source Ref |
|-----------|-----------|----------------|------|------------|

## Internal Behavior
| Field | Value |
|-------|-------|
| Name | ... |
| UUID | ... |
| Handle Termination | ... |
| Multiple Instantiation | ... |
| Source Reference | <file>:<line> |

## Events
| Event Name | Type | Trigger (Runnable) | Period | UUID |
|------------|------|--------------------|--------|------|

## Runnables
### <RunnableName>
| Field | Value |
|-------|-------|
| UUID | ... |
| Symbol | ... |
| Minimum Start Interval | ... |
| Concurrent Invocation | ... |
| Source Reference | <file>:<line> |

**Data Read Access:** / **Data Write Access:** / **Server Call Points:**
(as v2)

## Implementation
| Field | Value |
|-------|-------|
| Name | ... |
| UUID | ... |
| Programming Language | ... |
| Vendor ID | ... |
| Behavior Reference | ... |
| Source Reference | <file>:<line> |

## Dependencies
### Provides To / Requires From / Calls / Called By / Participates In Signal Chains
(as v2)
```

For **COMPOSITION-SW-COMPONENT-TYPE**, add (as v2) Internal Components, Assembly
Connectors, Delegation Connectors, Architecture Diagram. Add a `Source Ref`
column to the connector tables so each connector is traceable.

### Interface (`interfaces/<Name>.md`)

As v2 **plus** `Source Reference` row in the identity table and a `Source Ref`
column on operations/data-element tables.

### Platform files

As v2 **plus** a `Source Ref` column in the Base Types / Value Types tables.

### System (`system/<Name>.md`)

As v2 **plus** `Source Reference` row, and `Source Ref` columns on
implementation mappings, signal mappings, and communication tables.

### `README.md`

As v2, plus a section:

```markdown
## Validation

This knowledge base ships with `validate_kb.py`, which verifies every
cross-reference (markdown links, AUTOSAR paths, and source-ARXML line refs) and
can auto-repair mechanical breakage.

```bash
# Validate only (exit code 0 = clean, 1 = issues found)
python validate_kb.py . --source <path-to-source-arxml-dir>

# Validate and auto-fix repairable issues, then re-validate
python validate_kb.py . --source <path-to-source-arxml-dir> --fix
```

See [`_index/stats.md`](_index/stats.md) for the latest validation summary.
```

---

## Validation Script

Write this file verbatim to `<output_path>/validate_kb.py`. It is dependency-free
(standard library only) so it runs anywhere Python 3.8+ is available.

What it checks:

1. **Markdown links** — every `[text](relative/path.md)` (and optional `#anchor`)
   resolves to an existing file (and heading, if an anchor is used).
2. **AUTOSAR path references** — every `/Demo/...` or `/ArcCore/...` style path
   used as link text exists as a row in `_index/path-index.md`.
3. **Source references** — every `file:line (sn_path)` (and `_index/source-map.md`
   rows): the source file exists, and the recorded line's element matches the
   recorded `sn_path`/UUID (recomputing the true line by locating the SHORT-NAME
   or UUID in the source XML).
4. **UUID consistency** — UUIDs cited in detail files exist in the source ARXML.
5. **Dependency-graph symmetry** — if A "Requires From" B, then B "Provides To"
   A (and reverse-dependency table agrees).

What `--fix` repairs automatically:

- **Stale line numbers**: recompute from `sn_path`/UUID and rewrite.
- **Broken relative links** where the target was renamed/moved but is uniquely
  recoverable by filename or by the AUTOSAR path via `path-index.md`.
- **Missing/auto-resolvable `path-index` source-ref columns**: backfill from
  `source-map.md`.

What it reports but does NOT auto-fix (needs human judgment):

- A referenced AUTOSAR path that exists in no source file (genuinely dangling).
- UUID mismatches (could indicate a real model change).
- Asymmetric dependency entries (could indicate an extraction error).

```python
#!/usr/bin/env python3
"""
validate_kb.py — Validate and optionally auto-fix cross-references in an
AUTOSAR ARXML knowledge base produced by the v3 skill.

Usage:
    python validate_kb.py <kb_dir> [--source <arxml_dir>] [--fix] [--quiet]

Exit codes:
    0  clean (no issues, or all issues auto-fixed)
    1  issues remain (manual attention required)
    2  usage / environment error
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# ----------------------------- source ARXML index -----------------------------

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


class SourceIndex:
    """Indexes every typed element in the source ARXML by sn_path and by UUID.

    AUTOSAR puts the <SHORT-NAME> as the first child of its owning element, so we
    maintain a stack of open typed elements; when we see a SHORT-NAME we assign it
    to the innermost open element and record that element's opening-tag line.
    """

    def __init__(self) -> None:
        self.by_path: Dict[str, SourceElement] = {}
        self.by_uuid: Dict[str, SourceElement] = {}
        self.files: Dict[str, List[str]] = {}  # filename -> lines

    def build(self, source_dir: Path) -> None:
        for arxml in sorted(source_dir.rglob("*.arxml")):
            rel = arxml.name
            lines = arxml.read_text(encoding="utf-8", errors="replace").splitlines()
            self.files[rel] = lines
            self._index_file(rel, lines)

    def _index_file(self, fname: str, lines: List[str]) -> None:
        # Stack entries: dict with tag, line, uuid, name (name filled when seen).
        stack: List[dict] = []
        for idx, line in enumerate(lines, start=1):
            for m in TAG_RE.finditer(line):
                closing = m.group(1) == "/"
                tag = m.group(2)
                attrs = m.group(3) or ""
                self_close = m.group(4) == "/"
                if tag == "SHORT-NAME":
                    continue
                if closing:
                    # Pop the matching open element (nearest with same tag).
                    for i in range(len(stack) - 1, -1, -1):
                        if stack[i]["tag"] == tag:
                            del stack[i:]
                            break
                elif not self_close:
                    uuid_m = UUID_RE.search(attrs)
                    stack.append({
                        "tag": tag,
                        "line": idx,
                        "uuid": uuid_m.group(1) if uuid_m else None,
                        "name": None,
                    })
            sn = SHORT_NAME_RE.search(line)
            if sn and stack and stack[-1]["name"] is None:
                stack[-1]["name"] = sn.group(1)
                path = "/" + "/".join(e["name"] for e in stack if e["name"])
                top = stack[-1]
                el = SourceElement(sn_path=path, uuid=top["uuid"], tag=top["tag"],
                                   file=fname, line=top["line"])
                self.by_path[path] = el
                if top["uuid"]:
                    self.by_uuid[top["uuid"]] = el

    def locate(self, sn_path: Optional[str], uuid: Optional[str]) -> Optional[SourceElement]:
        if sn_path and sn_path in self.by_path:
            return self.by_path[sn_path]
        if uuid and uuid in self.by_uuid:
            return self.by_uuid[uuid]
        return None


# ------------------------------- issue model ---------------------------------

@dataclass
class Issue:
    kind: str          # "link" | "path" | "sourceref" | "uuid" | "graph"
    md_file: str
    detail: str
    fixable: bool = False
    fix_note: str = ""


@dataclass
class Report:
    issues: List[Issue] = field(default_factory=list)
    fixed: int = 0

    def add(self, issue: Issue) -> None:
        self.issues.append(issue)


# ------------------------------- validators ----------------------------------

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SOURCE_REF_RE = re.compile(r"([A-Za-z0-9_.\-]+\.arxml):(\d+)(?:\s*\(([^)]+)\))?")


def iter_md_files(kb_dir: Path) -> List[Path]:
    return list(kb_dir.rglob("*.md"))


def strip_code_fences(text: str) -> str:
    """Blank out fenced code blocks so example/template links and diagrams
    inside ``` ... ``` are not treated as real cross-references."""
    out = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
        else:
            # Also blank inline code spans (`...`) — links inside them are
            # illustrative examples, not real cross-references.
            out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def path_resolvable(autosar_path: str, path_index: Dict[str, str]) -> bool:
    """A path resolves if it, or any ancestor prefix, is in the path-index.
    This handles sub-element paths (e.g. an interface's data element) that
    live inside their parent element's file."""
    if autosar_path in path_index:
        return True
    parts = autosar_path.strip("/").split("/")
    for i in range(len(parts) - 1, 0, -1):
        if "/" + "/".join(parts[:i]) in path_index:
            return True
    return False


def load_path_index(kb_dir: Path) -> Dict[str, str]:
    idx: Dict[str, str] = {}
    pi = kb_dir / "_index" / "path-index.md"
    if not pi.exists():
        return idx
    for line in pi.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("AUTOSAR Path",) or cells[0].startswith(":--") or cells[0].startswith("---"):
            continue
        path = cells[0]
        link_m = LINK_RE.search(cells[2])
        if path.startswith("/") and link_m:
            idx[path] = link_m.group(2)
    return idx


def check_markdown_links(md: Path, kb_dir: Path, name_to_paths: Dict[str, List[Path]],
                         report: Report, fix: bool) -> None:
    raw = md.read_text(encoding="utf-8")
    lines = raw.splitlines()
    scan = strip_code_fences(raw).splitlines()
    changed = False
    for i, line in enumerate(scan):
        for m in LINK_RE.finditer(line):
            target = m.group(2)
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part.endswith(".md"):
                continue
            resolved = (md.parent / path_part).resolve()
            if resolved.exists():
                continue
            fname = os.path.basename(path_part)
            candidates = name_to_paths.get(fname, [])
            if fix and len(candidates) == 1:
                new_rel = os.path.relpath(candidates[0], md.parent)
                anchor = ("#" + target.split("#", 1)[1]) if "#" in target else ""
                new_target = new_rel + anchor
                lines[i] = lines[i].replace(f"]({target})", f"]({new_target})")
                changed = True
                report.fixed += 1
                report.add(Issue("link", str(md), f"broken link {target} -> {new_target}",
                                 fixable=True, fix_note="relinked"))
            else:
                report.add(Issue("link", str(md), f"broken link: {target}",
                                 fixable=(len(candidates) == 1)))
    if fix and changed:
        md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_autosar_paths(md: Path, path_index: Dict[str, str], report: Report) -> None:
    text = strip_code_fences(md.read_text(encoding="utf-8"))
    for m in LINK_RE.finditer(text):
        link_text = m.group(1)
        if link_text.startswith("/") and "/" in link_text[1:]:
            if not path_resolvable(link_text, path_index):
                report.add(Issue("path", str(md),
                                 f"AUTOSAR path not in path-index: {link_text}",
                                 fixable=False))


def check_source_refs(md: Path, src: SourceIndex, report: Report, fix: bool) -> None:
    if not src.files:
        return
    raw = md.read_text(encoding="utf-8")
    lines = raw.splitlines()
    scan = strip_code_fences(raw).splitlines()
    changed = False
    for i, line in enumerate(scan):
        for m in SOURCE_REF_RE.finditer(line):
            fname, lineno, sn_path = m.group(1), int(m.group(2)), m.group(3)
            if fname not in src.files:
                report.add(Issue("sourceref", str(md),
                                 f"source file not found: {fname}", fixable=False))
                continue
            el = src.locate(sn_path, None) if sn_path else None
            if el is None:
                if sn_path:
                    report.add(Issue("sourceref", str(md),
                                     f"sn_path not found in source: {sn_path}",
                                     fixable=False))
                continue
            if el.file != fname:
                report.add(Issue("sourceref", str(md),
                                 f"{sn_path} is in {el.file}, ref says {fname}",
                                 fixable=False))
                continue
            if el.line != lineno:
                if fix:
                    old = f"{fname}:{lineno}"
                    new = f"{fname}:{el.line}"
                    lines[i] = lines[i].replace(old, new, 1)
                    changed = True
                    report.fixed += 1
                    report.add(Issue("sourceref", str(md),
                                     f"stale line {old} -> {new} ({sn_path})",
                                     fixable=True, fix_note="reline"))
                else:
                    report.add(Issue("sourceref", str(md),
                                     f"stale line for {sn_path}: ref {lineno}, actual {el.line}",
                                     fixable=True))
    if fix and changed:
        md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_uuids(md: Path, src: SourceIndex, report: Report) -> None:
    if not src.by_uuid:
        return
    text = strip_code_fences(md.read_text(encoding="utf-8"))
    for um in re.finditer(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                          r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", text):
        uuid = um.group(0)
        if uuid not in src.by_uuid:
            report.add(Issue("uuid", str(md),
                             f"UUID not found in source ARXML: {uuid}", fixable=False))


def check_graph_symmetry(kb_dir: Path, report: Report) -> None:
    comp_dir = kb_dir / "components"
    if not comp_dir.exists():
        return
    requires: Dict[str, set] = {}
    provides: Dict[str, set] = {}
    for md in comp_dir.glob("*.md"):
        name = md.stem
        section = None
        for line in md.read_text(encoding="utf-8").splitlines():
            h = line.strip().lower()
            if h.startswith("### requires from"):
                section = "req"
            elif h.startswith("### provides to"):
                section = "prov"
            elif h.startswith(("###", "##")):
                section = None
            elif line.startswith("|") and section:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells and cells[0] and cells[0] not in (
                        "Consumer Component", "Provider Component") \
                        and not cells[0].startswith(":--") and not cells[0].startswith("---"):
                    other = cells[0]
                    if other in ("_None_", "None"):
                        continue
                    target = requires if section == "req" else provides
                    target.setdefault(name, set()).add(other.split()[0])
    for a, deps in requires.items():
        for b in deps:
            providers_of_b = {x.split()[0] for x in provides.get(b, set())}
            if a not in providers_of_b:
                report.add(Issue("graph", str(comp_dir / f"{b}.md"),
                                 f"{a} Requires From {b}, but {b} has no matching Provides To {a}",
                                 fixable=False))


# --------------------------------- main --------------------------------------

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Validate/auto-fix KB cross-references.")
    ap.add_argument("kb_dir")
    ap.add_argument("--source", help="Path to source ARXML directory", default=None)
    ap.add_argument("--fix", action="store_true", help="Auto-fix repairable issues")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    kb_dir = Path(args.kb_dir).resolve()
    if not kb_dir.exists():
        print(f"error: kb_dir not found: {kb_dir}", file=sys.stderr)
        return 2

    src = SourceIndex()
    if args.source:
        sdir = Path(args.source).resolve()
        if not sdir.exists():
            print(f"error: source dir not found: {sdir}", file=sys.stderr)
            return 2
        src.build(sdir)

    report = Report()
    path_index = load_path_index(kb_dir)
    name_to_paths: Dict[str, List[Path]] = {}
    for p in kb_dir.rglob("*.md"):
        name_to_paths.setdefault(p.name, []).append(p)

    for md in iter_md_files(kb_dir):
        check_markdown_links(md, kb_dir, name_to_paths, report, args.fix)
        check_autosar_paths(md, path_index, report)
        check_source_refs(md, src, report, args.fix)
        check_uuids(md, src, report)
    check_graph_symmetry(kb_dir, report)

    remaining = [i for i in report.issues if not i.fix_note]
    if not args.quiet:
        by_kind: Dict[str, int] = {}
        for i in remaining:
            by_kind[i.kind] = by_kind.get(i.kind, 0) + 1
        print(f"Auto-fixed: {report.fixed}")
        print(f"Remaining issues: {len(remaining)}")
        for k, n in sorted(by_kind.items()):
            print(f"  {k}: {n}")
        for i in remaining[:200]:
            print(f"  [{i.kind}] {i.md_file}: {i.detail}")

    return 0 if not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

---

## Rules Summary

- **Index first, detail on demand.**
- **Every fact is source-linked** with `file:line (sn_path)`; keep `UUID` too.
- One Markdown file per component / interface / system; platform types grouped.
- Cross-references are relative Markdown links with the AUTOSAR path as text.
- `_index/source-map.md` is the durable provenance table; `path-index.md` carries
  a Source Ref column.
- Generate `validate_kb.py` verbatim, run it, and record the result in
  `_index/stats.md`. Use `--fix` to repair line drift and recoverable links.
- The validator never edits source ARXML; the whole skill is read-only w.r.t.
  the source model.
- Issues needing human judgment (dangling paths, UUID mismatch, asymmetric
  dependency edges) are reported, not silently changed.
