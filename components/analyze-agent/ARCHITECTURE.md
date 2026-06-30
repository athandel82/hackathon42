# Component Architecture — Analyze Agent

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.4
> **Unit type:** In-process Strands agent inside the Analyze Lambda
> **Trigger:** Analysis request (`POST /analyze`) via API Gateway

---

## 1. Purpose

Answers a natural-language change request by navigating the Markdown KB (parent §5, built by the
Ingestion Agent §4.3) with read-only navigation tools, then emits the result JSON envelope (parent
§7). Relationships are precomputed at ingestion; the agent navigates deterministic index files and
never re-derives the graph.

---

## 2. Runtime & Dependencies

| Concern | Choice |
|---|---|
| Host | AWS Lambda (Analyze) |
| Agent framework | Strands Agents SDK (in-process) |
| Model | Amazon Bedrock — Claude (one structured-output call) |
| KB source | Amazon S3 (KB tree, repo prefix) — read-only |
| Session/cache | Amazon DynamoDB |
| Observability | Amazon CloudWatch |

---

## 3. Tools (read-only KB navigation)

| Tool | Signature (conceptual) | Responsibility |
|------|------------------------|----------------|
| `kb_read` | `(path) → markdown` | Read any KB Markdown file from the repo S3 prefix. |
| `resolve_path` | `(autosar_path\|name) → file` | Map an AUTOSAR reference / name to its detail file via `_index/path-index.md`. |
| `blast_radius` | `(component) → element[]` | Read `_index/dependency-graph.md` **reverse** adjacency → elements that break if the target changes. |
| `trace_signals` | `(element) → chain[]` | Read `_index/signal-chains.md` → signals/PDUs the element feeds and where a cut severs the chain. |

All tools are read-only; the agent never mutates the KB.

---

## 4. Analysis Flow

1. **Resolve target** — map the NL request to KB element(s) via `resolve_path`, using
   `_index/components.md` / `interfaces.md` for fuzzy matches.
2. **Compute impact set** — read the reverse-dependency section of `_index/dependency-graph.md`
   plus relevant `_index/signal-chains.md` entries (precomputed, deterministic, exact).
3. **Detail on demand** — open only the needed `components/`, `interfaces/`, or `system/` files
   (Impact Tags, ports, severity hints) via `kb_read`.
4. **Synthesize** — one Bedrock (Claude) structured-output call turns the impact set + details into
   the result JSON (`what_breaks` / `what_it_costs` / `what_it_risks`).

---

## 5. Output Contract — Result JSON

Fixed envelope per parent §7. Top-level fields:

| Field | Meaning |
|---|---|
| `change_request` | Echo of the NL request. |
| `target_nodes[]` | Resolved target element(s) (`id`, `label`, `type`). |
| `what_breaks` | `summary`, `impacted[]` (`id`, `type`, `hops`, `via`, `severity`, `domain`, `explanation`), `graph` (`nodes`/`edges`). |
| `what_it_costs` | `bom_saved` range, `eng_rework` range, `net_assessment`, `line_items[]`. |
| `what_it_risks` | `items[]` (`category`, `severity`, `title`, `detail`, `revalidation_required`). |
| `confidence` | `level`; `model_agreement` reserved for a future multi-model ensemble. |

The envelope is fixed so the frontend stays a pure renderer.

---

## 6. State & Caching

| Artifact | Destination |
|---|---|
| Chat session / history | DynamoDB |
| Cached analysis result (per repo + change request) | DynamoDB |
| Logs / traces | CloudWatch |

---

## 7. Data Flow

```
POST /analyze (repo_id, change_request)
  → API Gateway → Analyze Lambda (Strands agent)
      → resolve_path:  NL target → KB element (via _index/path-index.md)
      → blast_radius:  read _index/dependency-graph.md (reverse) → impact set
      → trace_signals: read _index/signal-chains.md → affected signals/PDUs
      → kb_read:       open only needed components/interfaces/system detail files
      → Bedrock (Claude) structured output → result JSON
      → cache result → DynamoDB
  → frontend renders impact cards
```

---

## 8. Constraints & Non-Goals

- **Read-only**: navigates the KB; never re-derives relationships or writes back.
- Exactly **one** Bedrock structured-output call per request (single model).
- Impact-set correctness depends on the precomputed indices from the Ingestion Agent.
- No production HA/scale; single environment.

---

## 9. Implementation (Python)

