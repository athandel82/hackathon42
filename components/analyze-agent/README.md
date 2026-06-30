# Analyze Agent

In-process [Strands](https://github.com/strands-agents) agent that answers a
natural-language **change request** against the Markdown knowledge base built by
the [Ingestion Agent](../ingestion-agent). It navigates the precomputed indices
with four read-only tools and emits one validated **result envelope**
(`what_breaks` / `what_it_costs` / `what_it_risks`) via a single Bedrock
`structured_output` call.

Relationships are precomputed at ingestion — the agent **never re-derives the
graph**, it only reads it. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the
full design.

## Layout

```
src/analyze_agent/
├── analyze_prompt.md  # analysis system prompt, loaded verbatim
├── models.py          # Pydantic ResultEnvelope (parent §7) — structured-output schema
├── kb.py              # KB source (S3 | local) + tiny Markdown table/section parsers
├── tools.py           # resolve_path / blast_radius / trace_signals / kb_read (@tool)
├── cache.py           # result cache + session store (DynamoDB | local file)
├── agent.py           # build_agent(): BedrockModel + tools + prompt
├── core.py            # run_analyze(...) + Config.from_env()
├── handler.py         # AWS Lambda adapter (POST /analyze)
└── __main__.py        # local CLI adapter
```

## Read-only tools

| Tool | Reads | Returns |
|------|-------|---------|
| `resolve_path(ref)` | `_index/path-index.md` | detail-file path + type (fuzzy name match) |
| `blast_radius(component)` | reverse-deps of `_index/dependency-graph.md` | elements that break |
| `trace_signals(element)` | `_index/signal-chains.md` | chains the element feeds + cut points |
| `kb_read(path)` | any KB Markdown file | raw Markdown |

## Local development

```bash
cd components/analyze-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export AWS_REGION=us-west-2
export BEDROCK_MODEL_ID=<claude-model-id>

# LOCAL mode — read the KB the Ingestion Agent wrote under ./out
python -m analyze_agent \
  --kb-dir ../ingestion-agent/out \
  --repo-id patrikja__autosar__master \
  --change-request "remove the rear-door module"

# AWS mode — reads real S3, caches to DynamoDB
export KB_BUCKET=my-dev-bucket RESULTS_TABLE=my-dev-results
python -m analyze_agent --repo-id patrikja__autosar__master \
  --change-request "remove the rear-door module"
```

For zero-cost iteration without ingesting first, point `--kb-dir` at a directory
laid out as `<repo_id>/kb/...` (see `tests/fixtures/`).

## Tests

```bash
pip install -r requirements-dev.txt   # or: pip install -e ".[dev]"
pytest                                # offline: tools (fixture KB) + envelope schema
```

Offline tests stub out Strands/Bedrock entirely and run the deterministic tools
against a fixture KB tree (subset of `knowledge_base/output/sample_4_skill`).

## Packaging (Lambda)

```bash
docker build -t analyze-agent .
```

Entry point (`CMD`): `analyze_agent.handler.handler` — synchronous `POST /analyze`
returning the result envelope (`200`), `400` on a malformed body, `409` when the
repo's KB is missing or not `READY`.
