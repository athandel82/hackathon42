"""AWS Lambda adapter — a single dispatcher with two modes (§10).

* ``api`` (sync, behind API Gateway):
    - ``POST /ingest``  → validate, compute ``repo_id``, write ``PENDING``,
      async self-invoke a ``worker`` run, return ``202 {repo_id}``.
    - ``GET  /status``  → read DynamoDB, return ``{status, meta}``.
* ``worker`` (async, self-invoked): run the full ingest to completion.

The mode is ``worker`` when the event carries ``{"mode": "worker"}`` (the
self-invoke payload); otherwise the event is treated as an API Gateway proxy
request.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .core import Config, run_ingest, slug
from .tools import record_status_impl
from . import workspace


def handler(event: dict, context: Any = None) -> dict:
    if event.get("mode") == "worker":
        return _worker(event)
    return _api(event)


# --------------------------------------------------------------------------- #
# worker mode
# --------------------------------------------------------------------------- #


def _worker(event: dict) -> dict:
    return run_ingest(
        github_url=event["github_url"],
        branch=event.get("branch", "master"),
        repo_id=event.get("repo_id"),
    )


# --------------------------------------------------------------------------- #
# api mode
# --------------------------------------------------------------------------- #


def _api(event: dict) -> dict:
    method = _method(event)
    path = event.get("rawPath") or event.get("path") or ""

    if method == "GET" or "status" in path:
        return _get_status(event)
    if method == "POST":
        return _post_ingest(event)
    return _resp(405, {"error": f"method not allowed: {method}"})


def _post_ingest(event: dict) -> dict:
    try:
        body = _body(event)
        github_url = body["github_url"]
    except (KeyError, ValueError):
        return _resp(400, {"error": "github_url is required"})
    branch = body.get("branch", "master")
    repo_id = slug(github_url, branch)

    # Mark PENDING immediately so the frontend can start polling.
    Config.from_env().bind_run(repo_id)
    record_status_impl(repo_id, "PENDING", {"github_url": github_url, "branch": branch})

    _self_invoke({"mode": "worker", "github_url": github_url,
                  "branch": branch, "repo_id": repo_id})
    return _resp(202, {"repo_id": repo_id, "status": "PENDING"})


def _get_status(event: dict) -> dict:
    params = event.get("queryStringParameters") or {}
    repo_id = params.get("repo_id")
    if not repo_id:
        return _resp(400, {"error": "repo_id is required"})

    import boto3

    table = boto3.resource("dynamodb").Table(os.environ["REPOS_TABLE"])
    item = table.get_item(Key={"repo_id": repo_id}).get("Item")
    if not item:
        return _resp(404, {"error": f"unknown repo_id: {repo_id}"})
    return _resp(200, {"repo_id": repo_id, "status": item.get("status"),
                       "meta": item.get("meta", {})})


def _self_invoke(payload: dict) -> None:
    import boto3

    boto3.client("lambda").invoke(
        FunctionName=os.environ["WORKER_FUNCTION_NAME"],
        InvocationType="Event",
        Payload=json.dumps(payload).encode("utf-8"),
    )


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _method(event: dict) -> str:
    ctx = event.get("requestContext", {})
    http = ctx.get("http", {})
    return (http.get("method") or event.get("httpMethod") or "POST").upper()


def _body(event: dict) -> dict:
    raw = event.get("body")
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def _resp(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
