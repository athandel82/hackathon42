"""Local CLI adapter — ``python -m analyze_agent``.

Reads the KB the Ingestion Agent wrote locally (``--kb-dir``) and answers a
change request. The only always-required AWS call is Bedrock; storage defaults
to local unless ``KB_BUCKET``/``RESULTS_TABLE`` (and no ``--kb-dir``) select AWS.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .core import Config, run_analyze


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="analyze_agent",
        description="Answer a change request against an AUTOSAR KB (blast radius / cost / risk).",
    )
    ap.add_argument("--repo-id", required=True, help="Repository slug (e.g. patrikja__autosar__master).")
    ap.add_argument("--change-request", required=True, help="Natural-language change request.")
    ap.add_argument("--kb-dir", default=None,
                    help="Local KB root (forces LOCAL mode); expects <kb-dir>/<repo-id>/kb/. "
                         "Omit and set KB_BUCKET/RESULTS_TABLE for AWS mode.")
    ap.add_argument("--no-cache", action="store_true", help="Bypass the result cache.")
    args = ap.parse_args(argv)

    cfg = Config.from_env(kb_dir=args.kb_dir)
    try:
        envelope = run_analyze(args.repo_id, args.change_request,
                               cfg=cfg, use_cache=not args.no_cache)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(envelope, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