Python 3.12 + Strands Agents SDK — same framework and packaging as the Ingestion Agent, for a
uniform deploy. The agent is built once per worker invocation: a `BedrockModel` for
navigation + synthesis, the four read-only tools from §3 registered via `@tool`, and an analysis
system prompt (`analyze_prompt.md`) loaded verbatim. The final answer is one `structured_output`
call against the Pydantic envelope (§9.4) — Strands converts the schema into a tool spec, lets the
model issue deterministic KB reads, then emits one validated result (the §8 single-call
constraint). Navigation tools are pure S3/local reads and never call the model. No XML, no graph
computation: the agent reads only the precomputed Markdown indices (parent §5). The only runtime
dependency beyond the stdlib is the Strands SDK (transitively `boto3`/`pydantic`).

### 9.1 Project Layout

> **Greenfield:** the folder currently holds only this `ARCHITECTURE.md`; the tree below is the
> target to create. Contents are inline: deps §9.2, `agent.py`/`core.py` §9.3/§9.6, envelope models
> §9.4, `Dockerfile` §11.1, env vars §11.3. Layout mirrors the Ingestion Agent so the infra
> `compute` module treats both identically.

```
components/analyze-agent/           # self-contained build unit — infra points its compute module here
├── ARCHITECTURE.md
├── pyproject.toml                 # package metadata + deps (src layout; enables `pip install -e .`)
├── requirements.txt               # pinned runtime deps (Strands + boto3)
├── requirements-dev.txt           # test/lint tooling (pytest, ruff)
├── Dockerfile                     # Lambda container image (python:3.12 base)
├── src/
│   └── analyze_agent/
│       ├── __init__.py
│       ├── core.py                # run_analyze(...) + Config.from_env() — shared by every entry point
│       ├── handler.py             # AWS Lambda adapter (POST /analyze) → run_analyze
│       ├── __main__.py            # local CLI adapter (`python -m analyze_agent …`) → run_analyze
│       ├── agent.py               # build_agent(): BedrockModel + KB tools + analysis prompt
│       ├── tools.py               # kb_read / resolve_path / blast_radius / trace_signals (@tool)
│       ├── kb.py                  # KB source abstraction (S3 prefix *or* local dir) + tiny MD parsers
│       ├── models.py              # Pydantic result envelope (parent §7) — the structured-output schema
│       ├── cache.py               # result cache + session store (DynamoDB *or* local file)
│       └── analyze_prompt.md      # analysis system prompt, packaged & loaded as system_prompt
└── tests/
    ├── test_tools.py              # deterministic KB navigation against a fixture tree
    ├── test_models.py             # envelope (de)serialization / schema validation
    └── fixtures/                  # small KB tree (subset of knowledge_base/output/sample_3_skill2)
```

> `analyze_prompt.md` is the analysis counterpart to the Ingestion Agent's `skill.md`: it tells the
> model how to navigate the KB and fill the envelope (resolve target → read reverse-deps + signal
> chains → open only needed detail files → estimate cost/risk). It is the single source of truth for
> the agent's behaviour and ships inside the package.

### 9.2 Dependencies

| Dependency | Scope | Why |
|---|---|---|
| `strands-agents>=1.0.0` | runtime | Agent loop, `@tool`, `BedrockModel`, **`structured_output`**. |
| `boto3>=1.34` | runtime | S3 (KB read), DynamoDB (cache/session), Bedrock; pinned for reproducibility. |
| `pydantic>=2` | runtime | Result-envelope models (§9.4); pinned for the schema. |
| *(stdlib)* `re`, `hashlib`, `pathlib`, `json` | runtime | Markdown-table parsing, cache-key hashing. |
| `pytest`, `ruff` | dev | Unit tests + lint. |

No XML/parsing libraries needed (Markdown, not ARXML). The dependency set is a strict subset of the
Ingestion Agent's.

### 9.3 Agent Construction (sketch)

```python
# agent.py
import os
from pathlib import Path
from strands import Agent
from strands.models import BedrockModel
from .tools import kb_read, resolve_path, blast_radius, trace_signals

PROMPT = (Path(__file__).parent / "analyze_prompt.md").read_text(encoding="utf-8")

def build_agent() -> Agent:
    model = BedrockModel(
        model_id=os.environ["BEDROCK_MODEL_ID"],
        region_name=os.environ.get("BEDROCK_REGION", os.environ["AWS_REGION"]),
        temperature=0.0,                     # deterministic navigation + synthesis
    )
    return Agent(
        model=model,
        system_prompt=PROMPT,
        tools=[resolve_path, blast_radius, trace_signals, kb_read],
        callback_handler=None,               # no console streaming in Lambda
    )
```

