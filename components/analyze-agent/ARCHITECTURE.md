# Component Architecture — Analyze Agent

> **Parent:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §4.4
> **Unit type:** In-process Strands agent inside the Analyze Lambda
> **Trigger:** Analysis request (`POST /analyze`) via API Gateway

---

## 1. Purpose

The agentic core. Answers a natural-language change request by navigating the Markdown KB
(parent §5) built by the Ingestion Agent (§4.3), using read-only KB navigation tools, then
emits the strict result JSON envelope (parent §7) for the frontend to render. Relationships
are precomputed at ingestion, so the agent **navigates** deterministic index files rather than
re-deriving any graph.

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
| `resolve_path` | `(autosar_path\|name) → file` | Look up `_index/path-index.md` to map an AUTOSAR reference / name to its concrete detail file. |
| `blast_radius` | `(component) → element[]` | Read `_index/dependency-graph.md` **reverse** adjacency → set of elements that break if the target changes. |
| `trace_signals` | `(element) → chain[]` | Read `_index/signal-chains.md` → network signals/PDUs the element feeds and where a cut severs the chain. |

All tools are read-only; the agent never mutates the KB.

---

## 4. Analysis Flow

1. **Resolve target** — map the NL request to concrete KB element(s) via `resolve_path`,
   using `_index/components.md` / `interfaces.md` for fuzzy name matches.
2. **Compute impact set** — read the **reverse-dependency** section of
   `_index/dependency-graph.md` plus relevant `_index/signal-chains.md` entries. These are
   precomputed and deterministic, so the impact set is exact (no graph re-derivation).
3. **Detail on demand** — open only the few `components/`, `interfaces/`, or `system/` detail
   files needed (Impact Tags, ports, severity hints) via `kb_read`.
4. **Synthesize** — one **Amazon Bedrock (Claude)** structured-output call turns the gathered
   impact set + details into the result JSON (`what_breaks` / `what_it_costs` / `what_it_risks`).

---

## 5. Output Contract — Result JSON

Returns the fixed envelope defined in parent §7. Top-level fields:

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
- Impact set correctness depends on the precomputed indices from the Ingestion Agent.
- No production HA/scale; single environment.
