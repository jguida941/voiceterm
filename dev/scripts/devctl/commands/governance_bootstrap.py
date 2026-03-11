"""devctl governance-bootstrap command implementation."""

from __future__ import annotations

import json
from dataclasses import asdict

from ..common import emit_output, pipe_output, write_output
from ..governance_bootstrap_support import bootstrap_governance_pilot_repo


def _render_markdown(result) -> str:
    lines = ["# devctl governance-bootstrap", ""]
    lines.append(f"- target_repo: {result.target_repo}")
    lines.append(f"- git_state: {result.git_state}")
    lines.append(f"- repaired_git_file: {result.repaired_git_file}")
    lines.append(f"- initialized_git_repo: {result.initialized_git_repo}")
    lines.append(
        f"- broken_gitdir_hint: {result.broken_gitdir_hint or '(none)'}"
    )
    lines.append(f"- created_at_utc: {result.created_at_utc}")
    return "\n".join(lines)


def run(args) -> int:
    """Normalize copied pilot repos into standalone git worktrees."""
    try:
        result = bootstrap_governance_pilot_repo(getattr(args, "target_repo"))
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    output = (
        json.dumps(asdict(result), indent=2)
        if args.format == "json"
        else _render_markdown(result)
    )
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    return 0 if pipe_code == 0 else pipe_code
