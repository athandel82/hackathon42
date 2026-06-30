# Ingestion Agent

In-process [Strands](https://github.com/strands-agents) agent that turns a
vehicle's AUTOSAR ARXML ECU extract (fetched from a GitHub repo) into an
indexed, relationship-aware, **source-linked** Markdown knowledge base (KB).

Extraction is deterministic — the LLM only sequences tool calls per the
procedure in [`src/ingest_agent/skill.md`](src/ingest_agent/skill.md) (the v3
"Source-Linked & Self-Validating" skill, adapted from
`knowledge_base/output/sample_4_skill`). See
[`ARCHITECTURE.md`](ARCHITECTURE.md) for the full design.

## Layout

```
src/ingest_agent/
├── skill.md      # v3 skill, loaded verbatim as the system prompt
├── arxml.py      # deterministic ARXML parse (stdlib only): paths, UUIDs, lines
├── workspace.py  # working tree + finalize sink (local dir or S3/DynamoDB) + tarball fetch
├── tools.py      # scan_repo / write_kb_file / record_status (@tool)
├── agent.py      # build_agent(): BedrockModel + tools + skill prompt
├── core.py       # run_ingest(...) + Config.from_env() + repo_id slug
├── handler.py    # AWS Lambda adapter (api | worker)
└── __main__.py   # local CLI adapter
```

## Three tools (deterministic)

| Tool | Responsibility |
|------|----------------|
| `scan_repo(github_url, branch)` | Fetch the GitHub tarball (no clone), extract, parse every `.arxml`, return classified, source-linked elements + a sorted `source_map`. |
| `write_kb_file(rel_path, markdown)` | Write one Markdown file into the KB working tree (synced on finalize). |
| `record_status(repo_id, status, meta)` | Update ingestion status (`PENDING` → `READY`/`FAILED`). |

## Local development

```bash
cd components/ingestion-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

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

The only always-required AWS call is **Bedrock**. Storage defaults to a local
`./out` directory; setting `KB_BUCKET` + `REPOS_TABLE` (and omitting `--out`)
selects AWS mode.

## Tests

```bash
pip install -r requirements-dev.txt   # or: pip install -e ".[dev]"
pytest                                # offline: parser + tools + workspace
```

Offline unit tests stub out Strands/Bedrock entirely. The parser is
cross-checked against the demo ARXML submodule
(`knowledge_base/input/autosar/ARXML`) and the reference line numbers in
`knowledge_base/output/sample_4_skill/_index/source-map.md`.

## Packaging (Lambda)

Container image on the official Python 3.12 Lambda base:

```bash
docker build -t ingest-agent .
```

Entry point (`CMD`): `ingest_agent.handler.handler` — a single dispatcher for
`api` (`POST /ingest`, `GET /status`) and `worker` (async self-invoke) modes.
