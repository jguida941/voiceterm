"""Launch and runtime argument group for `devctl review-channel`."""

from __future__ import annotations

from ..approval_mode import APPROVAL_MODE_CHOICES
from .core import (
    DEFAULT_BRIDGE_REL,
    DEFAULT_REVIEW_CHANNEL_REL,
    DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
    DEFAULT_ROLLOVER_DIR_REL,
    DEFAULT_ROLLOVER_THRESHOLD_PCT,
    DEFAULT_TERMINAL_PROFILE,
)
from .events import (
    DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
    DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
    DEFAULT_REVIEW_STATE_JSON_REL,
)
from .parser_bridge_controls import build_bridge_control_arguments
from .parser_types import ArgumentDef
from .peer_liveness import REVIEWER_MODE_CLI_CHOICES, ReviewerMode
from .state import DEFAULT_REVIEW_STATUS_DIR_REL


def build_launch_arguments(arg_builder) -> list[ArgumentDef]:
    return [
        arg_builder(
            "--terminal",
            choices=["terminal-app", "none"],
            default=None,
            help=(
                "Launch via Terminal.app on macOS or run the conductors headless in "
                "the background. When omitted, launch visibility is resolved from "
                "typed operator/remote-control state."
            ),
        ),
        arg_builder(
            "--terminal-profile",
            default=DEFAULT_TERMINAL_PROFILE,
            help=(
                "Terminal.app profile to apply on live launch. "
                "`auto-dark` picks a dark built-in profile when available; "
                "`default` leaves Terminal.app unchanged."
            ),
        ),
        arg_builder(
            "--review-channel-path",
            default=DEFAULT_REVIEW_CHANNEL_REL,
            help="Path to the active review-channel plan markdown",
        ),
        arg_builder("--bridge-path", default=DEFAULT_BRIDGE_REL, help="Path to the live markdown bridge file"),
        arg_builder(
            "--rollover-dir",
            default=DEFAULT_ROLLOVER_DIR_REL,
            help="Directory where repo-visible rollover handoff bundles are written",
        ),
        arg_builder(
            "--status-dir",
            default=DEFAULT_REVIEW_STATUS_DIR_REL,
            help="Directory where latest bridge-backed status projections are written",
        ),
        arg_builder(
            "--promotion-plan",
            default=None,
            help=("Active-plan checklist used for repo-owned next-task promotion and " "derived queue projections"),
        ),
        arg_builder(
            "--artifact-root",
            default=DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
            help="Root directory for canonical event-backed review-channel artifacts",
        ),
        arg_builder(
            "--state-json",
            default=DEFAULT_REVIEW_STATE_JSON_REL,
            help="Canonical reduced review-channel state JSON path",
        ),
        arg_builder(
            "--emit-projections",
            default=DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
            help="Directory where canonical event-backed projections are written",
        ),
        arg_builder(
            "--rollover-threshold-pct",
            type=int,
            default=DEFAULT_ROLLOVER_THRESHOLD_PCT,
            help=("Context-remaining percentage that should trigger a planned self-relaunch " "before compaction"),
        ),
        arg_builder(
            "--rollover-trigger",
            choices=["context-threshold", "manual", "peer-stale"],
            default="context-threshold",
            help="Reason recorded in the rollover handoff bundle",
        ),
        arg_builder(
            "--await-ack-seconds",
            type=int,
            default=DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
            help=(
                "How long a live launch should wait for a fresh Codex reviewer "
                "heartbeat, and how long a live rollover should wait for visible "
                "Codex/Claude ACK lines from the fresh conductor sessions before "
                "failing closed. Must be greater than zero for rollover."
            ),
        ),
        arg_builder(
            "--codex-workers",
            type=int,
            default=0,
            help="Requested optional Codex worker-fanout budget (0 keeps the launcher conductor-only)",
        ),
        arg_builder(
            "--claude-workers",
            type=int,
            default=0,
            help="Requested optional Claude worker-fanout budget (0 keeps the launcher conductor-only)",
        ),
        *_launch_mode_arguments(arg_builder),
        *_remote_control_attachment_arguments(arg_builder),
        arg_builder(
            "--dry-run",
            action="store_true",
            help="Build the launch bundle without opening Terminal.app windows",
        ),
        arg_builder(
            "--bypass-reason",
            default="",
            help=(
                "Deprecated request reason for a launch-discipline bypass. "
                "Use --bypass-receipt-id to consume an active typed bypass receipt."
            ),
        ),
        arg_builder(
            "--bypass-receipt-id",
            default="",
            help=(
                "Typed BypassLifecycle receipt id required for trusted/no-prompt "
                "provider launch modes."
            ),
        ),
        *build_bridge_control_arguments(
            arg_builder,
            reviewer_mode_choices=REVIEWER_MODE_CLI_CHOICES,
            default_reviewer_mode=ReviewerMode.ACTIVE_DUAL_AGENT,
        ),
    ]


