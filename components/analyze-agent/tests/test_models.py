"""Envelope (de)serialization / schema validation tests (frontend contract)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from analyze_agent.models import ResultEnvelope

VALID = {
    "change_request": "remove the rear-door module",
    "target_nodes": [
        {"id": "/Demo/Door/Door", "label": "Door", "type": "APPLICATION-SW-COMPONENT-TYPE"}
    ],
    "what_breaks": {
        "summary": "DoorControl and EDC lose their door inputs; 4 signal chains lose their source.",
        "impacted": [
            {
                "id": "/Demo/DoorControl/DoorControl",
                "type": "APPLICATION-SW-COMPONENT-TYPE",
                "hops": 1,
                "via": ["DoorStatus", "DoorCommands"],
                "severity": "high",
                "domain": "body/doors",
                "explanation": "Loses StatusLeft/Right inputs and Command targets.",
            }
        ],
        "graph": {
            "nodes": [{"id": "/Demo/Door/Door"}, {"id": "/Demo/DoorControl/DoorControl"}],
            "edges": [{"from": "/Demo/DoorControl/DoorControl", "to": "/Demo/Door/Door"}],
        },
    },
    "what_it_costs": {
        "bom_saved": {"low": 10.0, "high": 30.0, "currency": "USD", "basis": "per vehicle"},
        "eng_rework": {"low": 40.0, "high": 120.0, "unit": "hours"},
        "net_assessment": "neutral",
        "line_items": [{"label": "Door HW", "low": 10.0, "high": 30.0, "unit": "USD"}],
    },
    "what_it_risks": {
        "items": [
            {
                "category": "safety",
                "severity": "high",
                "title": "Loss of door status",
                "detail": "Status signals feeding the network are removed.",
                "revalidation_required": True,
            }
        ]
    },
    "confidence": {"level": "medium"},
}


def test_roundtrip():
    env = ResultEnvelope.model_validate(VALID)
    dumped = env.model_dump()
    assert dumped["target_nodes"][0]["label"] == "Door"
    assert dumped["what_it_costs"]["bom_saved"]["currency"] == "USD"
    assert dumped["confidence"]["model_agreement"] is None
    # Re-validating the dump must succeed (stable contract).
    ResultEnvelope.model_validate(dumped)


def test_rejects_bad_severity():
    bad = {**VALID}
    bad["confidence"] = {"level": "extreme"}
    with pytest.raises(ValidationError):
        ResultEnvelope.model_validate(bad)


def test_requires_core_sections():
    with pytest.raises(ValidationError):
        ResultEnvelope.model_validate({"change_request": "x", "target_nodes": []})