Each tool is a plain `@tool` function whose docstring/type hints become the schema. Tools are
read-only and deterministic; the model only sequences calls and synthesizes the envelope.

### 9.4 Output Contract as Code — Result Envelope (Pydantic)

The envelope (parent §7, §5) is expressed as Pydantic models handed to `structured_output`, so the
model must return a schema-valid object — no hand-parsing, frontend stays a pure renderer.

```python
# models.py  (abridged — full field set per parent §7)
from typing import Literal
from pydantic import BaseModel, Field

class TargetNode(BaseModel):
    id: str; label: str; type: str

class Impacted(BaseModel):
    id: str; type: str; hops: int
    via: list[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high"]
    domain: str; explanation: str

class Graph(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)

class WhatBreaks(BaseModel):
    summary: str
    impacted: list[Impacted] = Field(default_factory=list)
    graph: Graph = Field(default_factory=Graph)

class Range(BaseModel):
    low: float; high: float
    currency: str | None = None; unit: str | None = None; basis: str | None = None

class LineItem(BaseModel):
    label: str; low: float; high: float; unit: str

class WhatItCosts(BaseModel):
    bom_saved: Range; eng_rework: Range
    net_assessment: Literal["favorable", "neutral", "unfavorable"]
    line_items: list[LineItem] = Field(default_factory=list)

class RiskItem(BaseModel):
    category: str
    severity: Literal["low", "medium", "high"]
    title: str; detail: str; revalidation_required: bool

class WhatItRisks(BaseModel):
    items: list[RiskItem] = Field(default_factory=list)

class Confidence(BaseModel):
    level: Literal["low", "medium", "high"]
    model_agreement: float | None = None     # reserved for a future multi-model ensemble (parent §7)

class ResultEnvelope(BaseModel):
    change_request: str
    target_nodes: list[TargetNode]
    what_breaks: WhatBreaks
    what_it_costs: WhatItCosts
    what_it_risks: WhatItRisks
    confidence: Confidence
```

The single Bedrock call is `agent.structured_output(ResultEnvelope, change_request)` (§9.6); its
`.model_dump()` is the exact JSON the frontend consumes.

### 9.5 KB Source Binding (S3 vs local) & Tool Reads

The Ingestion Agent persists each repo's KB under `s3://$KB_BUCKET/<repo_id>/kb/` (parent §5); the
Analyze Agent reads it read-only. `kb.py` abstracts the source so the same tools work in Lambda and
locally:

| Source | Selected by | `read(rel_path)` resolves to |
|--------|-------------|------------------------------|
| **s3** | `KB_BUCKET` set | `GetObject s3://$KB_BUCKET/<repo_id>/kb/<rel_path>` |
| **local** | `--kb-dir <dir>` (no `KB_BUCKET`) | `<dir>/<repo_id>/kb/<rel_path>` on disk |

The four tools are thin readers over this source:

| Tool | Reads | Returns |
|------|-------|---------|
| `resolve_path(ref)` | `_index/path-index.md` (+ `components.md`/`interfaces.md` for fuzzy match) | concrete detail-file path + type |
| `blast_radius(component)` | **Reverse Dependencies** section of `_index/dependency-graph.md` | elements that break if the target changes |
| `trace_signals(element)` | `_index/signal-chains.md` | chains the element feeds + the hop where a cut severs them |
| `kb_read(path)` | any KB Markdown file | raw Markdown (Impact Tags, ports, severity hints) |

Parsing is minimal — regex/section-slicing helpers over the deterministic Markdown tables (parent
§5), not a general Markdown parser. The agent navigates precomputed indices, never re-derives
relationships (§8). The bound source caches read files in memory for the run (and may stage them
under `KB_CACHE_DIR`, default `/tmp`) to avoid re-fetching.

### 9.6 Shared Core & Entry Points

Every entry point is a thin adapter over one function, identical in Lambda and locally:

