"""Run the HarnessWeaver ATAM evaluation harness with the DeepAgents backend."""

from __future__ import annotations

import sys
from pathlib import Path


# Direct script execution has no package context; add this folder for its local package.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from atam_harness.config import build_parser, resolve_config
    from atam_harness.paths import REPOSITORY_ROOT
    from atam_harness.runner import run
else:
    from .atam_harness.config import build_parser, resolve_config
    from .atam_harness.paths import REPOSITORY_ROOT
    from .atam_harness.runner import run


def main() -> int:
    """Load environment variables, resolve CLI/YAML settings, and run the agent."""
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "python-dotenv is required; install examples/atam/deepagents/requirements.txt"
        ) from exc

    # Shell variables remain authoritative; .env supplies local development defaults.
    load_dotenv(REPOSITORY_ROOT / ".env", override=False)
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = resolve_config(args)
    except ValueError as exc:
        parser.error(str(exc))
    run(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
