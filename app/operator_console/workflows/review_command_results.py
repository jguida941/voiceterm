"""Review-channel completion helpers shared by Operator Console actions."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from .command_builder_reports import (
    evaluate_review_channel_launch,
    evaluate_review_channel_rollover,
    parse_review_channel_report,
)


def resolve_start_swarm_command_result(
    *,
    exit_code: int,
    stdout: str,
    stderr: str,
    evaluator: Callable[[Mapping[str, object]], tuple[bool, str]],
    invalid_json_message: str,
    empty_output_message: str,
) -> tuple[bool, str]:
    """Resolve one Start Swarm command result from JSON or visible stderr."""
    stripped_stdout = stdout.strip()
    if stripped_stdout:
        try:
            report = parse_review_channel_report(stripped_stdout)
        except ValueError:
            detail = first_visible_text_line(stderr) or invalid_json_message
            return False, detail
        return evaluator(report)
    detail = first_visible_text_line(stderr)
    if detail:
        return False, detail
    if exit_code:
        return False, empty_output_message
    return False, invalid_json_message


def resolve_review_channel_completion_message(
    *,
    action: str,
    live: bool,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> tuple[bool, str]:
    """Resolve one user-facing review-channel completion message."""
    stripped_stdout = stdout.strip()
    if stripped_stdout:
        try:
            report = parse_review_channel_report(stripped_stdout)
        except ValueError:
            detail = first_visible_text_line(stderr)
            if detail:
                return False, detail
            command_name = "Live launch" if action == "launch" and live else action.title()
            return False, f"{command_name} did not return a readable status report."
        if action == "rollover":
            return evaluate_review_channel_rollover(report)
        return evaluate_review_channel_launch(report, live=live)
    detail = first_visible_text_line(stderr)
    if detail:
        return False, detail
    if action == "rollover":
        fallback = "Rollover failed." if exit_code else "Rollover completed."
    elif live:
        fallback = "Live launch failed." if exit_code else "Live launch completed."
    else:
        fallback = "Dry run failed." if exit_code else "Dry run completed."
    return exit_code == 0, fallback


def first_visible_text_line(text: str) -> str:
    """Return the first non-empty rendered line from stderr or command output."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