```python
# core.py
def run_analyze(repo_id: str, change_request: str, cfg: "Config | None" = None) -> dict:
    cfg = cfg or Config.from_env()              # resolves KB source (s3|local) + cache (ddb|file)
    hit = cache_get(cfg, repo_id, change_request)   # keyed by repo_id + normalized request (§6)
    if hit:
        return hit
    bind_kb_source(cfg, repo_id)                 # sets the per-run KB reader for the tools (contextvars)
    result = build_agent().structured_output(    # the single Bedrock structured-output call (§8)
        ResultEnvelope,
        f'Change request for repo "{repo_id}": {change_request}',
    )
    out = result.model_dump()
    cache_put(cfg, repo_id, change_request, out) # persist + record session turn
    return out
```

- **`handler.py`** (AWS Lambda): parses the `POST /analyze` body (`{ repo_id, change_request }`),
  calls `run_analyze`, returns `200` + envelope JSON (CORS per aws-infrastructure §3); `409` on a
  missing/`!READY` repo.
- **`__main__.py`** (local CLI): parses args and calls `run_analyze` directly — no API Gateway/Lambda
  (§12).
- The `@tool` functions read a per-run KB source set by `run_analyze` via a
  `contextvars.ContextVar`, so tools stay plain and stateless (same pattern as the Ingestion Agent).

`Config.from_env()` picks **s3 + DynamoDB** when `KB_BUCKET`/`RESULTS_TABLE` are set, otherwise
**local dir + file cache** — the only difference between cloud and laptop runs.

---

## 10. Invocation Model

Analysis is short (a few KB reads + one `structured_output` call), fitting the API Gateway HTTP API
30 s limit. `POST /analyze` is a single synchronous request/response — no self-invoke, no extra
resources.

| Mode | Trigger | Behavior |
|---|---|---|
| `api` (sync) | API Gateway `POST /analyze` | Validate `{ repo_id, change_request }`, call `run_analyze`, return `200 { …envelope }` (or cached). |

```
POST /analyze (repo_id, change_request)
  → API Gateway → Analyze λ (sync)
       → cache lookup (DynamoDB) ── hit ─► return cached envelope
       → resolve_path → blast_radius → trace_signals → kb_read   (read-only KB navigation)
       → Bedrock (Claude) structured_output → ResultEnvelope
       → cache put (DynamoDB) → return envelope
  → frontend renders impact cards
```

**Streaming fallback (if a request approaches 30 s):** front the same handler with a Lambda Function
URL + response streaming (parent §4.2, aws-infrastructure §3) — `run_analyze` unchanged, only the
adapter differs. Documented escape hatch, not the default. A warm cache (§6) makes repeat requests
effectively instant.

---

## 11. Packaging & Lambda Configuration (Terraform alignment)

The infra `compute` module (aws-infrastructure §6) provisions this Lambda exactly as the Ingest
Lambda.

### 11.1 Packaging — container image (recommended)

