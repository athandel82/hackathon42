# Component Architecture — AWS Infrastructure

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.2, §4.5, §9
> **Unit type:** Cloud platform — API, storage/supporting services, IaC
> **Cloud:** AWS-only · **IaC:** Terraform

---

## 1. Purpose

AWS runtime hosting all SDV components: API entry point, two agent Lambdas (compute owned here,
behavior owned by the agent components), storage/supporting services, and the Terraform layout.
Both Lambdas are container images built by their own components
([ingestion-agent §11](../ingestion-agent/ARCHITECTURE.md), [analyze-agent §11](../analyze-agent/ARCHITECTURE.md));
this component provisions registry, functions, IAM, env vars, and wiring per their §11.5 contracts.

---

## 2. Service Inventory

| Service | Role |
|---|---|
| API Gateway (HTTP API) | Single open API for ingest + analyze routes. |
| ECR × 2 | Image registry for Ingest/Analyze Lambdas (`package_type = "Image"`). |
| Lambda × 2 | Ingest + Analyze (in-process Strands agents). |
| S3 | KB tree `<repo_id>/kb/` per repo; raw ARXML optional. |
| DynamoDB | `repos` (status) + `results` (sessions/cache); + TF state-lock table. |
| Secrets Manager | GitHub token (private repos only). |
| Bedrock | Claude (single model). |
| EC2 | VM serving the React frontend; nothing else. |
| CloudWatch | Logs/traces for both Lambdas. |

---

## 3. API Layer (§4.2)

- HTTP API, **Lambda proxy integrations**, **no authorizer** (open — prototype).
- **CORS `*`** (§7 S1) — avoids the EC2↔API circular dependency.

| Route | Target | Behavior |
|---|---|---|
| `POST /ingest` | Ingest λ (`api`) | Validate, write `PENDING`, async self-invoke worker → `202 { repo_id }`. |
| `GET /status` | Ingest λ (`api`) | Read `repos` → `{ status }` (`PENDING`/`READY`/`FAILED`). |
| `POST /analyze` | Analyze λ | Sync impact analysis → `200 {envelope}`; `409` if repo missing/not `READY`. |

- Ingest async (self-invoke `Event`) beats the API GW 30 s limit; frontend polls `/status` (ingestion-agent §10).
- Analyze sync — fits 30 s (analyze-agent §10). **Fallback:** Function URL + response streaming if it nears 30 s.

---

## 4. Storage & Supporting Services (§4.5)

- **S3** — KB tree under `<repo_id>/kb/`; raw ARXML under `<repo_id>/raw/` optional. Written by Ingest; **read-only** for Analyze.
- **DynamoDB** — `repos` (`REPOS_TABLE`, written by Ingest, read by `/status`); `results` (`RESULTS_TABLE`, sessions + cache, Analyze read/write). TF state-lock table is infra-only.
- **Secrets Manager** — GitHub token, read by `scan_repo` for private repos only.
- **Bedrock** — Claude via shared `BEDROCK_MODEL_ID`/`BEDROCK_REGION`.
- **EC2** — user-data: `vite build`, write `config.json` (`apiBaseUrl` = `api` URL output, `useStub:false`), serve `dist/`.

---

## 5. IAM (least privilege, prototype scope)

| Principal | Grants |
|---|---|
| Ingest λ | S3 RW (`<repo_id>/*`), `repos` RW, Bedrock invoke (+stream), Secrets read, `lambda:InvokeFunction` (self, a), CW logs. |
| Analyze λ | S3 **read-only** (`<repo_id>/kb/*` + ListBucket), `results` RW, `repos` read (b), Bedrock invoke (+stream), CW logs. |
| EC2 | Minimal — static serving only. |

- **(a)** Async self-invoke (§3); scoped to own ARN; pairs with `WORKER_FUNCTION_NAME`.
- **(b)** `GetItem` on `repos` for the `409` readiness check (analyze-agent §9.6); drop if check skipped (gap G7).

---

## 6. Terraform Layout (§9)

```
infra/
├── main.tf            # provider, backend (S3 + DynamoDB lock), module wiring
├── variables.tf
├── outputs.tf
├── modules/
│   ├── frontend/      # EC2 + SG; user-data builds SPA, writes config.json, serves dist/
│   ├── api/           # HTTP API + routes + CORS(*) + proxy integrations
│   ├── compute/       # ECR + image build/push + both Lambdas + IAM + env vars
│   └── storage/       # S3 bucket + DynamoDB tables (repos, results)
└── envs/
    └── dev/
```

