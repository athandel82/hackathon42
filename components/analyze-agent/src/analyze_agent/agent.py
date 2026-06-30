"""Build the in-process Strands agent: Bedrock model + read-only KB tools.

``analyze_prompt.md`` is loaded verbatim as the system prompt — the single source
of truth for how the agent navigates the KB and fills the result envelope. The
final answer is one ``structured_output`` call against :class:`ResultEnvelope`.
"""

from __future__ import annotations

import os
from pathlib import Path

from .tools import blast_radius, kb_read, resolve_path, trace_signals

PROMPT_PATH = Path(__file__).parent / "analyze_prompt.md"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_agent():
    """Construct the agent. Imports Strands lazily so the package can be
    imported (and unit-tested) without the SDK present."""
    from strands import Agent
    from strands.models import BedrockModel

    region = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION")
    model = BedrockModel(
        model_id=os.environ["BEDROCK_MODEL_ID"],
        region_name=region,
        temperature=0.0,  # deterministic navigation + synthesis
    )
    return Agent(
        model=model,
        system_prompt=load_prompt(),
        tools=[resolve_path, blast_radius, trace_signals, kb_read],
        callback_handler=None,  # no console streaming inside Lambda
    )
