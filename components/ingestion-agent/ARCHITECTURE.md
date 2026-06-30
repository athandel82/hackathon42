# Component Architecture — Ingestion Agent

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.3
> **Unit type:** In-process Strands agent inside the Ingest Lambda
> **Trigger:** `POST /ingest` via API Gateway

---

## 1. Purpose

Turns a vehicle's AUTOSAR ARXML ECU Extract (fetched from a GitHub repo) into an indexed,
relationship-aware **Markdown knowledge base (KB)** in S3. Driven by the *"Generate AUTOSAR
ARXML Knowledge Base (v2 — Indexed & Relationship-Aware)"* skill. Extraction is deterministic;
the LLM only sequences tool calls per the skill procedure.

---

## 2. Runtime & Dependencies

| Concern | Choice |
|---|---|
| Host | AWS Lambda (Ingest) |
| Agent framework | Strands Agents SDK (in-process) |
| Model | Amazon Bedrock — Claude |
| Input source | GitHub tarball (`/archive/refs/heads/<branch>.tar.gz`) |
| Output store | Amazon S3 (KB tree, one prefix per repo) |
| Metadata/status | Amazon DynamoDB |
| Secrets | AWS Secrets Manager (GitHub token, private repos only) |
| Observability | Amazon CloudWatch |

---

## 3. Tools (deterministic)

Three tools — download/list/read/parse are collapsed into one `scan_repo` call so the model
spends turns authoring the index, graph, signal chains, and detail files.

| Tool | Signature (conceptual) | Responsibility |
|------|------------------------|----------------|
| `scan_repo` | `(github_url, branch) → element[]` | Fetch the GitHub **tarball** (no clone), extract, enumerate every `.arxml`, parse all elements (SHORT-NAME, tag, UUID, AUTOSAR path, ports, connectors, signal mappings). |
| `write_kb_file` | `(rel_path, markdown)` | Write one Markdown file into the KB working tree (synced to S3 on finalize). |
| `record_status` | `(repo_id, status, meta)` | Update repo metadata / ingestion status in DynamoDB. |

---

## 4. Procedure (index-first)

1. **Plan** the batch — single-pass vs. multi-pass; record in `_index/stats.md`.
2. **First pass — skeleton index:** write `_index/path-index.md`, `components.md`,
   `interfaces.md`, `platform-types.md`, `port-map.md`.
3. **Resolve relationship graph:** forward + reverse dependencies and composition containment →
   `_index/dependency-graph.md`, `composition-tree.md`.
4. **Trace signal chains:** runnable → port → connector → system signal → I-Signal → I-PDU →
   `_index/signal-chains.md`.
5. **Second pass — detail files:** per-element `components/`, `interfaces/`, `platform/`,
   `system/` files; Dependencies / Impact Tags populated from the computed graph (not re-derived).
6. **Finalize:** write KB `README.md` and complete `_index/stats.md`.

---

## 5. Output Contract — KB Invariants

- Every cross-reference is a **relative Markdown link** with the AUTOSAR path as link text.
- All **UUIDs and AUTOSAR paths preserved verbatim**.
- Unresolved references tagged `(UNRESOLVED)` inline **and** listed in `_index/stats.md`.
- **Blast radius precomputed:** reverse-dependency adjacency in `_index/dependency-graph.md` +
  signal-source coverage in `_index/signal-chains.md`. Detail files carry derived Impact Tags;
  never re-derived downstream.
- Element classification follows parent §5 (signal/frame elements live in the system file and
  `signal-chains.md`, no standalone files).

---

## 6. Persistence

| Artifact | Destination |
|---|---|
| Raw ARXML | S3 (repo prefix) — *optional (see §9.4)* |
| Markdown KB tree | S3 (repo prefix, layout per parent §5) |
| Repo metadata + status | DynamoDB |
| Logs / traces | CloudWatch |

Status: `PENDING → READY` on success, `→ FAILED` on error; polled by the frontend.

---

## 7. Data Flow

```
POST /ingest (github_url)
  → API Gateway → Ingest Lambda (Strands agent + skill)
      → scan_repo (tarball + parse)
      → build _index/ (path-index, components, interfaces, port-map)
      → resolve dependency-graph + composition-tree
      → trace signal-chains
      → write_kb_file ×N → Markdown KB tree → S3 (repo prefix)
      → record_status (READY) → DynamoDB
  → frontend polls status until READY
```

---

## 8. Constraints & Non-Goals

- **Read-only** w.r.t. engineering artifacts; never writes back to ARXML.
- ARXML coverage limited to the demo subset (parent §2 Non-Goals).
- No production HA/scale; single environment.
- Extraction is deterministic — model orchestrates, tools compute.

---

## 9. Implementation (Python)

