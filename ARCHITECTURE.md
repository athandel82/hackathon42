# Architecture — ~~S~~DV "Still Defined Vehicle"

> **Status:** Prototype / Hackathon (`hackathon42`)
> **Scope:** Read-only impact analysis for vehicle ECU changes.
> **Cloud:** AWS-only. **IaC:** Terraform. **Last updated:** 2026-06-30

---

## 1. Overview

SDV reads a vehicle's existing engineering data (AUTOSAR **ARXML** ECU Extracts) and,
given a plain-English change request — returns the **blast radius** of that change:

- **What breaks** — every downstream element the change touches, traced exactly.
- **What it costs** — hardware/BOM saved vs. engineering rework, as a defensible range.
- **What it risks** — broken networks, re-validation triggers, safety/diagnostic implications.

This document describes the **lean prototype** architecture: a tool-using agent
turns the ARXML into a relationship-aware **Markdown knowledge base**, and a second
agent navigates that KB to answer change requests — deployed on Terraform-friendly
AWS services with a frontend served directly.

---

## 2. Goals & Non-Goals

### Goals
- Ingest an ARXML ECU Extract from a GitHub repository.
- Build an exact, deterministic, relationship-aware **Markdown knowledge base** of the vehicle's electronics.
- Accept natural-language change requests via a simple web chat.
- Return a structured, visually rich impact report (breaks / cost / risk).
- Deploy on AWS via Terraform — serverless backend (Lambda + API Gateway), with the React frontend served from a small EC2 VM.

### Non-Goals (prototype)
- Production-grade HA, multi-region, or scale.
- Writing back or modifying any engineering artifact (read-only by design).
- Cost optimization (quality and demo reliability are prioritized).
- Exhaustive ARXML coverage — only the subset needed for a convincing demo.

---

## 3. Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│  React + Cloudscape SPA                                        │
│  Served by a web server directly on a VM (public DNS)          │
│  Screen 1: paste GitHub URL   Screen 2: chat + impact cards    │
└───────────────┬────────────────────────────────────────────────┘
                │  HTTPS — HTTP API (open, no authorizer)
        ┌───────▼─────────────────┐
        │  API Gateway            │
        │  (HTTP API)             │
        └───┬───────────────────┬─┘
            │                   │
   ┌────────▼────────────┐   ┌──▼──────────────────────────────────┐
   │ Ingest λ            │   │ Analyze λ  (Strands agent in-proc)  │
   │ Strands agent +     │   │  1. resolve target via path-index   │
   │ tools:              │   │  2. read _index/dependency-graph    │
   │  • scan repo:       │   │     (reverse) + signal-chains →     │
   │    download tarball,│   │     impact set                      │
   │    list/read, parse │   │  3. open only the needed detail     │
   │  • write KB file    │   │     files (detail-on-demand)        │
   │ → indexed Markdown  │   │  4. Bedrock (Claude) structured     │
   │   knowledge base    │   │     output → breaks/cost/risk JSON  │
   └─────┬───────────────┘   └──────────────┬──────────────────────┘
         │                                  │
     ┌───▼──────────────────────────────────▼──────┐
     │  S3        (raw ARXML + Markdown KB tree)   │
     │  DynamoDB  (repos, sessions, cached results)│
     │  Secrets Manager (GitHub token, optional)   │
     └─────────────────────────────────────────────┘
            Amazon Bedrock — Claude (single model)
```

---

## 4. Components

Each component below has a detailed software-unit architecture document under `components/`:

| Component | Section | Unit architecture |
|-----------|---------|-------------------|
| Frontend — Web App | 4.1 | [`components/frontend/ARCHITECTURE.md`](components/frontend/ARCHITECTURE.md) |
| Ingestion Agent | 4.3 | [`components/ingestion-agent/ARCHITECTURE.md`](components/ingestion-agent/ARCHITECTURE.md) |
| Analyze Agent | 4.4 | [`components/analyze-agent/ARCHITECTURE.md`](components/analyze-agent/ARCHITECTURE.md) |
| AWS Infrastructure (API + storage + Terraform) | 4.2, 4.5, 9 | [`components/aws-infrastructure/ARCHITECTURE.md`](components/aws-infrastructure/ARCHITECTURE.md) |

### 4.1 Frontend — Web App
- **Stack:** React + Vite, **Cloudscape Design System**.
- **Hosting:** built to static assets (`vite build`) and served by a lightweight web
  server (nginx, or `vite preview`/a static file server) **running on the same EC2 VM**.
  The app is reachable directly at the VM's **public DNS name** (`http://<ec2-public-dns>/`).