Build on the official Lambda Python base image; the `compute` module references the ECR image
(`package_type = "Image"`).

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/analyze_agent/ ${LAMBDA_TASK_ROOT}/analyze_agent/
CMD ["analyze_agent.handler.handler"]
```

> Zip is viable (small dep set) but requires building `pydantic-core` against the Lambda runtime; the
> container image is preferred and matches the Ingest Lambda.

### 11.2 Lambda configuration

| Setting | Value | Rationale |
|---|---|---|
| Runtime | Container image, Python 3.12 base | §11.1 |
| Handler | `analyze_agent.handler.handler` | Single sync dispatcher (§10). |
| Memory | 1024 MB | Markdown reads + one model call; lighter than Ingest (no XML parsing). |
| Timeout | 60 s | Headroom over the typical sub-30 s run; ≤ the sync API path. |
| Ephemeral storage (`/tmp`) | 512 MB (default) | Optional in-run KB staging (§9.5). |
| Architecture | `x86_64` | Matches Ingest; avoids cross-build friction. |
| Reserved concurrency | low (2–5) | Prototype; bounds concurrent Bedrock calls. |

### 11.3 Environment variables (set by the `compute` module)

| Env var | Source (TF) | Purpose |
|---|---|---|
| `KB_BUCKET` | `storage` module output | S3 bucket holding the KB tree (read-only). |
| `RESULTS_TABLE` | `storage` module output | DynamoDB table for cached results + chat sessions. |
| `BEDROCK_MODEL_ID` | `compute` variable | Claude model id for navigation + structured output. |
| `BEDROCK_REGION` | `compute` variable / region | Bedrock invocation region. |
| `KB_CACHE_DIR` | default `/tmp` | Optional in-run KB staging dir (§9.5). |
| `LOG_LEVEL` | `compute` variable | Logging verbosity. |

> No `GITHUB_TOKEN_SECRET_ARN` or `WORKER_FUNCTION_NAME` — analysis neither fetches repos nor
> self-invokes (§10). A strict subset of the Ingest Lambda's variables.

### 11.4 IAM (refines aws-infrastructure §5 — Analyze Lambda role)

| Action | Resource | Used by |
|---|---|---|
| `s3:GetObject`, `s3:ListBucket` | `KB_BUCKET` (+ `<repo_id>/kb/*`) | KB navigation tools (§9.5). **Read-only — no `PutObject`.** |
| `dynamodb:GetItem`, `PutItem`, `UpdateItem` | `RESULTS_TABLE` | Result cache + session turns (§6). |
| `bedrock:InvokeModel` (+ `…WithResponseStream`) | the configured model | Strands `BedrockModel` / streaming fallback (§10). |
| `logs:CreateLogGroup/Stream`, `PutLogEvents` | function log group | CloudWatch. |

Matches aws-infrastructure §5; the read-only S3 grant is the key contrast with the Ingest role.

### 11.5 Deployment Contract (consumed by the infra `compute` module)

| Item | Value |
|---|---|
| Build context | `components/analyze-agent/` |
| Dockerfile | `components/analyze-agent/Dockerfile` |
| Image entry (`CMD`) | `analyze_agent.handler.handler` |
| Importable package | `analyze_agent` (src layout; copied into the image) |
| Function env vars | §11.3 |
| Function IAM | §11.4 |
| Invocation | synchronous `POST /analyze`; **no** async worker (§10) |

Terraform builds/pushes the image (ECR) and creates the Lambda with `package_type = "Image"`, the
§11.3 env vars, and the §11.4 role. The local CLI (§12) shares the package but is not part of the
deployed entry path.

---

## 12. Local Development & Run (no Lambda)

The full pipeline runs on a laptop with local AWS credentials; the only always-required AWS call is
Bedrock. `boto3`/Strands use the default credential chain (`AWS_PROFILE`, env vars, or SSO) — no
Lambda, API Gateway, S3, or DynamoDB required. The natural loop is **ingest → analyze** offline: run
the Ingestion Agent's local CLI to produce `./out/<repo_id>/kb/`, then point this agent at it.

```bash
cd components/analyze-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                          # src-layout editable install (pyproject.toml)

export AWS_PROFILE=my-dev                         # local creds — used for Bedrock
export AWS_REGION=us-west-2
export BEDROCK_MODEL_ID=<claude-model-id>

# LOCAL mode — read the KB the Ingestion Agent wrote under ./out; no S3/DynamoDB touched
python -m analyze_agent \
  --kb-dir ../ingestion-agent/out \
  --repo-id patrikja__autosar__master \
  --change-request "remove the rear-door module"

# AWS mode — local process with local creds, reads real S3 + caches to DynamoDB
export KB_BUCKET=my-dev-bucket RESULTS_TABLE=my-dev-results
python -m analyze_agent --repo-id patrikja__autosar__master \
  --change-request "remove the rear-door module"
```

For zero-cost iteration without ingesting first, point `--kb-dir` at the committed sample
(`knowledge_base/output/sample_3_skill2` arranged under `<repo_id>/kb/`).

### Run / source modes

Both modes share code through `run_analyze` (§9.6); only the KB source + cache differ:

| Mode | Selected by | KB read from | Cache / session |
|------|-------------|--------------|-----------------|
| **local** | `--kb-dir <dir>` (or no `KB_BUCKET`) | `<dir>/<repo_id>/kb/` | `<dir>/<repo_id>/results.json` (file) |
| **aws** | `KB_BUCKET` + `RESULTS_TABLE` set | `s3://$KB_BUCKET/<repo_id>/kb/` | DynamoDB item |

### Testing tiers

- **Offline unit** (`pytest`) — the deterministic tools against `tests/fixtures/` (subset of
  `knowledge_base/output/sample_3_skill2/`). No AWS, no Bedrock.
- **Envelope schema** (`pytest`) — `models.py` round-trips and rejects malformed objects (frontend
  contract, parent §7).
- **Local end-to-end** — `python -m analyze_agent --kb-dir …` against the sample KB; assert a
  schema-valid `ResultEnvelope` and that `what_breaks.impacted` contains the expected elements
  (e.g. "remove Door" → DoorControl + EDC + the 4 `CombinedStatus*` chains).
- **Q&A benchmark** — reuse `knowledge_base/validation/` to confirm blast-radius answers match
  validated expectations.
- **AWS integration** — set `KB_BUCKET`/`RESULTS_TABLE` and re-run locally to exercise the real S3
  read + DynamoDB cache paths before deploy.

`ruff` for lint.

---

## 13. Gaps Identified & Resolved

Closes gaps open in the prior (§1–§8) architecture, mirroring the Ingestion Agent's resolutions:

| # | Gap (was) | Resolution |
|---|---|---|
| 1 | No language/runtime, deps, or project layout. | §9 — Python 3.12, Strands SDK, Markdown-only reads, layout, agent sketch. |
| 2 | "One Bedrock call" stated, mechanism undefined. | §9/§9.6 — `agent.structured_output(ResultEnvelope, …)`; deterministic navigation reads + single synthesis call. |
| 3 | Result envelope had no machine-checked form. | §9.4 — Pydantic `ResultEnvelope`; `.model_dump()` is the API JSON. |
| 4 | Analysis system prompt unspecified. | §9.1/§9.3 — packaged `analyze_prompt.md` loaded as `system_prompt`. |
| 5 | Tool→S3/local KB binding undefined. | §9.5 — `kb.py` source abstraction (s3 \| local) + Markdown-table parsers; in-run caching. |
| 6 | Cache/session keying unspecified. | §6 + §9.6 — key = `repo_id` + normalized `change_request`; DynamoDB (aws) / file (local). |
| 7 | Invocation/timeout vs API GW 30 s unstated. | §10 — single sync call; Function URL streaming fallback. |
| 8 | Packaging, sizing, env, TF contract undefined. | §11 — container image, sizing, env + read-only IAM tables. |
| 9 | No way to run without a Lambda. | §9.6 + §12 — shared `run_analyze`, local CLI, local KB source. |
| 10 | Build/deploy hand-off implicit. | §11.5 — explicit deployment contract. |

**Remaining (accepted) constraints, not gaps:**

- **Cost & risk are model estimates, not grounded data.** The KB carries no BOM prices or
  engineer-hour figures, so `what_it_costs` and `what_it_risks.*.severity` are heuristic judgments
  from impact-set size and element types. A future tier can ground these in a parts/labor catalog
  (the "propose the fix" tier). `confidence.level` reflects this; `confidence.model_agreement` stays
  reserved for a future ensemble.
- **Impact-set correctness depends on the ingestion indices** (§8). Incomplete
  `dependency-graph.md` / `signal-chains.md` → incomplete blast radius; the agent must not re-derive.
- **NL → target resolution is fuzzy.** Mapping free text to a KB element relies on the model matching
  `components.md`/`interfaces.md`; ambiguous requests may resolve imperfectly. Out of scope for the
  prototype (parent §2 Non-Goals).

---

## 14. Prototype Simplifications

Each is a one-line change to revert if the product grows:

| Simplification | Instead of | Why it's safe |
|---|---|---|
| **Synchronous `/analyze`** (no worker) | Async self-invoke / streaming by default | A few reads + one model call fits the 30 s window; streaming is a fallback (§10). |
| **One `structured_output` call** | Separate navigate + synthesize passes | Strands runs navigation + typed synthesis in one call (§8). |
| **Tiny regex/section parsers** in `kb.py` | A general Markdown/AST parser | Ingestion emits fixed, deterministic tables (parent §5). |
| **In-memory KB read cache** | A shared cache layer / S3 Select | One request reads a handful of small index files. |
| **Flat module layout** | `tools/` + `kb/` subpackages | Fewer files; `Config.from_env()` lives in `core.py` — matches Ingestion. |
| **Model-estimated cost/risk** | A grounded parts/labor catalog | No cost data in the ARXML; heuristic ranges suffice for the demo (§13). |
| **`x86_64`** | `arm64` | Avoids cross-build friction; matches Ingestion. |
| **Single results table** (cache + sessions) | Separate cache and session tables | One table with a simple key scheme covers both at prototype scale. |

Not simplified (on purpose): container-image packaging (uniform with Ingest, reliable with the
Strands deps), the Pydantic envelope (the machine-checked frontend contract), and read-only S3
access (a hard safety property — parent §8, aws-infrastructure §5).
