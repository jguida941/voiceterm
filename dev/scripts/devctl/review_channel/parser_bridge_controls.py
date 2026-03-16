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
            "--open-findings",
            help="Reviewer checkpoint replacement body for `Open Findings`.",
        ),
        arg_builder(
            "--instruction",
            help="Reviewer checkpoint replacement body for `Current Instruction For Claude`.",
        ),
        arg_builder(
            "--reviewed-scope-item",
            action="append",
            default=[],
            help="Repeatable markdown bullet body for the reviewer checkpoint `Last Reviewed Scope` section.",
        ),
    ]
