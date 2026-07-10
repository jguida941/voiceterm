#!/usr/bin/env python3
"""Workflow helper for autonomy workflow config resolution and report exports."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.workflow_bridge.controller_config import (
    resolve_controller_config_from_env,
    write_controller_config_outputs,
)
from dev.scripts.workflow_bridge.ralph_config import (
    resolve_ralph_config_from_env,
    write_ralph_config_outputs,
)
from dev.scripts.workflow_bridge.report_exports import (
    assert_swarm_ok,
    export_controller,
    export_swarm,
)
from dev.scripts.workflow_bridge.swarm_config import (
    resolve_swarm_config_from_env,
    write_swarm_config_outputs,
)


def _resolve_controller_config_command(args: argparse.Namespace) -> int:
    event_name = args.event_name or os.getenv("EVENT_NAME", "")
    try:
        config = resolve_controller_config_from_env(event_name=event_name, env=os.environ)
    except ValueError as exc:
        print(str(exc))
        return 1
    write_controller_config_outputs(config, Path(args.github_output))
    return 0


def _resolve_ralph_config_command(args: argparse.Namespace) -> int:
    event_name = args.event_name or os.getenv("EVENT_NAME", "")
    try:
        config = resolve_ralph_config_from_env(event_name=event_name, env=os.environ)
    except ValueError as exc:
        print(str(exc))
        return 1
    write_ralph_config_outputs(config, Path(args.github_output))
    return 0


def _resolve_swarm_config_command(args: argparse.Namespace) -> int:
    try:
        config = resolve_swarm_config_from_env(os.environ)
    except ValueError as exc:
        print(str(exc))
        return 1
    write_swarm_config_outputs(config, Path(args.github_output))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_controller = sub.add_parser(
        "resolve-controller-config",
        help="Resolve and validate autonomy-controller config, then append outputs.",
    )
    resolve_controller.add_argument("--github-output", required=True)
    resolve_controller.add_argument("--event-name", default="")

    resolve_ralph = sub.add_parser(
        "resolve-ralph-config",
        help="Resolve and validate coderabbit-ralph config, then append outputs.",
    )
    resolve_ralph.add_argument("--github-output", required=True)
    resolve_ralph.add_argument("--event-name", default="")

    resolve_swarm = sub.add_parser(
        "resolve-swarm-config",
        help="Resolve and validate swarm-run config, then append outputs.",
    )
    resolve_swarm.add_argument("--github-output", required=True)

    controller = sub.add_parser("export-controller", help="Export autonomy-controller outputs")
    controller.add_argument("--input-file", required=True)
    controller.add_argument("--github-output", required=True)

    swarm = sub.add_parser("export-swarm", help="Export autonomy-run swarm outputs")
    swarm.add_argument("--input-file", required=True)
    swarm.add_argument("--github-output", required=True)

    assert_ok = sub.add_parser("assert-swarm-ok", help="Exit non-zero when swarm payload is not ok")
    assert_ok.add_argument("--input-file", required=True)

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "resolve-controller-config":
        return _resolve_controller_config_command(args)
    if args.command == "resolve-ralph-config":
        return _resolve_ralph_config_command(args)
    if args.command == "resolve-swarm-config":
        return _resolve_swarm_config_command(args)
    if args.command == "export-controller":
        return export_controller(args)
    if args.command == "export-swarm":
        return export_swarm(args)
    if args.command == "assert-swarm-ok":
        return assert_swarm_ok(args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
