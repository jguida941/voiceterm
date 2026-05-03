"""Argument parser wiring for ``devctl develop``."""

from __future__ import annotations

import argparse

from ...common import add_standard_output_arguments

DEVELOP_ACTIONS = (
    "status",
    "next",
    "show",
    "start",
    "watch",
    "verify",
    "submit",
    "close",
    "rollback",
    "pause",
    "resume",
    "audit-guards",
    "audit-packets",
    "ingest-intent",
    "ingest-plan",
    "launch",
)

COLLABORATION_MODE_CHOICES = (
    "solo",
    "pair_review",
    "dashboard_led",
    "intake_fanout",
    "research_fanout",
    "review_fanout",
    "watcher_fanout",
    "isolated_builder_fanout",
    "dogfood_campaign",
)

ROLE_PRESET_CHOICES = (
    "dashboard",
    "implementer",
    "reviewer",
    "architect",
    "researcher",
    "intake",
    "tester",
    "watcher",
    "operator",
)


def add_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``develop`` subcommand."""
    cmd = sub.add_parser(
        "develop",
        help="Read-only typed development controller over MP-377 governance state",
    )
    cmd.add_argument(
        "action",
        nargs="?",
        choices=DEVELOP_ACTIONS,
        help="Controller action. Defaults to status.",
    )
    for action_name, help_text in _action_flags():
        cmd.add_argument(
            f"--{action_name}",
            dest="action_flag",
            action="store_const",
            const=action_name,
            help=help_text,
        )

    _add_controller_options(cmd)
    _add_collaboration_options(cmd)
    _add_packet_options(cmd)
    _add_ingest_options(cmd)
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "terminal"),
        default_format="md",
    )


def _add_controller_options(cmd: argparse.ArgumentParser) -> None:
    """Add common read-only controller options."""
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview the controller cycle without spawning workers or mutating state.",
    )
    cmd.add_argument(
        "--fleet",
        default="default",
        help="Topology preset to render. Only `default` is implemented.",
    )
    cmd.add_argument(
        "--max-cycles",
        type=int,
        default=1,
        help="Maximum controller cycles for launch previews.",
    )
    cmd.add_argument(
        "--max-workers",
        type=int,
        default=0,
        help="Requested worker budget for future fanout planning.",
    )


def _add_collaboration_options(cmd: argparse.ArgumentParser) -> None:
    """Add collaboration mode and role preset selectors."""
    cmd.add_argument(
        "--collaboration-mode",
        choices=COLLABORATION_MODE_CHOICES,
        default="",
        help=(
            "Requested read-model collaboration mode, such as pair_review, "
            "dashboard_led, intake_fanout, or dogfood_campaign."
        ),
    )
    cmd.add_argument(
        "--role-preset",
        choices=ROLE_PRESET_CHOICES,
        default="",
        help=(
            "Requested read-only/mutation-filtered role preset, such as "
            "dashboard, implementer, reviewer, intake, tester, or operator."
        ),
    )


def _add_packet_options(cmd: argparse.ArgumentParser) -> None:
    """Add packet attention and lifecycle options."""
    cmd.add_argument(
        "--max-packets",
        type=int,
        default=30,
        help="Maximum packet-debt rows to include in audit-packets reports.",
    )
    cmd.add_argument(
        "--drain-packets",
        "--drain",
        dest="drain_packets",
        action="store_true",
        default=False,
        help=(
            "For audit-packets only, apply deterministic plan-row ingestion for "
            "eligible packet debt and emit durable-ingestion receipts."
        ),
    )
    cmd.add_argument(
        "--actor",
        default="auto",
        help=(
            "Actor whose packet-attention lane /develop should inspect. "
            "Use `auto` to resolve from typed caller or packet-attention state."
        ),
    )
    cmd.add_argument(
        "--slice-id",
        default="",
        help="Optional development slice id for lifecycle preview actions.",
    )
    cmd.add_argument(
        "--packet-id",
        default="",
        help="Optional packet id for /develop show, lifecycle previews, or ingest intent.",
    )


def _add_ingest_options(cmd: argparse.ArgumentParser) -> None:
    """Add plan-intent ingestion options."""
    cmd.add_argument(
        "--plan-row-id",
        default="",
        help="PlanRow id to write for ingest intent body/file/packet inputs.",
    )
    cmd.add_argument(
        "--title",
        default="",
        help="PlanRow title for ingest intent when the source is not a checklist row.",
    )
    cmd.add_argument(
        "--body",
        default="",
        help="Inline source body for ingest intent.",
    )
    cmd.add_argument(
        "--source",
        default="",
        help=(
            "Markdown plan source file for ingest intent; defaults to "
            "source-kind=markdown_plan_file."
        ),
    )
    cmd.add_argument(
        "--body-file",
        default="",
        help="Legacy source file for ingest intent.",
    )
    cmd.add_argument(
        "--source-kind",
        default="",
        help="Source family for ingest intent, for example chat, file, packet, or develop.",
    )
    cmd.add_argument(
        "--source-ref",
        default="",
        help="Stable evidence ref for ingest intent source provenance.",
    )
    cmd.add_argument(
        "--target-ref",
        default="",
        help="Typed plan target ref for ingest-plan output rows.",
    )
    cmd.add_argument(
        "--anchor-ref",
        dest="anchor_refs",
        action="append",
        default=[],
        help="Repeatable typed anchor ref to attach to an ingest-plan row.",
    )
    cmd.add_argument(
        "--mutation-op",
        default="",
        help="Plan mutation operation to record on ingest-plan rows.",
    )
    cmd.add_argument(
        "--sdlc-stage",
        default="spec",
        help="SDLC stage for explicit ingest-plan rows.",
    )
    cmd.add_argument(
        "--plan-status",
        default="queued",
        help="PlanRow status for explicit ingest-plan rows.",
    )
    cmd.add_argument(
        "--terminal-status",
        choices=("rejected", "duplicate", "obsolete"),
        default="",
        help="Emit a terminal typed receipt instead of writing a PlanRow.",
    )
    cmd.add_argument(
        "--reason",
        default="",
        help="Optional reason for an ingest intent terminal receipt.",
    )


def _action_flags() -> tuple[tuple[str, str], ...]:
    return (
        ("status", "Render controller status."),
        ("next", "Select the next typed development slice."),
        ("show", "Render the typed read command for a slice or packet."),
        ("start", "Preview slice claim / lease prerequisites."),
        ("watch", "Preview live packet/sync watch commands for the actor."),
        ("verify", "Render required verification commands for the slice."),
        ("submit", "Preview governed handoff / submit prerequisites."),
        ("close", "Preview retrospective learning closure for the slice."),
        ("rollback", "Preview typed rollback / recovery prerequisites."),
        ("pause", "Render a typed pause request without mutating state."),
        ("resume", "Render a typed resume request without mutating state."),
        ("audit-guards", "Show guard/probe learning checks for this loop."),
        ("audit-packets", "Show packet carry-forward durable-ingestion debt."),
        ("ingest-intent", "Ingest packet/chat/file intent into typed state."),
        ("ingest-plan", "Ingest a plan packet/file/body into typed plan authority."),
        ("launch", "Run one read-only controller cycle report."),
    )


__all__ = [
    "COLLABORATION_MODE_CHOICES",
    "DEVELOP_ACTIONS",
    "ROLE_PRESET_CHOICES",
    "add_parser",
]
