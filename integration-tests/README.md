# Integration Tests — Ingestion ⇄ Analyze

End-to-end test proving the two agents **work together**: the Ingestion Agent
builds a Markdown KB from an AUTOSAR repo, and the Analyze Agent answers change
requests by reading *that exact KB*.

```bash
python3 integration-tests/run_integration.py
```

Outputs:
- [`recorded_responses.json`](recorded_responses.json) — all 12 API
  request/response pairs (`POST /ingest`, `GET /status`, and 10 × `POST /analyze`).
- [`quality_report.md`](quality_report.md) — a scored summary of the 10 reference
  questions (resolved target, impacted set, cost, top risk, verdict) plus
  per-question detail, compared against the validation bank's ground truth.
- A readable log printed to stdout.

## Reference questions

The 10 questions are change-request phrasings aligned to the canonical bank in
[`knowledge_base/validation/questions.md`](../knowledge_base/validation/questions.md)
(blast-radius, interface dependency, signal-flow, de-content). The harness scores
each answer's resolved target type and `what_breaks.impacted` against the bank's
ground truth and prints a `✅ match` / `⚠️ limitation` / `❌` verdict.

Latest run: **8 ✅ match, 1 ✅ correct-root (EDC), 1 ⚠️ limitation** (instance-level
de-content of the `DoorRight` prototype — see notes in the report).

## What is real vs. stubbed

The test exercises the **real** code of both components through their real Lambda
handlers and one shared local workspace:

| Layer | Real? | Notes |
|-------|-------|-------|
| Lambda handlers (`POST /ingest`, `GET /status`, `POST /analyze`) | ✅ | Driven with API-Gateway-shaped events. |
| `run_ingest` / `run_analyze` cores, `Config`, slug, cache | ✅ | LOCAL storage mode (no AWS). |
| ARXML parse (`scan_repo`) + KB write (`write_kb_file`) + finalize | ✅ | Real deterministic tools. |
| KB navigation (`resolve_path`, `blast_radius`, `trace_signals`, `kb_read`) | ✅ | Real read-only tools over the produced KB. |
| Result envelope (`ResultEnvelope` Pydantic schema) | ✅ | Real schema validation. |
| **Bedrock model** (token generation) | ⛔ stubbed | `reference_agents.py` does deterministic tool orchestration instead. |
| **GitHub tarball fetch** | ⛔ redirected | Uses the committed demo ARXML (`knowledge_base/input/autosar/ARXML`) — no network. |
| **DynamoDB for `GET /status`** | ⛔ local | Status is read from the local sink's `status.json` (the Lambda path uses DynamoDB). |

Only the LLM and external I/O are replaced; the cross-component contract (the KB
layout ingestion writes and analyze reads, and the result schema) is real.

To run a **fully live** end-to-end (real Bedrock + real GitHub), use the two
agents' own CLIs instead:

```bash
# 1. ingest -> ./out/<repo_id>/kb
python -m ingest_agent --github-url https://github.com/patrikja/autosar --branch master --out ./out
# 2. analyze that KB
python -m analyze_agent --kb-dir ./out --repo-id patrikja__autosar__master \
  --change-request "remove the rear-door module"
```

(Both require `BEDROCK_MODEL_ID` + AWS credentials with Bedrock access.)

## Scenarios covered

1. **`remove the rear-door module`** → resolves the `Door` component; blast radius
   = `DoorControl`, `EDC`, plus the four `CombinedStatus*` network PDUs (2 hops).
2. **`change the DoorStatus interface`** → resolves the `DoorStatus` interface;
   impact from interface usage = provider `Door` + requirer `DoorControl`.
3. **`remove the IoHwAb service component`** → resolves `IoHwAb`; blast radius =
   `DoorControl`, `EDC`.

Each asserts the API status codes (202 / 200), `READY` ingestion status, that the
KB files analyze depends on were produced, and that the blast radius matches the
known structure of the demo model.
