"""Command line entry point for YAML-driven offline scenarios."""

import argparse
import json
from pathlib import Path
from typing import List, Optional

from iam_chaos.engine import ScenarioEngine
from iam_chaos.reporting import write_artifacts

def parse_seed(value: str):
    try:
        return int(value)
    except ValueError:
        return value



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iam-chaos",
        description="Run deterministic IAM lifecycle scenarios offline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser(
        "run", help="execute a versioned YAML scenario offline"
    )
    run_parser.add_argument(
        "scenario", type=Path, help="versioned YAML scenario file"
    )
    run_parser.add_argument(
        "--seed", type=parse_seed, help="override the seed declared by the scenario"
    )
    run_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/iam-chaos"),
        help="directory for payloads.json, events.json and report.json",
    )
    run_parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="return zero when expected/actual assertions differ",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = ScenarioEngine(seed=args.seed).run(args.scenario)
    paths = write_artifacts(report, args.output_dir)
    print(json.dumps(report.summary, indent=2, sort_keys=True))
    for name, path in paths.items():
        print("{}: {}".format(name, path))
    if report.summary["failed"] and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