Python 3.12 + Strands Agents SDK. The agent is built once per worker invocation: a `BedrockModel`,
the §3 tools registered via `@tool`, and `skill.md` loaded verbatim as `system_prompt`. XML
extraction uses only the stdlib (`xml.etree.ElementTree` with `iterparse`, `tarfile`, `urllib`) —
the only heavyweight runtime dep is the Strands SDK (pulls `boto3`/`pydantic`).

### 9.1 Project Layout

> **Greenfield:** the folder currently holds only this `ARCHITECTURE.md`; the tree below is the
> target to create. `skill.md` is copied verbatim from
> `knowledge_base/output/sample_3_skill2/skill.md`.

```
components/ingestion-agent/         # self-contained build unit
├── ARCHITECTURE.md
├── pyproject.toml                 # package metadata + deps (src layout)
├── requirements.txt               # pinned runtime deps (Strands + boto3)
├── requirements-dev.txt           # test/lint tooling (pytest, ruff)
├── Dockerfile                     # Lambda container image (python:3.12 base)
├── src/
│   └── ingest_agent/
│       ├── __init__.py
│       ├── core.py                # run_ingest(...) + Config.from_env()
│       ├── handler.py             # AWS Lambda adapter (api | worker) → run_ingest
│       ├── __main__.py            # local CLI adapter → run_ingest
│       ├── agent.py               # build_agent(): BedrockModel + tools + skill prompt
│       ├── tools.py               # scan_repo / write_kb_file / record_status (@tool)
│       ├── arxml.py               # deterministic parse: iterparse, namespaces, AUTOSAR paths
│       ├── workspace.py           # working tree + finalize sink (S3 or local dir)
│       └── skill.md               # v2 skill, loaded as the system prompt
└── tests/
    ├── test_arxml.py
    ├── test_tools.py
    └── fixtures/                  # small ARXML snippets
```

> `skill.md` is the single source of truth for the agent's procedure. Keep it in sync with
> `knowledge_base/output/sample_3_skill2/skill.md` (copy at build time, or symlink in dev).

### 9.2 Dependencies

| Dependency | Scope | Why |
|---|---|---|
| `strands-agents>=1.0.0` | runtime | Agent loop, `@tool`, `BedrockModel`, structured output. |
| `boto3>=1.34` | runtime | S3, DynamoDB, Secrets Manager, self-invoke. |
| *(stdlib)* `xml.etree.ElementTree`, `tarfile`, `urllib` | runtime | ARXML parse, tarball fetch/extract, `repo_id` slug. |
| `pytest`, `ruff` | dev | Unit tests + lint. |

No `lxml`/`requests` for the demo scope; `lxml` (manylinux wheels) can be added later without
changing the packaging model.

### 9.3 Agent Construction (sketch)

```python
# agent.py
import os
from pathlib import Path
from strands import Agent
from strands.models import BedrockModel
from .tools import scan_repo, write_kb_file, record_status

SKILL = (Path(__file__).parent / "skill.md").read_text(encoding="utf-8")

def build_agent() -> Agent:
    model = BedrockModel(
        model_id=os.environ["BEDROCK_MODEL_ID"],
        region_name=os.environ.get("BEDROCK_REGION", os.environ["AWS_REGION"]),
        temperature=0.0,                   # deterministic orchestration
    )
    return Agent(
        model=model,
        system_prompt=SKILL,
        tools=[scan_repo, write_kb_file, record_status],
        callback_handler=None,             # no console streaming in Lambda
    )
```

Each `@tool` function's docstring/type hints become the schema the model sees. Tools compute and
return data; the model only sequences calls per the skill.

### 9.4 Working-Directory Model (S3 binding)

The agent works against a local tree under `/tmp`, then syncs to S3 — keeps the skill's filesystem
semantics and lets later steps re-read earlier `_index/` files in the same run:

1. `scan_repo` fetches the tarball to `/tmp/<repo_id>/src/`, extracts, parses every `.arxml`.
   (Raw-ARXML upload to `s3://$KB_BUCKET/<repo_id>/raw/` is optional — Analyze reads only the KB.)
2. `write_kb_file(rel_path, markdown)` writes into `/tmp/<repo_id>/kb/<rel_path>`.
3. On finalize, `/tmp/<repo_id>/kb/` is uploaded to `s3://$KB_BUCKET/<repo_id>/kb/` in one pass.
4. `/tmp` is cleared at the end of the invocation.

`repo_id` is a human-readable slug from the GitHub URL + branch (e.g. `patrikja__autosar__main`) —
visible in the S3 console and idempotent on re-ingest.

### 9.5 Shared Core & Entry Points

Every entry point is a thin adapter over one function, so behaviour is identical in Lambda or on a
laptop:

