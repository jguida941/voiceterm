#!/usr/bin/env python3
"""Workflow helper for Mutation Ralph loop config resolution and report parsing."""

from __future__ import annotations

import argparse
if __package__:
    from .mutation_ralph_cli import build_parser
    from .mutation_ralph_config import resolve_config_command, resolve_config_from_env, write_config_outputs
    from .mutation_ralph_loop import (
        build_loop_command,
        extract_failure_reason,
        extract_failure_reason_command,
        run_loop_command,
    )
else:  # pragma: no cover - standalone script fallback
    from mutation_ralph_cli import build_parser
    from mutation_ralph_config import resolve_config_command, resolve_config_from_env, write_config_outputs
    from mutation_ralph_loop import (
        build_loop_command,
        extract_failure_reason,
        extract_failure_reason_command,
        run_loop_command,
    )


def main() -> int:
    args = build_parser(__doc__).parse_args()
    if args.command == "resolve-config":
        return resolve_config_command(args)
    if args.command == "extract-failure-reason":
        return extract_failure_reason_command(args)
    if args.command == "run-loop":
        return run_loop_command(args)
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
