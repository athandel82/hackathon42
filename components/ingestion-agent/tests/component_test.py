"""Component test for the Ingestion Agent.

Drives the *real* component end-to-end against the live GitHub repo
``patrikja/autosar`` and records every API response to
``tests/artifacts/component_api_responses.json``.

Only the two genuinely-external dependencies are stubbed:

* **Bedrock / the LLM** — replaced by a deterministic ``FakeAgent`` that calls
  the real ``scan_repo`` tool (live tarball fetch + ARXML parse) and authors a
  representative KB with the real ``write_kb_file`` tool. The orchestration the
  LLM would normally do is scripted, but every byte of data is real.
* **AWS SDK (boto3)** — replaced by an in-memory DynamoDB table + S3 client so
  the ``AwsSink`` / ``GET /status`` code paths run unchanged without real AWS.

Everything else (handler dispatch, api/worker modes, RunContext/workspace,
tarball fetch, ARXML parser, finalize/upload, status transitions) is the actual
component code.

Run (no pytest needed)::

    python3 tests/component_test.py
"""

from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

# Make `import ingest_agent` work without installation (src layout).
COMPONENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(COMPONENT_ROOT / "src"))

GITHUB_URL = "https://github.com/patrikja/autosar"
BRANCH = "master"
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"


# --------------------------------------------------------------------------- #
# Fake boto3 (in-memory DynamoDB + S3) injected before any boto3 import.
# --------------------------------------------------------------------------- #

_DDB_STORE: dict[str, dict] = {}
_S3_UPLOADS: list[dict] = []


class _FakeTable:
    def __init__(self, store):
        self._store = store

    def put_item(self, Item):  # noqa: N803 (boto3 kwarg name)
        self._store[Item["repo_id"]] = Item

    def get_item(self, Key):  # noqa: N803
        item = self._store.get(Key["repo_id"])
        return {"Item": item} if item is not None else {}


class _FakeResource:
    def __init__(self, store):
        self._store = store

    def Table(self, _name):  # noqa: N802 (boto3 method name)
        return _FakeTable(self._store)


class _FakeS3:
    def __init__(self, uploads):
        self._uploads = uploads

    def upload_file(self, filename, bucket, key):
        self._uploads.append({"bucket": bucket, "key": key,
                              "bytes": Path(filename).stat().st_size})


class _FakeSession:
    def __init__(self, *_a, **_k):
        pass

    def client(self, name):
        if name == "s3":
            return _FakeS3(_S3_UPLOADS)
        raise ValueError(f"fake session: unexpected client {name!r}")

    def resource(self, name):
        if name == "dynamodb":
            return _FakeResource(_DDB_STORE)
        raise ValueError(f"fake session: unexpected resource {name!r}")


def _install_fake_boto3() -> None:
    boto3 = types.ModuleType("boto3")
    boto3.session = types.SimpleNamespace(Session=_FakeSession)
    boto3.resource = lambda name: _FakeResource(_DDB_STORE) if name == "dynamodb" \
        else (_ for _ in ()).throw(ValueError(name))
    boto3.client = lambda name, *a, **k: _FakeS3(_S3_UPLOADS) if name == "s3" \
        else (_ for _ in ()).throw(ValueError(f"fake boto3: unexpected client {name!r}"))
    sys.modules["boto3"] = boto3


# --------------------------------------------------------------------------- #
# Fake agent: real tools, scripted orchestration (no Bedrock).
# --------------------------------------------------------------------------- #


class FakeAgent:
    """Stands in for the Strands+Bedrock agent. Calls the real tool impls."""

    def __init__(self, github_url: str, branch: str):
        self.github_url = github_url
        self.branch = branch

    def __call__(self, _prompt: str):
        from ingest_agent.tools import (
            scan_repo_impl,
            write_kb_file_impl,
        )

        model = scan_repo_impl(self.github_url, self.branch)
        stats = model["stats"]

        # --- _index/stats.md ---
        write_kb_file_impl(
            "_index/stats.md",
            "# Stats\n\n"
            + "\n".join(f"- **{k}**: {v}" for k, v in stats.items())
            + "\n",
        )

        # --- _index/source-map.md (durable provenance table) ---
        rows = ["# Source Map\n", "| Path | Type | Source |", "|---|---|---|"]
        for r in model["source_map"]:
            rows.append(f"| `{r['path']}` | {r['type']} | {r['file']}:{r['line']} |")
        write_kb_file_impl("_index/source-map.md", "\n".join(rows) + "\n")

        # --- _index/path-index.md ---
        rows = ["# Path Index\n", "| AUTOSAR Path | Type | Source Ref |", "|---|---|---|"]
        for r in model["source_map"]:
            rows.append(f"| `{r['path']}` | {r['type']} | {r['file']}:{r['line']} |")
        write_kb_file_impl("_index/path-index.md", "\n".join(rows) + "\n")

        # --- _index/components.md + per-component detail ---
        comps = model["elements"]["components"]
        idx = ["# Components\n"]
        for c in comps:
            idx.append(f"- [{c['path']}](../components/{c['name']}.md)")
            ports = [ch for ch in c["children"] if ch["tag"].endswith("-PORT-PROTOTYPE")]
            body = [
                f"# {c['name']}\n",
                f"- **Type:** {c['tag']}",
                f"- **AUTOSAR Path:** `{c['path']}`",
                f"- **UUID:** {c['uuid']}",
                f"- **Source:** {c['file']}:{c['line']}",
                f"\n## Ports ({len(ports)})\n",
            ]
            for p in ports:
                refs = ", ".join(f"`{r['target']}`" for r in p["refs"]) or "—"
                body.append(f"- **{p['name']}** ({p['tag']}) → {refs}")
            write_kb_file_impl(f"components/{c['name']}.md", "\n".join(body) + "\n")
        write_kb_file_impl("_index/components.md", "\n".join(idx) + "\n")

        # --- README.md ---
        write_kb_file_impl(
            "README.md",
            f"# Knowledge Base — {self.github_url}@{self.branch}\n\n"
            f"{stats['components']} components, {stats['interfaces']} interfaces, "
            f"{stats['indexed_elements']} indexed elements across "
            f"{stats['source_files']} ARXML files.\n",
        )
        return types.SimpleNamespace(stop_reason="end_turn")


