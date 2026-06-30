"""Ingestion agent: turn an AUTOSAR ARXML ECU extract into a Markdown KB.

The package is a thin set of adapters (Lambda / CLI) over a single shared
entry point, :func:`ingest_agent.core.run_ingest`, which drives an in-process
Strands agent. The agent is told what to do by ``skill.md`` (loaded verbatim as
the system prompt) and given three deterministic tools (``scan_repo``,
``write_kb_file``, ``record_status``).
"""

from .core import Config, run_ingest, slug

__all__ = ["Config", "run_ingest", "slug"]

__version__ = "0.1.0"
