"""Analyze agent: answer a natural-language change request against a KB.

Thin adapters (Lambda / CLI) over a single shared entry point,
:func:`analyze_agent.core.run_analyze`, which drives an in-process Strands agent.
The agent navigates the precomputed Markdown knowledge base (built by the
Ingestion Agent) with four read-only tools and emits one validated result
envelope via a single Bedrock ``structured_output`` call.
"""

from .core import Config, run_analyze

__all__ = ["Config", "run_analyze"]

__version__ = "0.1.0"
