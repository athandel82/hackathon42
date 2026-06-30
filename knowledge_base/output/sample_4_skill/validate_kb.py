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
