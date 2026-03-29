"""Bridge/reviewer parser argument helpers for review-channel."""

from __future__ import annotations

from typing import Any, Callable, Sequence


def build_bridge_control_arguments(
    arg_builder: Callable[..., Any],
    *,
    reviewer_mode_choices: Sequence[str],
    default_reviewer_mode: str,
) -> list[Any]:
    """Return the bridge/reviewer control arguments for launch/status actions."""
    return [
        arg_builder(
            "--refresh-bridge-heartbeat-if-stale",
            action="store_true",
            help=(
                "When the markdown bridge is otherwise launchable but reviewer heartbeat "
                "metadata is stale or missing, refresh it before launch continues."
            ),
        ),
        arg_builder(
            "--auto-promote",
            action="store_true",
            help=(
                "When the bridge shows an accepted verdict with no open findings "
                "and an idle instruction, automatically promote the next unchecked "
                "plan item into the bridge before continuing."
            ),
        ),
        arg_builder(
            "--reviewer-mode",
            choices=list(reviewer_mode_choices),
            default=default_reviewer_mode,
            help=(
                "Reviewer operating mode recorded in bridge metadata and liveness "
                "projections. Canonical values are persisted; human-facing aliases "
                "such as `agents` -> `active_dual_agent` and `developer` -> "
                "`single_agent` are accepted for convenience."
            ),
        ),
        arg_builder(
            "--reason",
            default="manual-review",
            help="Short reason recorded on reviewer heartbeat/checkpoint writes.",
        ),
        arg_builder(
            "--verdict",
            help="Reviewer checkpoint replacement body for `Current Verdict`.",
        ),
        arg_builder(
            "--verdict-file",
            help=(
                "Read the reviewer checkpoint replacement body for "
                "`Current Verdict` from a file. Prefer this when the markdown "
                "contains backticks or other shell-sensitive content."
            ),
        ),
        arg_builder(
            "--open-findings",
            help="Reviewer checkpoint replacement body for `Open Findings`.",
        ),
        arg_builder(
            "--open-findings-file",
            help=(
                "Read the reviewer checkpoint replacement body for "
                "`Open Findings` from a file. Prefer this when the markdown "
                "contains backticks or other shell-sensitive content."
            ),
        ),
        arg_builder(
            "--instruction",
            help="Reviewer checkpoint replacement body for `Current Instruction For Claude`.",
        ),
        arg_builder(
            "--instruction-file",
            help=(
                "Read the reviewer checkpoint replacement body for "
                "`Current Instruction For Claude` from a file. Prefer this "
                "when the markdown contains backticks or other "
                "shell-sensitive content."
            ),
        ),
        arg_builder(
            "--checkpoint-payload-file",
            help=(
                "Read reviewer-checkpoint bodies from one JSON payload file. "
                "Preferred for AI-generated markdown or any shell-sensitive "
                "content. The payload must define `verdict`, "
                "`open_findings`, `instruction`, and `reviewed_scope_items`."
            ),
        ),
        arg_builder(
            "--rotate-instruction-revision",
            action="store_true",
            help=(
                "Force a new current instruction revision on the next reviewer "
                "checkpoint even if the instruction body text is unchanged."
            ),
        ),
        arg_builder(
            "--expected-instruction-revision",
            help=(
                "Fail-closed precondition for instruction-mutating reviewer "
                "writes. Use the live `current_instruction_revision` from "
                "`review-channel --action bridge-poll --format json` or the "
                "bridge header when replacing the current instruction."
            ),
        ),
        arg_builder(
            "--reviewed-scope-item",
            action="append",
            default=[],
            help="Repeatable markdown bullet body for the reviewer checkpoint `Last Reviewed Scope` section.",
        ),
    ]