```python
# core.py
def run_ingest(github_url: str, branch: str,
               repo_id: str | None = None, cfg: "Config | None" = None) -> dict:
    cfg = cfg or Config.from_env()           # resolves storage mode: aws | local
    repo_id = repo_id or slug(github_url, branch)
    cfg.bind_run(repo_id)                     # per-run workdir + sink for the tools
    record_status(repo_id, "PENDING", {})
    try:
        build_agent()(f"Generate the knowledge base for repo {github_url}@{branch} "
                      f"(repo_id={repo_id}).")
        finalize(cfg, repo_id)                # sync working tree → S3, or copy → local out dir
        record_status(repo_id, "READY", {})
    except Exception as e:
        record_status(repo_id, "FAILED", {"error": str(e)})
        raise
    return {"repo_id": repo_id, "status": "READY"}
```

- **`handler.py`** (Lambda): `api` mode validates, writes `PENDING`, self-invokes; `worker` mode
  calls `run_ingest` (§10).
- **`__main__.py`** (local CLI): parses args, calls `run_ingest` directly (§12).
- `@tool` functions read a per-run context (workdir + sink) set by `run_ingest` via a
  `contextvars.ContextVar`, so the tools stay stateless.

`Config.from_env()` picks the **aws** sink when `KB_BUCKET`/`REPOS_TABLE` are set, else a **local**
sink.

---

## 10. Invocation & Async Model

`POST /ingest` runs longer than the **API Gateway 30 s** limit, and the full run must fit the
**Lambda 15 min** ceiling. The single Lambda has two modes, dispatched in `handler.py`:

| Mode | Trigger | Behavior |
|---|---|---|
| `api` (sync) | `POST /ingest` | Validate body, compute `repo_id`, write `PENDING`, **async self-invoke** (`InvocationType="Event"`) with a `worker` payload, return **`202 { repo_id }`**. |
| `api` (sync) | `GET /status?repo_id=…` | Read DynamoDB, return `{ status, meta }`. |
| `worker` (async) | Self-invoke (`Event`) | Build the agent, run §4 to completion, set `READY`/`FAILED`. |

```
POST /ingest ──► Ingest λ (api)  ──► DynamoDB: PENDING
                      │
                      └─ async self-invoke (Event) ──► Ingest λ (worker)
                                                          └─ Strands agent + skill (§4)
                                                          └─ DynamoDB: READY / FAILED
GET /status  ──► Ingest λ (api)  ──► DynamoDB read ──► { status }
```

Frontend polls `GET /status` until `READY`/`FAILED`. An SQS trigger (retries, DLQ) can replace the
self-invoke later; self-invoke keeps the prototype to one Lambda.

---

## 11. Packaging & Lambda Configuration (Terraform alignment)

The infra `compute` module (aws-infrastructure §6) provisions this Lambda.

### 11.1 Packaging — container image (recommended)

