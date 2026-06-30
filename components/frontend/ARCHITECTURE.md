# Component Architecture — Frontend Web App

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.1
> **Unit type:** Client-side single-page application (SPA)
> **Runtime:** Static assets served over HTTP from an EC2 VM

---

## 1. Purpose

Browser UI for the SDV prototype. Two screens: onboarding (submit GitHub repo URL, watch
ingestion status) and analysis (submit NL change requests, render impact report). No business
logic — pure renderer of the result JSON from the Analyze Lambda.

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

- **Build:** `vite build` → static assets in `dist/`.
- **Serve:** lightweight web server (nginx, or `vite preview`/static file server) on the
  **same EC2 VM**, serving `dist/` over HTTP.
- **Access:** `http://<ec2-public-dns>/`.
- **Provisioning:** EC2 instance created by the `frontend` Terraform module; user-data builds
  and starts the server on boot (see AWS Infrastructure component).

---

## 4. Configuration

Read at **runtime** from `public/config.json`, fetched once at startup before first render.
Runtime config (not build-time env vars) lets the **same build** target a stub, dev API, or
deployed API by editing one file — no rebuild.

```json
{
  "apiBaseUrl": "http://<ec2-public-dns>",
  "useStub": false
}
```

| Item | Mechanism | Notes |
|---|---|---|
| `apiBaseUrl` | `config.json` (runtime) | API Gateway HTTP API base URL. Ignored when `useStub` is `true`. |
| `useStub` | `config.json` (runtime) | When `true`, backend calls served by in-browser mock (§8). Defaults to `false`. |

**No secrets or AWS credentials client-side** — pure HTTP client, never calls the AWS SDK.
Credentials are only relevant to the backend the SPA points at.

> Build-time `VITE_API_BASE_URL` may override `config.json` during local dev, but
> `config.json` remains the source of truth for deployed builds.

---

## 5. Screens & Responsibilities

### 5.1 Onboarding
- Input: GitHub repo URL.
- Action: `POST /ingest`; keep returned `repo_id` in memory.
- Behavior: poll `GET /status?repo_id=<id>` every ~2s until `READY` or `FAILED`.
- States:
  - `PENDING` → spinner / progress text.
  - `READY` → enable Chat + Dashboard screen.
  - `FAILED` → inline error alert with retry.
  - Network/HTTP error → error alert with retry; no crash.

### 5.2 Chat + Dashboard
- Input: NL change request.
- Action: `POST /analyze` with `{ repo_id, change_request, session_id? }`. `repo_id` from
  onboarding; `session_id` optional (Analyze Agent keys sessions/history in DynamoDB), may be
  omitted for the prototype (the Analyze handler currently reads only `{ repo_id, change_request }`,
  analyze-agent §9.6).
- States: loading → render result; error → alert with retry.
  - `409` (repo missing / not `READY`, analyze-agent §9.6) → prompt to (re)run onboarding first.
- Render result JSON as impact cards:
  - **What Breaks** — dependency tree/graph from `what_breaks.graph` and `what_breaks.impacted`.
  - **What it Costs** — savings-vs-rework range widget from `what_it_costs`.
  - **What it Risks** — severity-sorted list from `what_it_risks.items`.
- Missing optional sections → empty states (§7); unknown fields ignored.

---

## 6. External Interfaces (consumed)

SPA calls the API Gateway HTTP API (see AWS Infrastructure component). CORS must allow the VM
public-DNS origin.

| Operation | Request | Response |
|---|---|---|
| Trigger ingestion | `POST /ingest` `{ "github_url": "<url>" }` | `202 { "repo_id" }` (status tracked via `/status`, ingestion-agent §10) |
| Poll status | `GET /status?repo_id=<id>` | `{ "status": "PENDING\|READY\|FAILED" }` |
| Analyze change | `POST /analyze` `{ "repo_id", "change_request", "session_id"? }` | `200` Result JSON envelope (parent §7); `409` if repo missing / not `READY` (analyze-agent §9.6) |

> Authoritative route definitions live in the AWS Infrastructure component. `POST /ingest` returns
> `202` immediately and the SPA polls `GET /status` until `READY`/`FAILED` (ingestion-agent §10).
> Long-running `/analyze` may use response streaming or request/response behind a loading state.

---

