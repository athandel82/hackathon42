"""Deterministic stand-ins for the Bedrock-backed Strands agents.

A real end-to-end run invokes Amazon Bedrock (the LLM) inside each agent. That
needs AWS credentials + network, which integration CI does not have. These fakes
replace *only* the model: they drive the **real** deterministic tools, so the
cross-component contract is exercised for real —

  * ``ReferenceIngestAgent`` calls the real ``scan_repo`` (deterministic ARXML
    parse) and authors a real KB with the real ``write_kb_file`` tool, computing
    the dependency graph + signal chains from the parsed model (what the skill's
    procedure does, in Python).
  * ``ReferenceAnalyzeAgent`` answers with the real read-only KB navigation tools
    (``resolve_path`` / ``blast_radius`` / ``trace_signals`` / ``kb_read``) over
    the KB the ingest agent just wrote, and fills a real ``ResultEnvelope``.

Nothing about the storage, handlers, core, tools, KB layout or result schema is
faked — only the token generation.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Optional, Set

# --- ingest tools (real) ---
from ingest_agent.tools import scan_repo_impl, write_kb_file_impl

# --- analyze tools + schema (real) ---
from analyze_agent.models import ResultEnvelope
from analyze_agent import kb
from analyze_agent.tools import (
    blast_radius_impl,
    kb_read_impl,
    resolve_path_impl,
    trace_signals_impl,
)


def _short(path: str) -> str:
    return path.rstrip("/").rsplit("/", 1)[-1]


# =========================================================================== #
# Ingestion: parse -> compute graph -> author KB
# =========================================================================== #


class ReferenceIngestAgent:
    """Authors a KB from a scan_repo result (stands in for the skill-driven LLM)."""

    def __init__(self, github_url: str, branch: str) -> None:
        self.github_url = github_url
        self.branch = branch

    # The Strands Agent is invoked as ``agent(prompt)``.
    def __call__(self, prompt: str) -> str:
        scan = scan_repo_impl(self.github_url, self.branch)
        author_kb(scan)
        return "KB authored"


def _detail_file(node_tag: str, path: str, name: str, system_name: str) -> Optional[str]:
    if node_tag in {
        "APPLICATION-SW-COMPONENT-TYPE", "SERVICE-SW-COMPONENT-TYPE",
        "COMPOSITION-SW-COMPONENT-TYPE", "SENSOR-ACTUATOR-SW-COMPONENT-TYPE",
        "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE", "ECU-ABSTRACTION-SW-COMPONENT-TYPE",
        "NV-BLOCK-SW-COMPONENT-TYPE",
    }:
        return f"components/{name}.md"
    if node_tag.endswith("-INTERFACE"):
        return f"interfaces/{name}.md"
    if node_tag in {"SW-BASE-TYPE"}:
        return "platform/BaseTypes.md"
    if node_tag in {"IMPLEMENTATION-DATA-TYPE", "COMPU-METHOD",
                    "APPLICATION-PRIMITIVE-DATA-TYPE", "APPLICATION-RECORD-DATA-TYPE"}:
        return "platform/ImplementationDataTypes.md"
    if node_tag == "SYSTEM":
        return f"system/{name}.md"
    return None


def _compute_reverse_deps(components: List[dict]):
    """Reverse-dependency adjacency from composition connectors + containment."""
    proto_to_type: Dict[str, str] = {}
    containment: Dict[str, Set[str]] = defaultdict(set)
    requires: Dict[str, Set[str]] = defaultdict(set)

    # Pass 1: prototypes + containment.
    for c in components:
        for ch in c["children"]:
            if ch["tag"] == "SW-COMPONENT-PROTOTYPE":
                tref = next((r["target"] for r in ch["refs"] if r["role"] == "TYPE-TREF"), None)
                proto_to_type[ch["path"]] = tref
                if tref:
                    containment[c["path"]].add(tref)

    # Pass 2: assembly connectors -> requester type requires provider type.
    for c in components:
        for ch in c["children"]:
            if ch["tag"] == "ASSEMBLY-SW-CONNECTOR":
                ctx = [r["target"] for r in ch["refs"] if r["role"] == "CONTEXT-COMPONENT-REF"]
                if len(ctx) >= 2:
                    prov, req = proto_to_type.get(ctx[0]), proto_to_type.get(ctx[1])
                    if prov and req:
                        requires[req].add(prov)

    reverse: Dict[str, Set[str]] = defaultdict(set)
    for req_t, provs in requires.items():
        for p in provs:
            reverse[p].add(req_t)
    for comp_t, contained in containment.items():
        for ct in contained:
            reverse[ct].add(comp_t)
    return reverse


def author_kb(scan: dict) -> None:
    """Write the KB files the Analyze agent depends on, from the scan result."""
    elements = scan["elements"]
    components = elements["components"]
    interfaces = elements["interfaces"]
    systems = elements["systems"]
    communication = elements["communication"]
    source_map = scan["source_map"]
    system_name = systems[0]["name"] if systems else "System"

    # ---- primary path -> detail file map (for path-index + resolution) ----
    primaries: List[tuple] = []  # (path, file)
    for bucket in (components, interfaces, systems,
                   elements["platform_types"], communication):
        for n in bucket:
            f = _detail_file(n["tag"], n["path"], n["name"], system_name)
            if f is None and n in communication:
                f = f"system/{system_name}.md"
            if f:
                primaries.append((n["path"], f))
    primaries.sort(key=lambda t: len(t[0]), reverse=True)  # longest-prefix first

    def owner_file(path: str) -> Optional[str]:
        for p, f in primaries:
            if path == p or path.startswith(p + "/"):
                return f
        return None

    # ---- _index/path-index.md ----
    rows = ["# Path Index", "",
            "| AUTOSAR Path | Type | File | Source Ref |",
            "|--------------|------|------|------------|"]
    for e in source_map:
        f = owner_file(e["path"])
        if not f:
            continue
        rel = "../" + f
        rows.append(f"| {e['path']} | {e['type']} | [{f}]({rel}) | {e['file']}:{e['line']} |")
    write_kb_file_impl("_index/path-index.md", "\n".join(rows) + "\n")

    # ---- _index/source-map.md ----
    smap = ["# Source Map", "",
            "| AUTOSAR Path | UUID | Type | Source File | Line |",
            "|--------------|------|------|-------------|-----:|"]
    for e in source_map:
        smap.append(f"| {e['path']} | {e['uuid']} | {e['type']} | {e['file']} | {e['line']} |")
    write_kb_file_impl("_index/source-map.md", "\n".join(smap) + "\n")

    # ---- _index/components.md ----
    cidx = ["# Components Index", "",
            "| Component | Type | Package | File | Source Ref |",
            "|-----------|------|---------|------|------------|"]
    for c in components:
        pkg = c["path"].rsplit("/", 1)[0]
        cidx.append(f"| [{c['path']}](../components/{c['name']}.md) | {c['tag']} | {pkg} "
                    f"| [{c['name']}.md](../components/{c['name']}.md) | {c['file']}:{c['line']} |")
    write_kb_file_impl("_index/components.md", "\n".join(cidx) + "\n")

    # ---- _index/interfaces.md ----
    iidx = ["# Interfaces Index", "",
            "| Interface | Type | File | Source Ref |",
            "|-----------|------|------|------------|"]
    for i in interfaces:
        iidx.append(f"| [{i['path']}](../interfaces/{i['name']}.md) | {i['tag']} "
                    f"| [{i['name']}.md](../interfaces/{i['name']}.md) | {i['file']}:{i['line']} |")
    write_kb_file_impl("_index/interfaces.md", "\n".join(iidx) + "\n")

    # ---- _index/dependency-graph.md (reverse adjacency = blast radius) ----
    reverse = _compute_reverse_deps(components)
    type_name = {c["path"]: c["name"] for c in components}
    dg = ["# Dependency Graph", "",
          "## Reverse Dependencies (blast radius — who breaks if this changes)", "",
          "| Component | Depended On By |", "|-----------|----------------|"]
    for c in sorted(components, key=lambda c: c["path"]):
        deps = sorted(type_name.get(t, _short(t)) for t in reverse.get(c["path"], set()))
        cell = ", ".join(deps) if deps else "_None_ (root composition)"
        dg.append(f"| [{c['path']}](../components/{c['name']}.md) | {cell} |")
    dg += ["", "## Blast-Radius Quick Reference", ""]
    for c in sorted(components, key=lambda c: c["path"]):
        deps = sorted(type_name.get(t, _short(t)) for t in reverse.get(c["path"], set()))
        if deps:
            dg.append(f"- **Remove `{c['name']}`** → breaks {', '.join(deps)}.")
        else:
            dg.append(f"- **`{c['name']}`** is a root; nothing depends on it.")

    # Interface Usage: providers / requirers from component port TREFs.
    provided: Dict[str, Set[str]] = defaultdict(set)
    required: Dict[str, Set[str]] = defaultdict(set)
    for c in components:
        for ch in c["children"]:
            if ch["tag"] in ("P-PORT-PROTOTYPE", "R-PORT-PROTOTYPE"):
                tref = next((r["target"] for r in ch["refs"] if r["role"].endswith("INTERFACE-TREF")), None)
                if not tref:
                    continue
                (provided if ch["tag"] == "P-PORT-PROTOTYPE" else required)[tref].add(c["name"])
    dg += ["", "## Interface Usage (who touches each interface)", "",
           "| Interface | Provided By | Required By |", "|-----------|-------------|-------------|"]
    for i in sorted(interfaces, key=lambda i: i["path"]):
        prov = ", ".join(sorted(provided.get(i["path"], set()))) or "_None_"
        req = ", ".join(sorted(required.get(i["path"], set()))) or "_None_"
        dg.append(f"| [{i['path']}](../interfaces/{i['name']}.md) | {prov} | {req} |")
    write_kb_file_impl("_index/dependency-graph.md", "\n".join(dg) + "\n")

    # ---- _index/signal-chains.md (one chain per system signal) ----
    sys_signals = [n for n in communication if n["tag"] == "SYSTEM-SIGNAL"]
    isigs = {n["name"] for n in communication if n["tag"] == "I-SIGNAL"}
    ipdus = {n["name"] for n in communication if n["tag"] == "I-SIGNAL-I-PDU"}
    producer = next((c["name"] for c in components
                     if c["tag"] == "APPLICATION-SW-COMPONENT-TYPE"), "Producer")
    aggregator = next((c["name"] for c in components
                       if c["tag"] == "APPLICATION-SW-COMPONENT-TYPE"
                       and any(ch["tag"] == "R-PORT-PROTOTYPE" for ch in c["children"])),
                      producer)
    sc = ["# Signal Chains (end-to-end data flow)", ""]
    for idx, s in enumerate(sys_signals, start=1):
        base = re.sub(r"SSig$", "", s["name"])
        isig = next((n for n in isigs if n.startswith(base)), base + "ISig")
        ipdu = next((n for n in ipdus if n.startswith(base)), base + "IPdu")
        sc += [
            f"## Chain {idx}: {base}", "",
            "```",
            f"{producer} (producer, status bit)",
            f"  → {aggregator} (aggregates into CombinedStatus)",
            f"    → system signal: {s['name']}",
            f"      → I-Signal: {isig}",
            f"        → I-PDU: {ipdu}",
            "```",
            f"**Endpoints:** producer `{producer}` → network PDU `{ipdu}`",
            f"**Cut analysis:** removing `{producer}` breaks this chain at the source.",
            "",
        ]
    write_kb_file_impl("_index/signal-chains.md", "\n".join(sc) + "\n")

    # ---- detail files (Impact Tags + identity) ----
    producers_in_chains = {producer, aggregator}
    for c in components:
        net = "yes" if c["name"] in producers_in_chains or reverse.get(c["path"]) else "no"
        deps = sorted(type_name.get(t, _short(t)) for t in reverse.get(c["path"], set()))
        body = [
            f"# {c['name']}", "",
            "## Impact Tags", "",
            f"- **type:** {c['tag']}",
            "- **safety-relevant:** unknown",
            f"- **network-connected:** {net}",
            f"- **depended-on-by:** {', '.join(deps) if deps else 'None'}",
            "",
            "## Component Information", "",
            "| Field | Value |", "|-------|-------|",
            f"| Name | {c['name']} |",
            f"| Type | {c['tag']} |",
            f"| UUID | {c['uuid']} |",
            f"| Source Reference | {c['file']}:{c['line']} ({c['path']}) |",
            "",
        ]
        write_kb_file_impl(f"components/{c['name']}.md", "\n".join(body) + "\n")

    for i in interfaces:
        write_kb_file_impl(
            f"interfaces/{i['name']}.md",
            f"# {i['name']}\n\n| Field | Value |\n|-------|-------|\n"
            f"| Type | {i['tag']} |\n| UUID | {i['uuid']} |\n"
            f"| Source Reference | {i['file']}:{i['line']} ({i['path']}) |\n",
        )

    for s in systems:
        write_kb_file_impl(
            f"system/{s['name']}.md",
            f"# {s['name']}\n\n| Field | Value |\n|-------|-------|\n"
            f"| Type | {s['tag']} |\n| UUID | {s['uuid']} |\n"
            f"| Source Reference | {s['file']}:{s['line']} ({s['path']}) |\n",
        )

    # ---- README + stats ----
    st = scan["stats"]
    write_kb_file_impl(
        "README.md",
        f"# AUTOSAR ARXML Knowledge Base\n\nGenerated KB. Components: "
        f"{st['components']}, interfaces: {st['interfaces']}, systems: {st['systems']}.\n",
    )
    write_kb_file_impl(
        "_index/stats.md",
        "# Knowledge Base Statistics\n\n| Metric | Count |\n|--------|------:|\n"
        + f"| Source ARXML files | {st['source_files']} |\n"
        + f"| Components | {st['components']} |\n"
        + f"| Interfaces | {st['interfaces']} |\n"
        + f"| Systems | {st['systems']} |\n"
        + f"| Indexed elements | {st['indexed_elements']} |\n",
    )


# =========================================================================== #
# Analyze: navigate the KB -> fill the envelope
# =========================================================================== #


class ReferenceAnalyzeAgent:
    """Answers a change request with the real KB navigation tools."""

    _PROMPT_RE = re.compile(r'repo "([^"]+)":\s*(.*)$', re.DOTALL)

    def structured_output(self, schema, prompt: str):
        m = self._PROMPT_RE.search(prompt)
        repo_id = m.group(1) if m else "?"
        change_request = (m.group(2).strip() if m else prompt).strip()
        return synthesize(change_request)


def _interface_users(interface_path: str) -> list:
    """Providers + requirers of an interface, from the Interface Usage table."""
    usage = kb.section(kb_read_impl("_index/dependency-graph.md"), "Interface Usage")
    users: list = []
    for cells in kb.table_rows(usage):
        if len(cells) < 3:
            continue
        link = kb.parse_link(cells[0])
        ipath = link[0] if link else cells[0]
        if ipath != interface_path:
            continue
        for col in (cells[1], cells[2]):
            for name in col.split(","):
                name = name.strip()
                if name and "None" not in name and name not in users:
                    users.append(name)
    return users


def _choose(change_request: str, matches: list) -> Optional[dict]:
    """Pick the best match using request keywords for type bias (what the real
    LLM does with context — "interface" vs "component" vs "signal/bus")."""
    if not matches:
        return None
    cr = change_request.lower()

    def bias(m: dict) -> int:
        t = m.get("type", "")
        s = 0
        if "interface" in cr and t.endswith("-INTERFACE"):
            s += 10
        if "component" in cr and t.endswith("COMPONENT-TYPE"):
            s += 10
        if "instance" in cr and t == "SW-COMPONENT-PROTOTYPE":
            s += 10
        if any(k in cr for k in ("signal", "pdu", "bus", "network")) and (
                "SIGNAL" in t or "PDU" in t):
            s += 8
        return s

    # matches are already score-sorted; stable-sort by keyword bias on top.
    return sorted(matches, key=bias, reverse=True)[0]


def synthesize(change_request: str) -> ResultEnvelope:
    res = resolve_path_impl(change_request)
    resolved = _choose(change_request, res.get("matches", [])) or res.get("resolved")
    if not resolved:
        # Fall back to the first component in the index.
        resolved = (resolve_path_impl("Door").get("resolved")
                    or {"path": "/unknown", "type": "UNKNOWN"})
    target_path = resolved["path"]
    target_name = _short(target_path)
    target_type = resolved["type"]

    chains = trace_signals_impl(target_name).get("chains", [])

    # Interface targets -> interface-usage (providers + requirers).
    # Component targets -> reverse-dependency blast radius.
    if target_type.endswith("-INTERFACE"):
        dependents = _interface_users(target_path)
    else:
        dependents = blast_radius_impl(target_name).get("depended_on_by", [])

    # Read the target's impact tags for grounding (components carry them).
    detail = kb_read_impl(resolved.get("file") or f"components/{target_name}.md")
    network = "network-connected:** yes" in detail

    impacted = []
    nodes = [{"id": target_path}]
    edges = []
    for dep in dependents:
        dep_path = (resolve_path_impl(dep).get("resolved") or {}).get("path", dep)
        dep_type = (resolve_path_impl(dep).get("resolved") or {}).get("type", "COMPONENT")
        impacted.append({
            "id": dep_path,
            "type": dep_type,
            "hops": 1,
            "via": ["assembly/containment"],
            "severity": "high" if len(dependents) > 1 else "medium",
            "domain": "body/doors",
            "explanation": f"{dep} depends on {target_name}; removing/changing it "
                           f"breaks this relationship.",
        })
        nodes.append({"id": dep_path})
        edges.append({"from": dep_path, "to": target_path})

    # Signal/PDU impact (network reach), hops=2.
    for ch in chains:
        ep = ch.get("endpoints", "")
        pdu = ep.split("`")[-2] if "`" in ep else ch.get("title", "chain")
        impacted.append({
            "id": pdu, "type": "I-SIGNAL-I-PDU", "hops": 2,
            "via": [ch.get("title", "signal chain")],
            "severity": "high", "domain": "network",
            "explanation": f"{target_name} feeds this chain; a cut severs {pdu}.",
        })

    summary = (f"{len(dependents)} component(s) and {len(chains)} signal chain(s) "
               f"impacted by changing {target_name}.")

    rework_high = 80.0 + 40.0 * len(dependents) + 20.0 * len(chains)
    risks = []
    if network or chains:
        risks.append({
            "category": "network", "severity": "high",
            "title": "Network signal source affected",
            "detail": f"{len(chains)} signal chain(s) lose their source if {target_name} changes.",
            "revalidation_required": True,
        })
    risks.append({
        "category": "integration",
        "severity": "high" if len(dependents) > 1 else "medium",
        "title": "Downstream components require rework",
        "detail": f"{', '.join(dependents) or 'No'} component(s) depend on {target_name}.",
        "revalidation_required": bool(dependents),
    })

    envelope = {
        "change_request": change_request,
        "target_nodes": [{"id": target_path, "label": target_name, "type": target_type}],
        "what_breaks": {
            "summary": summary,
            "impacted": impacted,
            "graph": {"nodes": nodes, "edges": edges},
        },
        "what_it_costs": {
            "bom_saved": {"low": 5.0, "high": 25.0, "currency": "USD", "basis": "per-vehicle"},
            "eng_rework": {"low": 40.0, "high": rework_high, "unit": "engineer-hours"},
            "net_assessment": "favorable" if not dependents else "neutral",
            "line_items": [
                {"label": f"Rework {d}", "low": 20.0, "high": 60.0, "unit": "hours"}
                for d in dependents
            ],
        },
        "what_it_risks": {"items": risks},
        "confidence": {"level": "medium", "model_agreement": None},
    }
    return ResultEnvelope.model_validate(envelope)