ECR image (`package_type = "Image"`) on the official Lambda base — sidesteps the 250 MB zip limit
and the manylinux-wheel build, and matches the Analyze Lambda.

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ingest_agent/ ${LAMBDA_TASK_ROOT}/ingest_agent/
CMD ["ingest_agent.handler.handler"]
```

> Zip alternative: `pip install -r requirements.txt -t build/`, add `src/`, zip; requires building
> pydantic-core against the Lambda runtime. Container image is preferred.

### 11.2 Lambda configuration

| Setting | Value | Rationale |
|---|---|---|
| Runtime | Container image, Python 3.12 base | §11.1 |
| Handler | `ingest_agent.handler.handler` | Single dispatcher (§10). |
| Memory | 2048 MB | XML parsing + orchestration headroom. |
| Timeout | 900 s | Single-pass run with headroom (§10). |
| Ephemeral storage (`/tmp`) | 4096 MB | Tarball + extracted ARXML + KB tree (§9.4). |
| Architecture | `x86_64` | Avoids cross-build friction; `arm64` later. |
| Reserved concurrency | low (1–2) | Bounds self-invoke fan-out. |

### 11.3 Environment variables (set by the `compute` module)

| Env var | Source (TF) | Purpose |
|---|---|---|
| `KB_BUCKET` | `storage` output | S3 bucket for raw ARXML + KB tree. |
| `REPOS_TABLE` | `storage` output | DynamoDB table for metadata/status. |
| `BEDROCK_MODEL_ID` | `compute` variable | Claude model id. |
| `BEDROCK_REGION` | `compute` variable / region | Bedrock invocation region. |
| `GITHUB_TOKEN_SECRET_ARN` | `compute` variable (optional) | Secrets Manager ARN; private repos only. |
| `WORKER_FUNCTION_NAME` | this function's own name | Target of the async self-invoke (§10). |
| `KB_WORKDIR` | default `/tmp` | Root of the local working tree (§9.4). |
| `LOG_LEVEL` | `compute` variable | Logging verbosity. |

### 11.4 IAM (refines aws-infrastructure §5 — Ingest Lambda role)

| Action | Resource | Used by |
|---|---|---|
| `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` | `KB_BUCKET` (+ `<repo_id>/*`) | `scan_repo`, `write_kb_file`, S3 sync (§9.4). |
| `dynamodb:PutItem`, `UpdateItem`, `GetItem` | `REPOS_TABLE` | `record_status`, `GET /status`. |
| `bedrock:InvokeModel` (+ `…WithResponseStream`) | the configured model | Strands `BedrockModel`. |
| `secretsmanager:GetSecretValue` | `GITHUB_TOKEN_SECRET_ARN` | `scan_repo` (private repos). |
| `lambda:InvokeFunction` | `WORKER_FUNCTION_NAME` (self) | Async self-invoke (§10). |
| `logs:CreateLogGroup/Stream`, `PutLogEvents` | function log group | CloudWatch. |

### 11.5 Deployment Contract (consumed by the `compute` module)

| Item | Value |
|---|---|
| Build context | `components/ingestion-agent/` |
| Dockerfile | `components/ingestion-agent/Dockerfile` |
| Image entry (`CMD`) | `ingest_agent.handler.handler` |
| Importable package | `ingest_agent` (src layout) |
| Function env vars | §11.3 |
| Function IAM | §11.4 |
| Async worker | the **same** function, self-invoked; `WORKER_FUNCTION_NAME` = its own name |

Terraform builds/pushes the image (ECR) and creates the Lambda with `package_type = "Image"`, the
§11.3 env vars, and the §11.4 role. The local CLI (§12) shares the package but is not part of the
deployed entry path.

---

## 12. Local Development & Run (no Lambda)

Plain Python — the whole pipeline runs on a laptop with local AWS credentials; the only
always-required AWS call is **Bedrock**. No Lambda, API Gateway, S3, or DynamoDB needed to develop.

```bash
cd components/ingestion-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export AWS_PROFILE=my-dev
export AWS_REGION=us-west-2
export BEDROCK_MODEL_ID=<claude-model-id>

# LOCAL mode — KB tree + status under ./out, no S3/DynamoDB
python -m ingest_agent \
  --github-url https://github.com/patrikja/autosar --branch master \
  --out ./out

# AWS mode — local process, writes to real S3 + DynamoDB
export KB_BUCKET=my-dev-bucket REPOS_TABLE=my-dev-repos
python -m ingest_agent --github-url https://github.com/patrikja/autosar --branch master
```

### Run / storage modes

Both modes share code up to `finalize()` (§9.5); only the sink differs:

| Mode | Selected by | KB tree | Status |
|------|-------------|---------|--------|
| **local** | `--out <dir>` (or no `KB_BUCKET`) | `<dir>/<repo_id>/kb/` | `<dir>/<repo_id>/status.json` |
| **aws** | `KB_BUCKET` + `REPOS_TABLE` set | `s3://$KB_BUCKET/<repo_id>/kb/` | DynamoDB item |

### Testing tiers

- **Offline unit** (`pytest`) — `arxml.py`, `scan_repo`, `write_kb_file` against `tests/fixtures/`
  and the demo submodule (`knowledge_base/input/autosar`). No AWS/Bedrock — stub the model.
- **Local end-to-end** — `python -m ingest_agent --out ./out` against the demo repo; diff against
  `knowledge_base/output/sample_3_skill2/` for the §5 invariants.
- **Q&A benchmark** — run `knowledge_base/validation/skill.md` over `./out` to confirm
  blast-radius/dependency questions are answerable index-first.
- **AWS integration** — set `KB_BUCKET`/`REPOS_TABLE` and re-run locally before any deploy.

`ruff` for lint.

---

## 13. Prototype Simplifications

Each is a one-line change to revert if the product grows:

| Simplification | Instead of | Why it's safe |
|---|---|---|
| **3 tools** | 6 fine-grained tools | Extraction is deterministic; one `scan_repo` removes file-by-file agent turns. |
| **Single-pass only** | Multi-pass batching (skill §0) | Demo ARXML is "small" by the skill's own rule; skill still selects the mode. |
| **Human-readable `repo_id` slug** | `sha256(url@branch)` | Debuggable, idempotent, no hashing code. |
| **Flat module layout** | `tools/` + `arxml/` subpackages | Fewer files; `Config.from_env()` lives in `core.py`. |
| **Skip raw-ARXML upload** (optional) | Always persist raw ARXML | Analyze reads only the KB. |
| **`x86_64`** | `arm64` | Avoids cross-build friction; arm64 is a later cost tweak. |
| **Async self-invoke** | SQS / Step Functions | No extra resources; smallest thing beating the API GW 30 s limit. |

Kept on purpose: container-image packaging and DynamoDB for status (already required system-wide).
