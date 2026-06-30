"""AWS Lambda adapter — synchronous ``POST /analyze`` (§10).

Body: ``{ "repo_id": ..., "change_request": ... }``. Returns ``200`` + the
result envelope (or cached), ``400`` on a malformed body, and ``409`` when the
repo's KB is missing / not yet ``READY``.
"""

from __future__ import annotations

import json
from typing import Any

from .core import run_analyze

_CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def handler(event: dict, context: Any = None) -> dict:
    if _method(event) == "OPTIONS":
        return _resp(204, {})

    try:
        body = _body(event)
        repo_id = body["repo_id"]
        change_request = body["change_request"]
    except (KeyError, ValueError):
        return _resp(400, {"error": "repo_id and change_request are required"})

    try:
        envelope = run_analyze(repo_id, change_request)
    except FileNotFoundError:
        return _resp(409, {"error": f"KB for repo_id '{repo_id}' is not available "
                                    f"(missing or not READY)"})
    return _resp(200, envelope)


def _method(event: dict) -> str:
    http = event.get("requestContext", {}).get("http", {})
    return (http.get("method") or event.get("httpMethod") or "POST").upper()


def _body(event: dict) -> dict:
    raw = event.get("body")
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)


def _resp(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": _CORS, "body": json.dumps(body)}
