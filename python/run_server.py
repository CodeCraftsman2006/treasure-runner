#!/usr/bin/env python3
"""Launch the Treasure Runner web server."""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Treasure Runner web server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to world .ini file (default: assets/starter.ini)",
    )
    parser.add_argument("--reload", action="store_true", help="Dev auto-reload")
    args = parser.parse_args()

    if args.config:
        os.environ["TREASURE_RUNNER_CONFIG"] = str(Path(args.config).resolve())

    uvicorn.run(
        "treasure_runner.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