# --------------------------------------------------------------------------- #
# Test harness
# --------------------------------------------------------------------------- #


def _v2_event(method: str, path: str, body=None, query=None) -> dict:
    ev: dict = {"rawPath": path, "requestContext": {"http": {"method": method}}}
    if body is not None:
        ev["body"] = json.dumps(body)
    if query is not None:
        ev["queryStringParameters"] = query
    return ev


def main() -> int:
    _install_fake_boto3()

    import ingest_agent.agent as agent_mod
    from ingest_agent import handler

    # Stub Bedrock: build_agent() -> deterministic FakeAgent over real tools.
    agent_mod.build_agent = lambda: FakeAgent(GITHUB_URL, BRANCH)

    # Capture the async self-invoke instead of calling AWS Lambda.
    captured: list[dict] = []
    handler._self_invoke = lambda payload: captured.append(payload)

    recorded: list[dict] = []

    def record(name: str, description: str, event: dict, response: dict) -> None:
        recorded.append({
            "case": name,
            "description": description,
            "request": event,
            "response": response,
        })
        status = response.get("statusCode")
        print(f"[{name}] -> {status} {response.get('body', response)}")

    # 1) POST /ingest (valid) -> 202 PENDING, schedules worker.
    ev = _v2_event("POST", "/ingest", body={"github_url": GITHUB_URL, "branch": BRANCH})
    resp = handler.handler(ev)
    record("post_ingest_valid", "POST /ingest with a valid body", ev, resp)

    # 2) GET /status right after submit -> PENDING.
    repo_id = json.loads(resp["body"])["repo_id"]
    ev = _v2_event("GET", "/status", query={"repo_id": repo_id})
    resp = handler.handler(ev)
    record("get_status_pending", "GET /status immediately after submit", ev, resp)

    # 3) Run the worker (the captured async self-invoke payload).
    assert captured, "expected a self-invoke payload"
    worker_payload = captured[0]
    worker_result = handler.handler(worker_payload)
    recorded.append({
        "case": "worker_run",
        "description": "Async worker invocation (real ingest, stubbed LLM)",
        "request": worker_payload,
        "response": worker_result,
    })
    print(f"[worker_run] -> {worker_result}")

    # 4) GET /status after the worker completes -> READY (+ location).
    ev = _v2_event("GET", "/status", query={"repo_id": repo_id})
    resp = handler.handler(ev)
    record("get_status_ready", "GET /status after the worker finished", ev, resp)

    # 5) POST /ingest missing github_url -> 400.
    ev = _v2_event("POST", "/ingest", body={"branch": "master"})
    resp = handler.handler(ev)
    record("post_ingest_missing_url", "POST /ingest without github_url", ev, resp)

    # 6) GET /status unknown repo_id -> 404.
    ev = _v2_event("GET", "/status", query={"repo_id": "nope__nope__main"})
    resp = handler.handler(ev)
    record("get_status_unknown", "GET /status for an unknown repo_id", ev, resp)

    # 7) GET /status missing repo_id -> 400.
    ev = _v2_event("GET", "/status", query={})
    resp = handler.handler(ev)
    record("get_status_missing_param", "GET /status without repo_id", ev, resp)

    # 8) Unsupported method -> 405.
    ev = _v2_event("PUT", "/ingest")
    resp = handler.handler(ev)
    record("method_not_allowed", "PUT /ingest (unsupported method)", ev, resp)

    # Persist artifacts.
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": f"{GITHUB_URL}@{BRANCH}",
        "repo_id": repo_id,
        "note": "Bedrock LLM and AWS SDK stubbed; ARXML fetch+parse are real.",
        "status_table_final": _DDB_STORE,
        "kb_files_uploaded": sorted(u["key"] for u in _S3_UPLOADS),
        "api_cases": recorded,
    }
    art = ARTIFACTS / "component_api_responses.json"
    art.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nWrote {len(recorded)} API cases + {len(_S3_UPLOADS)} KB files "
          f"to {art.relative_to(COMPONENT_ROOT)}")

    # Minimal assertions so this doubles as a smoke test.
    final = _DDB_STORE[repo_id]
    assert final["status"] == "READY", final
    assert any(k.endswith("README.md") for k in out["kb_files_uploaded"])
    print("Component test PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