## 7. Rendering Contract

Parent-document result JSON (parent §7; schema = analyze-agent §9.4 `ResultEnvelope`) is read-only
input. All six top-level fields are present: `change_request`, `target_nodes`, `what_breaks`,
`what_it_costs`, `what_it_risks`, `confidence`.

- `change_request` → echoed as the report heading.
- `target_nodes[]` → resolved target chip(s) (`id`, `label`, `type`).
- `what_breaks.graph` → dependency-tree visual (nodes/edges).
- `what_breaks.impacted[]` → per-element list with `severity`, `domain`, `hops`, `via`, `explanation`.
- `what_it_costs.bom_saved` / `eng_rework` → range bars; `net_assessment` → headline; `line_items[]` → breakdown.
- `what_it_risks.items[]` → list sorted by `severity`, flagged on `revalidation_required`.
- `confidence.level` → confidence badge (`model_agreement` reserved for future ensemble).

Unknown fields ignored; missing optional sections → empty states.

---

## 8. Local Development & Testing

Fully developable and testable **without the backend or AWS credentials**. Two modes, driven
by `config.json` (§4):

### 8.1 Stub mode (default for local dev) — `useStub: true`
- `vite dev` serves with HMR at `http://localhost:5173`.
- `/ingest`, `/status`, `/analyze` intercepted **in-browser** from canned fixtures — no
  network, no API Gateway, no AWS.
- Tooling: **MSW (Mock Service Worker)** or a simple `fetch` shim. One handler file plus fixtures.
- Fixtures in `src/mocks/fixtures/`, mirroring the backend contracts verbatim:
  - `ingest.json` → `202 { "repo_id": "demo" }` (ingestion-agent §10; status comes from `/status`).
  - `status.json` → cycles `PENDING` → `READY`; `status-failed.json` → `{ "status": "FAILED" }` for the error path.
  - `analyze.json` → full `ResultEnvelope` (analyze-agent §9.4) with **all six** top-level fields:
    `change_request`, `target_nodes[]`, `what_breaks` (`summary`/`impacted[]`/`graph`),
    `what_it_costs` (`bom_saved`/`eng_rework`/`net_assessment`/`line_items[]`),
    `what_it_risks.items[]`, `confidence` (`level`, optional `model_agreement`). Use the documented
    sample case ("remove Door" → `DoorControl` + `EDC` + the 4 `CombinedStatus*` chains,
    analyze-agent §12) so the stub matches the backend's end-to-end expectation.
  - `analyze-409.json` → `409` body for the missing/not-`READY` repo path (§5.2).

### 8.2 Live mode — `useStub: false`
- Point `apiBaseUrl` at a deployed (or locally proxied) dev API.
- No AWS credentials in the SPA; creds (standard local AWS credential chain) only needed by
  backend components run locally.
- Use Vite's dev proxy to keep browser calls same-origin (avoids dev CORS); deployed builds
  rely on API Gateway CORS for the VM origin (§6).

### 8.3 Tests
- **Unit/render:** Vitest + React Testing Library — feed each `src/mocks/fixtures/*.json` into
  card components; assert they render and missing optional sections become empty states (§7).
- Reuse MSW handlers to cover the onboarding poll loop (`status.json` → `status-failed.json`) and
  the error paths (`analyze-409.json`, network/HTTP failures).

---

## 9. Source Layout (prototype)

```
components/frontend/
├── ARCHITECTURE.md
├── index.html
├── package.json
├── vite.config.ts            # dev server + proxy (live mode)
├── public/
│   └── config.json           # runtime config: apiBaseUrl, useStub
└── src/
    ├── main.tsx              # loads config.json, then mounts the app
    ├── api/                  # thin client: ingest/status/analyze (honors useStub)
    ├── screens/              # Onboarding, ChatDashboard
    ├── cards/                # WhatBreaks, WhatItCosts, WhatItRisks
    └── mocks/                # MSW handlers + fixtures/ (parent §7 envelope)
```

---

## 10. Constraints & Non-Goals

- No authentication, sessions, or access control (prototype).
- No client-side persistence beyond in-memory state.
- No business logic or impact computation client-side — rendering only.
- No AWS SDK or AWS credentials in the browser — pure HTTP client.
- Single environment (`dev`); not hardened for production traffic.