def _launch_mode_arguments(arg_builder) -> list[ArgumentDef]:
    return [
        arg_builder(
            "--approval-mode",
            choices=list(APPROVAL_MODE_CHOICES),
            default=None,
            help=(
                "Shared approval policy for conductor launches. When unset, the "
                "launcher auto-selects `trusted` for headless `interaction_mode="
                "remote_control` launches (which cannot render local sandbox-"
                "escalation prompts) and otherwise falls back to `balanced`. "
                "`trusted` enables provider no-prompt modes, and `strict` reserves "
                "dangerous/publish-class actions for explicit approval surfaces."
            ),
        ),
        arg_builder(
            "--dangerous",
            action="store_true",
            help=(
                "Legacy compatibility alias for `--approval-mode trusted`; uses "
                "provider no-prompt flags (`codex --dangerously-bypass-...`, "
                "`claude --dangerously-skip-permissions`)"
            ),
        ),
        arg_builder(
            "--scope",
            default=None,
            help=(
                "Active-plan doc to auto-scope the launch. Rewrites "
                "`Current Instruction For Claude` from the plan's first unchecked "
                "execution-checklist item before launching conductors. Accepts a "
                "plan filename (e.g. `review_probes`), a full relative path "
                "(e.g. `dev/active/review_probes.md`), or an MP id (e.g. `MP-368`)."
            ),
        ),
        arg_builder(
            "--recover-provider",
            choices=["claude", "codex", "cursor"],
            default="claude",
            help="Provider conductor to replace during `review-channel --action recover`.",
        ),
        arg_builder(
            "--daemon-kind",
            choices=["publisher", "reviewer_supervisor", "all"],
            default="all",
            help="Daemon target for repo-owned review-channel stop actions.",
        ),
        arg_builder(
            "--stop-grace-seconds",
            type=float,
            default=5.0,
            help=(
                "How long `review-channel --action stop` should wait for a daemon "
                "to record stopped lifecycle state after SIGINT."
            ),
        ),
        arg_builder("--script-dir", help="Optional directory for generated conductor launch scripts"),
    ]


def _remote_control_attachment_arguments(arg_builder) -> list[ArgumentDef]:
    return [
        arg_builder(
            "--session-name",
            default="",
            help="Optional external remote-control session label for typed attachment state.",
        ),
        arg_builder(
            "--remote-provider",
            choices=["claude", "codex", "cursor"],
            default="claude",
            help="Provider for an external remote-control session attachment.",
        ),
        arg_builder(
            "--remote-role",
            choices=["implementer", "reviewer", "operator"],
            default="implementer",
            help="Role the external remote-control session currently owns.",
        ),
        arg_builder(
            "--attachment-status",
            choices=["attached", "unknown", "detached", "stale"],
            default="attached",
            help="Typed lifecycle state for the external remote-control attachment.",
        ),
        arg_builder("--session-url", default="", help="External remote-control session URL, when known."),
        arg_builder("--remote-session-id", default="", help="External remote-control session id, when known."),
        arg_builder(
            "--metadata-path",
            default="",
            help="Optional metadata path echoed into the typed remote-control attachment.",
        ),
        arg_builder(
            "--launcher-source",
            default="",
            help="Repo-owned source that created the remote-control attachment.",
        ),
        arg_builder(
            "--host-pid",
            type=int,
            default=None,
            help="Local host process pid for the remote-control lifecycle.",
        ),
        arg_builder("--host-session-label", default="", help="Local host session label for the remote-control lifecycle."),
        arg_builder(
            "--heartbeat-ttl-seconds",
            type=int,
            default=900,
            help="Seconds before a remote-control heartbeat expires.",
        ),
        arg_builder("--previous-operator-mode", default="", help="Operator mode observed before entering remote control."),
        arg_builder("--entrypoint", default="", help="Slash or launcher entrypoint that touched the attachment."),
    ]


__all__ = ["build_launch_arguments"]