| Module | Provisions | Consumes |
|---|---|---|
| `storage` | S3 bucket, `repos`+`results` tables | — |
| `compute` | ECR, image build/push, Lambdas, IAM, env vars (§7) | `storage` outputs; component build contexts |
| `api` | HTTP API, routes, CORS(*), proxy integrations | `compute` ARNs (outputs invoke URL) |
| `frontend` | EC2, SG, user-data | `api` URL |

**Order (acyclic):** `storage → compute → api → frontend`. `api` does not depend on `frontend`
(CORS `*`), breaking the cycle. State backend: S3 + DynamoDB lock. Single `dev`.

---

## 7. compute Module — Deploy & Env Vars

Realizes ingestion-agent §11.5 / analyze-agent §11.5.

| Item | Ingest | Analyze |
|---|---|---|
| Build context | `components/ingestion-agent/` | `components/analyze-agent/` |
| Image entry | `ingest_agent.handler.handler` | `analyze_agent.handler.handler` |
| Memory / Timeout | 2048 MB / 900 s | 1024 MB / 60 s |
| Architecture | `x86_64` | `x86_64` |
| Reserved concurrency | 1–2 | 2–5 |

| Env var | Ingest | Analyze | Source |
|---|:--:|:--:|---|
| `KB_BUCKET` | ✓ | ✓ | `storage` |
| `REPOS_TABLE` | ✓ | read (G7) | `storage` |
| `RESULTS_TABLE` | — | ✓ | `storage` |
| `BEDROCK_MODEL_ID`/`BEDROCK_REGION` | ✓ | ✓ | `compute` var |
| `GITHUB_TOKEN_SECRET_ARN` | ✓ (opt) | — | `compute` var |
| `WORKER_FUNCTION_NAME` | ✓ (self) | — | own name |
| `KB_WORKDIR`/`KB_CACHE_DIR` | `/tmp` | `/tmp` | default |
| `LOG_LEVEL` | ✓ | ✓ | `compute` var |

Image build/push: TF docker provider, a `docker build/push` provisioner, or a referenced script.

---

## 8. Gaps Identified & Resolved

| # | Gap | Resolution |
|---|---|---|
| G1 | No image registry. | §2/§6/§7 — ECR ×2; `compute` builds/pushes per component `Dockerfile`. |
| G2 | Ingest self-invoke not provisioned. | §3/§5(a)/§7 — `InvokeFunction` (self) + `WORKER_FUNCTION_NAME`; `/ingest` → `202`. |
| G3 | Env-var wiring undocumented. | §7 — per-Lambda env table. |
| G4 | DynamoDB ambiguous. | §4 — `repos` + `results` + TF lock table. |
| G5 | Frontend config + CORS cycle. | §3/§4/§6 — CORS `*`; user-data writes `config.json` from `api` URL. |
| G6 | Stale `download_repo`. | §4 — corrected to `scan_repo`. |
| G7 | Analyze `409` vs IAM. | §5(b) — Analyze reads `repos`, or drop the check (accepted). |

---

## 9. Constraints, Non-Goals & Simplifications

- Open endpoints, no auth; no HA/multi-region/autoscaling; cost not optimized; AWS-provider resources only.

| # | Simplification | Instead of | Safe because |
|---|---|---|---|
| S1 | CORS `*` | Pin EC2 DNS origin | Removes EC2↔API cycle; endpoints already open. |
| S2 | Async self-invoke | SQS / Step Functions | Smallest thing beating API GW 30 s; one Lambda. |
| S3 | Sync `/analyze` | Streaming by default | Fits 30 s; streaming kept as fallback (§3). |
| S4 | Single `results` table | Separate cache/session tables | One key scheme covers both. |
| S5 | Skip raw-ARXML upload | Always persist raw | Analyze reads only the KB. |
| S6 | Single `dev` env | Multi-env | Enough to demo. |
| S7 | `x86_64` | `arm64` | Avoids cross-build friction. |

Kept on purpose: container images, two DynamoDB app tables, read-only S3 for Analyze (hard safety property).
