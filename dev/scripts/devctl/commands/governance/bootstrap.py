"""devctl governance-bootstrap command implementation."""

from __future__ import annotations

from dataclasses import asdict

from ...governance_bootstrap_support import bootstrap_governance_pilot_repo
from .common import emit_governance_command_output, render_governance_value_error


def _render_markdown(result) -> str:
    lines = ["# devctl governance-bootstrap", ""]
    lines.append(f"- target_repo: {result.target_repo}")
    lines.append(f"- git_state: {result.git_state}")
    lines.append(f"- repaired_git_file: {result.repaired_git_file}")
    lines.append(f"- initialized_git_repo: {result.initialized_git_repo}")
    lines.append(f"- broken_gitdir_hint: {result.broken_gitdir_hint or '(none)'}")
    lines.append(f"- starter_policy_path: {result.starter_policy_path or '(none)'}")
    lines.append(f"- starter_policy_written: {result.starter_policy_written}")
    lines.append(f"- starter_policy_preset: {result.starter_policy_preset or '(none)'}")
    lines.append(
        f"- starter_setup_guide_path: {result.starter_setup_guide_path or '(none)'}"
    )
    lines.append(
        f"- starter_setup_guide_written: {result.starter_setup_guide_written}"
    )
    if result.starter_policy_warnings:
        lines.append(
            "- starter_policy_warnings: "
            + " | ".join(result.starter_policy_warnings)
        )
    lines.append(f"- created_at_utc: {result.created_at_utc}")
    if result.next_steps:
        lines.extend(["", "## Next steps"])
        for step in result.next_steps:
            lines.append(f"- {step}")
    return "\n".join(lines)


def run(args) -> int:
    """Normalize copied pilot repos into standalone git worktrees."""
    try:
        result = bootstrap_governance_pilot_repo(
            args.target_repo,
            write_starter_policy=bool(getattr(args, "write_starter_policy", True)),
            force_starter_policy=bool(getattr(args, "force_starter_policy", False)),
        )
    except ValueError as exc:
        return render_governance_value_error(exc)

    return emit_governance_command_output(
        args,
        command="governance-bootstrap",
        json_payload=asdict(result),
        markdown_output=_render_markdown(result),
    )
