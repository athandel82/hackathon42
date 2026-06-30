"""Build the in-process Strands agent: Bedrock model + tools + the skill.

``skill.md`` is loaded verbatim as the system prompt — it is the single source
of truth for the procedure. The model only sequences tool calls; the tools
(``scan_repo``, ``write_kb_file``, ``record_status``) do all deterministic work.
"""

from __future__ import annotations

import os
from pathlib import Path

from .tools import record_status, scan_repo, write_kb_file

SKILL_PATH = Path(__file__).parent / "skill.md"


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def build_agent():
    """Construct the agent. Imports Strands lazily so the package can be
    imported (and unit-tested) without the SDK present."""
    from strands import Agent
    from strands.models import BedrockModel

    region = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION")
    model = BedrockModel(
        model_id=os.environ["BEDROCK_MODEL_ID"],
        region_name=region,
        temperature=0.0,  # deterministic orchestration
    )
    return Agent(
        model=model,
        system_prompt=load_skill(),
        tools=[scan_repo, write_kb_file, record_status],
        callback_handler=None,  # no console streaming inside Lambda
    )