- **Auth:** N/A.
- **Config:** the API base URL is read at **runtime** from a small `config.json` (the
  deployed source of truth; an optional build-time `VITE_API_BASE_URL` override exists for
  local dev); pointing the SPA at the API Gateway URL is the only wiring needed.
- **Screens:**
  - *Onboarding* — paste a GitHub URL, trigger ingestion, watch status.
  - *Chat + Dashboard* — enter change requests; render the result JSON as impact cards:
    a **What Breaks** dependency tree/graph, a **What it Costs** savings-vs-rework range,
    a **What it Risks** severity-sorted list.

### 4.2 API Layer
- **Amazon API Gateway (HTTP API)** — single API for both ingestion and chat.
- **No authorizer — all routes are open.**
- **CORS `*`** (wildcard) so the SPA can call the API directly; using `*` also breaks the
  EC2↔API circular dependency (the API need not be told the VM's public-DNS origin).
- **Ingestion is asynchronous:** `POST /ingest` returns `202 { repo_id }` immediately and the
  Ingest Lambda **async self-invokes** a worker (beating the API Gateway 30 s limit); the
  frontend polls `GET /status` until `READY`/`FAILED`.
- **Analysis is synchronous:** `POST /analyze` returns the result within the 30 s window. A
  **Lambda Function URL with response streaming** is a documented fallback if a request nears
  the limit — no WebSocket connection management.

### 4.3 Ingestion Agent (Markdown KB builder)
A **Strands agent** running in-process inside the Ingest Lambda, triggered by the
onboarding request. The agent is driven by the
**"Generate AUTOSAR ARXML Knowledge Base (v2 — Indexed & Relationship-Aware)" skill** and
calls a small set of deterministic **tools** to produce an indexed Markdown knowledge base:

| Tool | Responsibility |
|------|----------------|
| `scan_repo` | One deterministic call: fetch the GitHub **tarball** (`/archive/refs/heads/<branch>.tar.gz`, no git clone), extract, enumerate every `.arxml`, and parse all elements (SHORT-NAME, tag, UUID, full AUTOSAR path, ports, connectors, signal mappings). |
| `write_kb_file` | Write a Markdown file to the KB tree under the repo's S3 prefix. |
| `record_status` | Update repo metadata / ingestion status in DynamoDB. |

The agent follows the skill's **index-first** procedure:

1. **Plan** the batch (small single-pass vs. large multi-pass) and record it in `_index/stats.md`.
2. **First pass — skeleton index:** scan every file for cheap identifying data and write
   `_index/path-index.md`, `components.md`, `interfaces.md`, `platform-types.md`, `port-map.md`.
3. **Resolve the relationship graph:** compute forward + reverse dependencies and composition
   containment → `_index/dependency-graph.md`, `composition-tree.md`.
4. **Trace signal chains:** follow runnable → port → connector → system signal → I-Signal → I-PDU
   end-to-end → `_index/signal-chains.md`.
5. **Second pass — detail files (batched):** generate per-element `components/`, `interfaces/`,
   `platform/`, `system/` files, populating each one's Dependencies / Impact Tags from the
   already-computed graph (not re-derived).
6. **Finalize:** write `README.md` (navigation guide + metadata) and complete `_index/stats.md`.

Every cross-reference is a relative Markdown link with the AUTOSAR path as text; all UUIDs and
paths are preserved verbatim; unresolved references are tagged `(UNRESOLVED)` and listed in
`_index/stats.md`. The whole KB tree is persisted to **S3**; repo metadata + status to **DynamoDB**.

### 4.4 Analyze Agent (Agentic Core)
A **single Strands agent** running in-process inside the Analyze Lambda. It answers change
requests by **navigating the Markdown KB** (§5) built by the Ingestion Agent (§4.3) —
index-first, detail-on-demand — using read-only **KB navigation tools**:

| Tool | Responsibility |
|------|----------------|
| `kb_read(path)` | Read any KB Markdown file from the repo's S3 prefix. |
| `resolve_path(autosar_path)` | Look up `_index/path-index.md` to turn an AUTOSAR reference / name into the concrete detail file. |
| `blast_radius(component)` | Read `_index/dependency-graph.md` (**reverse** adjacency) to get the set of elements that break if the target changes. |
| `trace_signals(element)` | Read `_index/signal-chains.md` to find the network signals/PDUs the element feeds, and where a cut severs the chain. |

Flow:
1. **Resolve target** — map the NL request to concrete KB element(s) via `resolve_path`
   (and `_index/components.md` / `interfaces.md` for fuzzy name matches).
2. **Compute impact set** — read the **reverse dependency** section of
   `_index/dependency-graph.md` plus the relevant `_index/signal-chains.md` entries. These
   are precomputed and deterministic, so the impact set is exact (no graph re-derivation).
3. **Detail on demand** — open only the few `components/`, `interfaces/`, or `system/` detail
   files needed for the affected elements (e.g. to read Impact Tags, ports, severity hints).
4. **Synthesize** — one **Amazon Bedrock (Claude)** structured-output call turns the gathered
   impact set + details into the strict result JSON (`what_breaks` / `what_it_costs` /
   `what_it_risks`).
- Session/history stored in **DynamoDB**; logs/traces in **CloudWatch**.

### 4.5 Storage & Supporting Services
- **Amazon S3** — raw ARXML and the generated **Markdown KB tree** (one prefix per repo).
- **Amazon DynamoDB** — repos, ingestion status, chat sessions, cached results.
- **AWS Secrets Manager** — GitHub token (only if private repos are needed).
- **Amazon Bedrock** — Claude model invocation.
- **Amazon EC2** — the VM that serves the React frontend (and nothing else).

---

## 5. Data Model — Indexed Markdown Knowledge Base

The ARXML extract is normalized into a **tree of Markdown files**, not a single graph blob.
The layout is **index-first, detail-on-demand**: a small `_index/` layer holds the global,
relationship-aware navigation data; per-element detail files hold the rest. This is the artifact
the Ingest agent writes and the Analyze agent reads.

**Layout** (one prefix per repo in S3):

```
<repo-prefix>/
├── README.md                       # Overview + generation metadata + how to navigate
├── _index/                         # Global, agent-first navigation layer
│   ├── path-index.md               # AUTOSAR path → file + type (resolve any reference)
│   ├── components.md               # All components: type, package, P/R-port counts, file
│   ├── interfaces.md               # All interfaces: type, #providers, #requesters, file
│   ├── platform-types.md           # All base/impl types: category, #consumers, file
│   ├── dependency-graph.md         # Forward + reverse adjacency + interface usage (blast-radius core)
│   ├── port-map.md                 # Every component.port → interface + direction
│   ├── signal-chains.md            # End-to-end data-flow traces (runnable → … → I-PDU)
│   ├── composition-tree.md         # Hierarchical tree of all compositions
│   └── stats.md                    # Counts, processing mode, unresolved references
├── components/<Name>.md            # One per SW component (ports, runnables, dependencies, impact tags)
├── interfaces/<Name>.md            # One per interface (data elements / operations, usage)
├── platform/BaseTypes.md           # All SW base types, grouped
├── platform/ImplementationDataTypes.md  # All impl data types + compu methods, grouped
└── system/<Name>.md                # One per SYSTEM element (signal/comm mappings, I-Signals, I-PDUs)
```

**Element classification** (what becomes which file):

| ARXML element | Lands in |
|---------------|----------|
| `*-SW-COMPONENT-TYPE` (APPLICATION, SERVICE, COMPOSITION, SENSOR-ACTUATOR, …) | `components/<Name>.md` |
| `SENDER-RECEIVER` / `CLIENT-SERVER` / `MODE-SWITCH` / `NV-DATA` / … `-INTERFACE` | `interfaces/<Name>.md` |
| `SW-BASE-TYPE`, `IMPLEMENTATION-DATA-TYPE`, `COMPU-METHOD`, application data types | `platform/*.md` |
| `SYSTEM` (esp. `ECU_EXTRACT`) | `system/<Name>.md` |
| `I-SIGNAL`, `SYSTEM-SIGNAL`, `I-SIGNAL-I-PDU`, `FRAME`, `CAN-CLUSTER`, mappings | captured in the system file and `signal-chains.md` (no standalone files) |

**Blast radius** is *precomputed at ingestion* and read back at analysis time. It is the
**reverse-dependency adjacency** in `_index/dependency-graph.md` (which components break if
this one changes) combined with `_index/signal-chains.md` (which network signals/PDUs lose
their source when a chain is cut). The Analyze agent does not re-derive relationships — it
navigates these deterministic index files, then opens detail files as needed.

**Relationship blocks** (excerpt — from `_index/dependency-graph.md`):
```markdown
## Reverse Dependencies (blast radius — who breaks if this changes)
| Component   | Depended On By        |
|-------------|-----------------------|
| Door        | DoorControl, EDC      |
| DoorControl | EDC                   |
| IoHwAb      | DoorControl, EDC      |
| EDC         | _None_ (root)         |
```

**Reference resolution** (excerpt — from `_index/path-index.md`): every AUTOSAR path resolves
to a concrete file via a relative Markdown link, with all UUIDs/paths preserved verbatim:
```markdown
| AUTOSAR Path                | Type                            | File                                  |
|-----------------------------|---------------------------------|---------------------------------------|
| /Demo/Door/Door             | APPLICATION-SW-COMPONENT-TYPE   | [components/Door.md](../components/Door.md) |
| /Demo/Interfaces/DoorStatus | SENDER-RECEIVER-INTERFACE       | [interfaces/DoorStatus.md](../interfaces/DoorStatus.md) |
```

Unresolved references are tagged `(UNRESOLVED)` inline and listed in `_index/stats.md`.

---

## 6. Data Flows

### 6.1 Ingestion
```
User submits GitHub URL
   → API Gateway (open) → Ingest Lambda (api): validate, write PENDING, async self-invoke → 202 { repo_id }
   → Ingest Lambda (worker, Strands agent + skill)
       → scan_repo (tarball fetch + extract + parse, deterministic)
       → build _index/ (path-index, components, interfaces, port-map)
       → resolve relationship graph (dependency-graph, composition-tree)
       → trace signal-chains
       → write_kb_file ×N → Markdown KB tree → S3 (repo prefix)
       → record_status (READY/FAILED) → DynamoDB
   → frontend polls GET /status until READY
```

### 6.2 Analysis
```
User submits change request (chat)
   → API Gateway (open) → Analyze Lambda (Strands agent)
       → resolve_path: NL target → KB element (via _index/path-index.md)
       → blast_radius: read _index/dependency-graph.md (reverse) → impact set
       → trace_signals: read _index/signal-chains.md → affected network signals/PDUs
       → kb_read: open only the needed components/interfaces/system detail files
       → Bedrock (Claude) structured output → result JSON
       → cache result → DynamoDB
   → frontend renders impact cards
```

---

## 7. API & Result Contract

The Analyze Lambda returns a fixed JSON envelope so the frontend is pure rendering.

```json
{
  "change_request": "remove the rear-door module",
  "target_nodes": [{ "id": "ECU_RDM_01", "label": "Rear Door Module", "type": "ECU" }],
  "what_breaks": {
    "summary": "12 downstream elements affected across 3 buses.",
    "impacted": [
      {
        "id": "SIG_window_pos", "type": "Signal", "hops": 2,
        "via": ["PDU_door_status", "FRAME_body_can_3"],
        "severity": "high", "domain": "Body",
        "explanation": "Window position signal is sourced only by RDM."
      }
    ],
    "graph": { "nodes": [], "edges": [] }
  },
  "what_it_costs": {
    "bom_saved":  { "low": 18.0, "high": 26.0, "currency": "USD", "basis": "per-vehicle" },
    "eng_rework": { "low": 120, "high": 280, "unit": "engineer-hours" },
    "net_assessment": "favorable",
    "line_items": [{ "label": "Re-map window signals", "low": 40, "high": 90, "unit": "hours" }]
  },
  "what_it_risks": {
    "items": [
      {
        "category": "network", "severity": "high",
        "title": "Body CAN load drops below validated profile",
        "detail": "...", "revalidation_required": true
      }
    ]
  },
  "confidence": { "level": "medium", "model_agreement": 0.82 }
}
```

- `what_breaks.graph` feeds a dependency-tree visual.
- `what_it_costs` ranges feed a bar/range widget.
- `what_it_risks.items` feed a severity-sorted list.
- `confidence.model_agreement` is reserved for a future multi-model ensemble upgrade.

---

## 8. Technology Stack

| Concern | Service / Tool |
|---|---|
| Frontend | React + Vite + Cloudscape Design System |
| Frontend hosting | Static build served by nginx on an **Amazon EC2** VM (public DNS) |
| Auth | **None** (open endpoints — prototype only) |
| API | Amazon API Gateway (HTTP API, no authorizer) |
| Compute | AWS Lambda × 2 (Ingest agent, Analyze agent) |
| Agent framework | Strands Agents SDK (in-process) |
| Knowledge base | Indexed **Markdown** tree (skill-generated) in S3 |
| LLM | Amazon Bedrock — Claude |
| Object storage | Amazon S3 |
| State / cache | Amazon DynamoDB |
| Secrets | AWS Secrets Manager |
| Observability | Amazon CloudWatch |
| IaC | Terraform |

---

## 9. Infrastructure — Terraform Layout

All resources are first-class AWS-provider resources.

```
infra/
├── main.tf            # provider, backend (S3 + DynamoDB lock), module wiring
├── variables.tf
├── outputs.tf
├── modules/
│   ├── frontend/      # EC2 instance + security group; user-data builds/serves the React app (public DNS)
│   ├── api/           # HTTP API + routes (open, no authorizer) + CORS
│   ├── compute/       # Ingest & Analyze Lambdas, IAM roles, Bedrock permissions
│   └── storage/       # S3 buckets (raw ARXML + Markdown KB) + DynamoDB tables
└── envs/
    └── dev/           # single environment is sufficient for the prototype
```
