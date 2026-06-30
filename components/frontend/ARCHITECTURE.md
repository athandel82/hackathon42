# Component Architecture — Frontend Web App

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.1
> **Unit type:** Client-side single-page application (SPA)
> **Runtime:** Static assets served over HTTP from an EC2 VM

---

## 1. Purpose

Browser-based UI for the SDV prototype. Provides two screens: onboarding (submit a
GitHub repository URL and watch ingestion status) and analysis (submit natural-language
change requests and render the impact report). The SPA holds no business logic; it is a
pure renderer of the result JSON returned by the Analyze Lambda.

---

## 2. Technology Stack

| Concern | Choice |
|---|---|
| Framework | React (function components + hooks) |
| Build tool | Vite (`vite build` → static assets) |
| Component library | Cloudscape Design System |
| Language | TypeScript |
| HTTP client | `fetch` (browser-native) |
| State | Local component state / React context (no external store) |
| Auth | None (open endpoints — prototype only) |

---

## 3. Deployment & Hosting

- **Build:** `vite build` emits static assets to `dist/`.
- **Serve:** a lightweight web server (nginx, or `vite preview`/static file server) runs on
  the **same EC2 VM** and serves `dist/` over HTTP.
- **Access:** reachable directly at the VM public DNS — `http://<ec2-public-dns>/`.
- **Provisioning:** the EC2 instance is created by the `frontend` Terraform module; user-data
  builds and starts the server on boot (see AWS Infrastructure component).

---

## 4. Configuration

| Item | Mechanism | Notes |
|---|---|---|
| `API_BASE_URL` | Build-time env var **or** runtime `config.json` | Points the SPA at the API Gateway HTTP API base URL. |

Wiring the SPA to the backend requires only this single value. No secrets are held client-side.

---

## 5. Screens & Responsibilities

### 5.1 Onboarding
- Input: GitHub repository URL.
- Action: `POST /ingest` to trigger ingestion.
- Behavior: poll ingestion status until `READY` (or `FAILED`); display progress.

### 5.2 Chat + Dashboard
- Input: natural-language change request.
- Action: `POST /analyze` with the change request and repo/session identifier.
- Render the result JSON as impact cards:
  - **What Breaks** — dependency tree/graph from `what_breaks.graph` and `what_breaks.impacted`.
  - **What it Costs** — savings-vs-rework range widget from `what_it_costs`.
  - **What it Risks** — severity-sorted list from `what_it_risks.items`.

---

## 6. External Interfaces (consumed)

The SPA calls the API Gateway HTTP API (see AWS Infrastructure component). CORS must allow
the VM public-DNS origin.

| Operation | Request | Response |
|---|---|---|
| Trigger ingestion | `POST /ingest` `{ "github_url": "<url>" }` | `{ "repo_id", "status" }` |
| Poll status | `GET /status?repo_id=<id>` | `{ "status": "PENDING\|READY\|FAILED" }` |
| Analyze change | `POST /analyze` `{ "repo_id", "change_request" }` | Result JSON envelope (parent §7) |

> Endpoint paths are the SPA's contract expectation; the authoritative route definitions
> live in the AWS Infrastructure component. Long-running `/analyze` may use response
> streaming or a request/response call behind a loading state.

---

## 7. Rendering Contract

The frontend treats the parent-document result JSON (parent §7) as read-only input:

- `what_breaks.graph` → dependency-tree visual (nodes/edges).
- `what_breaks.impacted[]` → per-element list with `severity`, `domain`, `hops`, `explanation`.
- `what_it_costs.bom_saved` / `eng_rework` → range bars; `net_assessment` → headline.
- `what_it_risks.items[]` → list sorted by `severity`, flagged on `revalidation_required`.
- `confidence.level` → confidence badge (`model_agreement` reserved for future ensemble).

Unknown fields are ignored; missing optional sections render as empty states.

---

## 8. Constraints & Non-Goals

- No authentication, sessions, or access control (prototype).
- No client-side persistence beyond in-memory state.
- No business logic or impact computation client-side — rendering only.
- Single environment (`dev`); not hardened for production traffic.
