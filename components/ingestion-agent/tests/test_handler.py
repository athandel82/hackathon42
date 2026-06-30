"""Unit tests for the Lambda handler response serialization.

Regression coverage for the ``GET /status`` 500 caused by DynamoDB returning
numbers as ``decimal.Decimal`` (not JSON-serializable by the stdlib encoder).
"""

from __future__ import annotations

import json
from decimal import Decimal

from ingest_agent.handler import _json_default, _resp


def test_resp_serializes_decimal_meta():
    # Mirrors a status item whose meta carries numeric values (e.g. counts).
    body = {
        "repo_id": "acme__widgets__main",
        "status": "READY",
        "meta": {"components": Decimal("4"), "coverage": Decimal("0.95")},
    }
    resp = _resp(200, body)
    assert resp["statusCode"] == 200
    parsed = json.loads(resp["body"])  # must not raise
    assert parsed["meta"]["components"] == 4
    assert parsed["meta"]["coverage"] == 0.95


def test_json_default_decimal_int_vs_float():
    assert _json_default(Decimal("7")) == 7
    assert isinstance(_json_default(Decimal("7")), int)
    assert _json_default(Decimal("1.5")) == 1.5
    assert isinstance(_json_default(Decimal("1.5")), float)


def test_json_default_unknown_type_stringified():
    class Weird:
        def __str__(self) -> str:
            return "weird"

    assert _json_default(Weird()) == "weird"
