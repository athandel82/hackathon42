"""Local CLI adapter — ``python -m ingest_agent``.

Runs the whole pipeline on a laptop with local AWS credentials. The only
always-required AWS call is Bedrock; storage defaults to a local ``./out``
directory unless ``KB_BUCKET``/``REPOS_TABLE`` (or no ``--out``) select AWS mode.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .core import Config, run_ingest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ingest_agent",
        description="Generate an AUTOSAR ARXML knowledge base from a GitHub repo.",
    )
    ap.add_argument("--github-url", required=True,
                    help="HTTPS URL of the GitHub repo (e.g. https://github.com/patrikja/autosar)")
    ap.add_argument("--branch", default="master", help="Branch to fetch (default: master)")
    ap.add_argument("--out", default=None,
                    help="Local output directory (forces LOCAL mode). "
                         "Omit and set KB_BUCKET/REPOS_TABLE for AWS mode.")
    ap.add_argument("--repo-id", default=None, help="Override the computed repo id slug.")
    args = ap.parse_args(argv)

    cfg = Config.from_env(out_dir=args.out)
    result = run_ingest(args.github_url, args.branch, repo_id=args.repo_id, cfg=cfg)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
