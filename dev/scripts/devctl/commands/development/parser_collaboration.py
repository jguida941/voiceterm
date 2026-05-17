"""Collaboration argument groups for ``devctl develop``."""

from __future__ import annotations

import argparse


def add_collaboration_options(
    cmd: argparse.ArgumentParser,
    *,
    collaboration_mode_choices: tuple[str, ...],
    role_preset_choices: tuple[str, ...],
) -> None:
    """Add collaboration mode and role preset selectors."""
    _add_mode_options(
        cmd,
        collaboration_mode_choices=collaboration_mode_choices,
        role_preset_choices=role_preset_choices,
    )
    _add_role_binding_options(cmd)
    _add_mode_chain_options(cmd)
    _add_packet_route_options(cmd)
    _add_profile_validation_options(cmd)


def _add_mode_options(
    cmd: argparse.ArgumentParser,
    *,
    collaboration_mode_choices: tuple[str, ...],
    role_preset_choices: tuple[str, ...],
) -> None:
    cmd.add_argument(
        "--collaboration-mode",
        choices=collaboration_mode_choices,
        default="",
        help=(
            "Requested read-model collaboration mode, such as pair_review, "
            "dashboard_led, agent_sync, intake_fanout, or dogfood_campaign."
        ),
    )
    cmd.add_argument(
        "--role-preset",
        choices=role_preset_choices,
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


def _add_role_binding_options(cmd: argparse.ArgumentParser) -> None:
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


def _add_mode_chain_options(cmd: argparse.ArgumentParser) -> None:
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


def _add_packet_route_options(cmd: argparse.ArgumentParser) -> None:
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


def _add_profile_validation_options(cmd: argparse.ArgumentParser) -> None:
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
