"""devctl quality-policy command implementation."""

from __future__ import annotations

import json
from dataclasses import asdict

from ..common import emit_output, pipe_output, write_output
from . import resolve_quality_policy
from .rendering import build_quality_policy_payload, render_quality_policy_markdown


def run(args) -> int:
    """Resolve and render the active quality-policy configuration."""
    policy = resolve_quality_policy(
        policy_path=getattr(args, "quality_policy", None),
    )
    payload = build_quality_policy_payload(policy)
    output = (
        json.dumps(asdict(payload), indent=2)
        if args.format == "json"
        else render_quality_policy_markdown(policy)
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
