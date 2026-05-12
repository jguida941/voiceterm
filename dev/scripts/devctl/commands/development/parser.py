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
    "design-preflight",
    "baseline-inventory",
    "ingest-intent",
    "ingest-plan",
    "campaign",
    "collaboration-profile",
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
    "agent_sync",
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
    _add_design_preflight_options(cmd)
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
    cmd.add_argument(
        "--enforce-final-response-gate",
        action="store_true",
        default=False,
        help=(
            "Return nonzero when typed controller state says a final response "
            "is not allowed."
        ),
    )
    cmd.add_argument(
        "--proposed-response-text",
        default="",
        help=(
            "Optional terminal response candidate to validate against the typed "
            "final-response gate."
        ),
    )


def _add_collaboration_options(cmd: argparse.ArgumentParser) -> None:
    """Add collaboration mode and role preset selectors."""
    cmd.add_argument(
        "--collaboration-mode",
        choices=COLLABORATION_MODE_CHOICES,
        default="",
        help=(
            "Requested read-model collaboration mode, such as pair_review, "
            "dashboard_led, agent_sync, intake_fanout, or dogfood_campaign."
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
    cmd.add_argument(
        "--profile",
        default="",
        help="Portable collaboration profile id or path label for report output.",
    )
    cmd.add_argument(
        "--provider",
        action="append",
        default=[],
        help="Repeatable provider id participating in the collaboration profile.",
    )
    cmd.add_argument(
        "--role-binding",
        action="append",
        default=[],
        help=(
            "Repeatable role=provider or role=provider:session binding, for "
            "example implementer=claude or reviewer=codex:session_id."
        ),
    )
    cmd.add_argument(
        "--role-count",
        action="append",
        default=[],
        help=(
            "Repeatable role=n request for collaboration-profile fanout, for "
            "example architect=3, researcher=2, watcher=1, or tester=4."
        ),
    )
    cmd.add_argument(
        "--agents",
        dest="generic_agents",
        type=int,
        default=0,
        help=(
            "Generic fanout count for the selected role preset, compiled to "
            "the same typed role-count budget as role=n."
        ),
    )
    cmd.add_argument(
        "--dogfood",
        action="store_true",
        default=False,
        help=(
            "Append a dogfood_campaign tester phase to the typed mode-chain "
            "request; authority still comes from runtime gates."
        ),
    )
    cmd.add_argument(
        "--chain-phase",
        action="append",
        default=[],
        help=(
            "Repeatable role[:collaboration_mode] phase for composable mode "
            "requests, for example implementer:pair_review or tester:dogfood_campaign."
        ),
    )
    cmd.add_argument(
        "--chain-scope",
        default="",
        help="Optional scope ref inherited by child phases in a mode chain.",
    )
    cmd.add_argument(
        "--chain-receipt-ref",
        action="append",
        default=[],
        help="Repeatable child receipt ref for the composite receipt container.",
    )
    cmd.add_argument(
        "--agent-mind-provider",
        action="append",
        default=[],
        help="Repeatable provider id whose AgentMindSlice should be polled.",
    )
    cmd.add_argument(
        "--remote-provider",
        default="",
        help="Provider that owns remote-control lifecycle for this profile.",
    )
    cmd.add_argument(
        "--architecture-agents",
        "--architecture-agent-count",
        dest="architecture_agents",
        type=int,
        default=0,
        help=(
            "Deprecated shortcut for --role-count architect=n in "
            "collaboration-profile fanout; prefer --role-count architect=n."
        ),
    )
    cmd.add_argument(
        "--review-agents",
        "--review-agent-count",
        dest="review_agents",
        type=int,
        default=0,
        help=(
            "Deprecated shortcut for --role-count reviewer=n in "
            "collaboration-profile fanout; prefer --role-count reviewer=n."
        ),
    )
    cmd.add_argument(
        "--source-packet-id",
        default="",
        help="Packet id the collaboration profile starts from.",
    )
    cmd.add_argument(
        "--target-packet-id",
        default="",
        help="Packet id the collaboration profile should route toward.",
    )
    cmd.add_argument(
        "--stop-at-packet",
        "--stop-at-packet-id",
        dest="stop_at_packet",
        default="",
        help=(
            "Packet id whose ack/apply state should trigger the agent_sync "
            "stop-anchor path."
        ),
    )
    cmd.add_argument(
        "--stop-at-mp-row",
        "--stop-at-plan-row",
        dest="stop_at_mp_row",
        default="",
        help=(
            "Master-plan row id whose completed state should trigger the "
            "agent_sync stop-anchor path."
        ),
    )
    cmd.add_argument(
        "--emit-profile-template",
        action="store_true",
        default=False,
        help="Embed a starter portable collaboration profile template.",
    )
    cmd.add_argument(
        "--validate-profile",
        action="store_true",
        default=False,
        help="Fail the report when collaboration profile validation has errors.",
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


def _add_design_preflight_options(cmd: argparse.ArgumentParser) -> None:
    """Add ground-truth design-preflight options."""
    cmd.add_argument(
        "--topic",
        default="",
        help="State, proof channel, or contract topic for design-preflight.",
    )
    cmd.add_argument(
        "--record-ground-truth-receipt",
        action="store_true",
        default=False,
        help="Append a GroundTruthProbeRunReceipt for design-preflight evidence.",
    )
    cmd.add_argument(
        "--since-ref",
        default="",
        help=(
            "Optional base ref for commit-range design-preflight evidence; "
            "matches check_ground_truth_probe_gate --since-ref."
        ),
    )
    cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref for commit-range design-preflight evidence.",
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
        (
            "design-preflight",
            "Probe ground truth before adding architecture/proof surfaces.",
        ),
        (
            "baseline-inventory",
            "Capture the current governed authority substrate before refactors.",
        ),
        ("ingest-intent", "Ingest packet/chat/file intent into typed state."),
        ("ingest-plan", "Ingest a plan packet/file/body into typed plan authority."),
        ("campaign", "Show the remote-control Codex/Claude campaign state."),
        (
            "collaboration-profile",
            "Render a provider-neutral collaboration profile over existing typed surfaces.",
        ),
        ("launch", "Run one read-only controller cycle report."),
    )


__all__ = [
    "COLLABORATION_MODE_CHOICES",
    "DEVELOP_ACTIONS",
    "ROLE_PRESET_CHOICES",
    "add_parser",
]
