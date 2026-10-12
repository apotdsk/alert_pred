"""Command-line entry point for the alert forecasting pipeline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


STAGES = ("audit", "panel", "backtest", "forecast", "report")


def build_parser() -> argparse.ArgumentParser:
    """Build the pipeline command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-path", help="Use a local raw data file.")
    parser.add_argument("command", nargs="?", choices=(*STAGES, "inspect"))
    parser.add_argument("unit", nargs="?")
    parser.add_argument("date", nargs="?")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a pipeline stage or print all stages for a full run."""
    args = build_parser().parse_args(argv)
    if args.command == "inspect":
        if not args.unit or not args.date:
            build_parser().error("inspect requires <unit> <YYYY-MM-DD>")
        print("inspect")
        return 0

    stages = (args.command,) if args.command else STAGES
    for stage in stages:
        print(stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
