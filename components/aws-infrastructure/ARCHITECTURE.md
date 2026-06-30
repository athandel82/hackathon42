# Component Architecture — AWS Infrastructure

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.2, §4.5, §9
> **Unit type:** Cloud platform — API layer, storage/supporting services, and IaC
> **Cloud:** AWS-only · **IaC:** Terraform

---

## 1. Purpose

Defines the AWS runtime that hosts and connects all SDV components: the API entry point, the
two agent Lambdas (defined as compute but owned by the agent components), the storage and
supporting services, and the Terraform layout that provisions everything. Groups the parent
document's API Layer (§4.2) and Storage & Supporting Services (§4.5) with the Terraform
infrastructure (§9). All resources are first-class AWS-provider resources.

---

## 2. Service Inventory

| Service | Role |
|---|---|
| Amazon API Gateway (HTTP API) | Single open API for ingestion and analysis routes. |
| AWS Lambda × 2 | Ingest agent + Analyze agent (in-process Strands agents). |
| Amazon S3 | Raw ARXML and the generated Markdown KB tree (one prefix per repo). |
| Amazon DynamoDB | Repos, ingestion status, chat sessions, cached results. |
| AWS Secrets Manager | GitHub token (only if private repos are needed). |
| Amazon Bedrock | Claude model invocation (single model). |
| Amazon EC2 | VM that serves the React frontend (and nothing else). |
| Amazon CloudWatch | Logs and traces for both Lambdas. |

---

## 3. API Layer (§4.2)

- **Amazon API Gateway (HTTP API)** — one API for both ingestion and chat.
- **No authorizer** — all routes are open (prototype only).
- **CORS** enabled for the VM public-DNS origin so the SPA can call the API directly.
- Long-running analysis uses a **Lambda Function URL with response streaming**, or
  request/response with a frontend loading state — no WebSocket connection management.

### Routes (logical)

| Route | Target | Purpose |
|---|---|---|
| `POST /ingest` | Ingest Lambda | Start ingestion of a GitHub repo. |
| `GET /status` | Ingest Lambda / DynamoDB | Report ingestion status (`PENDING`/`READY`/`FAILED`). |
| `POST /analyze` | Analyze Lambda | Run impact analysis for a change request. |

> Route names are the integration contract shared with the Frontend component; exact paths
> are finalized in the `api` Terraform module.

---

## 4. Storage & Supporting Services (§4.5)

### 4.1 Amazon S3
- One **prefix per repo**: raw ARXML plus the Markdown KB tree (layout in parent §5).
- Written by the Ingestion Agent (`write_kb_file`); read-only for the Analyze Agent.

### 4.2 Amazon DynamoDB
- Repos and ingestion status (drives frontend polling).
- Chat sessions / history and cached analysis results.

### 4.3 AWS Secrets Manager
- Stores a GitHub token; consumed by `download_repo` only for private repositories.

### 4.4 Amazon Bedrock
- Claude invocation: skill-step orchestration (ingest) and one structured-output call (analyze).

### 4.5 Amazon EC2
- Single VM serving the static React frontend over HTTP at its public DNS; no other workload.

---

## 5. IAM & Access (least privilege, prototype scope)

| Principal | Grants |
|---|---|
| Ingest Lambda role | S3 read/write (repo prefix), DynamoDB write, Bedrock invoke, Secrets read, CloudWatch logs. |
| Analyze Lambda role | S3 read (repo prefix), DynamoDB read/write, Bedrock invoke, CloudWatch logs. |
| EC2 instance role | Minimal — static serving only (no AWS API calls required by default). |

---

## 6. Terraform Layout (§9)

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

### Module responsibilities

| Module | Provisions | Consumed by |
|---|---|---|
| `frontend` | EC2 instance, security group, user-data bootstrap | Frontend component |
| `api` | HTTP API, routes, CORS | Frontend → Lambdas |
| `compute` | Ingest & Analyze Lambdas, IAM roles, Bedrock permissions | Ingestion & Analyze agents |
| `storage` | S3 buckets, DynamoDB tables | Both agents |

State backend: S3 with a DynamoDB lock table. Single `dev` environment.

---

## 7. Constraints & Non-Goals

- **Open endpoints, no auth** — prototype only; not safe for untrusted exposure.
- No production-grade HA, multi-region, or autoscaling.
- Cost optimization is not a goal (quality and demo reliability prioritized).
- All resources are first-class AWS-provider resources (no exotic/3rd-party providers).
