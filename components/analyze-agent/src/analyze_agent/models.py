"""Result envelope (parent §7) as Pydantic models — the structured-output schema.

``ResultEnvelope`` is handed to ``agent.structured_output(...)`` so the model
must return a schema-valid object. ``.model_dump()`` is the exact JSON the
frontend consumes; the frontend stays a pure renderer.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]


class TargetNode(BaseModel):
    id: str
    label: str
    type: str


class Impacted(BaseModel):
    id: str
    type: str
    hops: int
    via: list[str] = Field(default_factory=list)
    severity: Severity
    domain: str
    explanation: str


class Graph(BaseModel):
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)


class WhatBreaks(BaseModel):
    summary: str
    impacted: list[Impacted] = Field(default_factory=list)
    graph: Graph = Field(default_factory=Graph)


class Range(BaseModel):
    low: float
    high: float
    currency: Optional[str] = None
    unit: Optional[str] = None
    basis: Optional[str] = None


class LineItem(BaseModel):
    label: str
    low: float
    high: float
    unit: str


class WhatItCosts(BaseModel):
    bom_saved: Range
    eng_rework: Range
    net_assessment: Literal["favorable", "neutral", "unfavorable"]
    line_items: list[LineItem] = Field(default_factory=list)


class RiskItem(BaseModel):
    category: str
    severity: Severity
    title: str
    detail: str
    revalidation_required: bool


class WhatItRisks(BaseModel):
    items: list[RiskItem] = Field(default_factory=list)


class Confidence(BaseModel):
    level: Severity
    # Reserved for a future multi-model ensemble (parent §7).
    model_agreement: Optional[float] = None


class ResultEnvelope(BaseModel):
    change_request: str
    target_nodes: list[TargetNode]
    what_breaks: WhatBreaks
    what_it_costs: WhatItCosts
    what_it_risks: WhatItRisks
    confidence: Confidence
