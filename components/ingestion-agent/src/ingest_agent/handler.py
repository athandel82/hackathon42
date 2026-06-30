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
from decimal import Decimal
from typing import Any

from .core import Config, run_ingest, slug
from .tools import read_status_impl, record_status_impl
from . import workspace


# CORS `*` (parent §4.2) so the SPA can call the API directly. API Gateway also
# sets these; emitting them here keeps responses correct on any adapter path.
_CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST,GET,OPTIONS",
}


def handler(event: dict, context: Any = None) -> dict:
    if event.get("mode") == "worker":
        return _worker(event)
    if _method(event) == "OPTIONS":
        return _resp(204, {})
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
    force = bool(body.get("force", False))
    repo_id = slug(github_url, branch)

    # Bind the per-run context so the status sink (DynamoDB in AWS mode) is
    # available for both the cache lookup and the PENDING write below.
    Config.from_env().bind_run(repo_id)

    # Idempotency / caching: a repo's KB lives at a deterministic prefix keyed by
    # repo_id (github_url + branch), so re-submitting the same repo need not
    # rebuild the index from scratch. Short-circuit unless the caller forces a
    # refresh or the previous attempt failed.
    if not force:
        existing = read_status_impl(repo_id)
        if existing is not None:
            status = existing.get("status")
            if status == "READY":
                # KB already built — return it as-is; the frontend's status poll
                # sees READY immediately and proceeds without a rebuild.
                return _resp(202, {"repo_id": repo_id, "status": "READY",
                                   "cached": True, "meta": existing.get("meta", {})})
            if status == "PENDING":
                # A build is already in flight — don't schedule a duplicate.
                return _resp(202, {"repo_id": repo_id, "status": "PENDING",
                                   "cached": True})
            # status == FAILED (or anything else) → fall through and re-ingest.

    # Mark PENDING immediately so the frontend can start polling.
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


def _json_default(o: Any) -> Any:
    """Fallback encoder for ``json.dumps``.

    DynamoDB returns all numbers as ``decimal.Decimal``, which the stdlib JSON
    encoder cannot serialize — that previously made ``GET /status`` 500 whenever
    a status ``meta`` carried a numeric value (e.g. element counts). Convert
    Decimals to int/float and stringify anything else unexpected so a response
    can never crash the handler.
    """
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    return str(o)


def _resp(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=_json_default),
    }
