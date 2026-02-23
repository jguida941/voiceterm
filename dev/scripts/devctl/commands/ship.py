"""devctl ship command implementation."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List

from ..common import pipe_output, write_output
from .ship_common import VERSION_RE, render_md, render_text
from .ship_steps import STEP_HANDLERS


def _selected_steps(args) -> List[str]:
    selected_steps: List[str] = []
    if args.verify:
        selected_steps.append("verify")
    if args.tag:
        selected_steps.append("tag")
    if args.notes:
        selected_steps.append("notes")
    if args.github:
        selected_steps.append("github")
    if args.pypi:
        selected_steps.append("pypi")
    if args.homebrew:
        selected_steps.append("homebrew")
    if args.verify_pypi:
        selected_steps.append("verify-pypi")
    return selected_steps


def run(args) -> int:
    """Run the unified release/distribution control-plane workflow."""
    if not VERSION_RE.match(args.version):
        print("Error: --version must be in format X.Y.Z")
        return 2

    selected_steps = _selected_steps(args)
    if not selected_steps:
        print(
            "Error: no steps selected. Choose one or more of --verify --tag --notes --github --pypi --homebrew --verify-pypi."
        )
        return 2

    context = {
        "version": args.version,
        "tag": f"v{args.version}",
        "notes_file": args.notes_output or f"/tmp/voiceterm-release-v{args.version}.md",
    }

    steps: List[Dict] = []
    exit_code = 0
    for name in selected_steps:
        step = STEP_HANDLERS[name](args, context)
        steps.append(step)
        if not step["ok"]:
            exit_code = step["returncode"] or 1
            break

    report = {
        "command": "ship",
        "timestamp": datetime.now().isoformat(),
        "version": context["version"],
        "tag": context["tag"],
        "notes_file": context["notes_file"],
        "selected_steps": selected_steps,
        "steps": steps,
        "ok": exit_code == 0,
        "exit_code": exit_code,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        output = render_md(report)
    else:
        output = render_text(report)

    write_output(output, args.output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return exit_code
