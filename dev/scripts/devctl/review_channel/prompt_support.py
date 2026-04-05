"""Support helpers for review-channel conductor prompt rendering."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from ..common import display_path
from ..context_graph.escalation import (
    build_context_escalation_packet,
    collect_query_terms,
    normalize_query_terms,
)
from ..runtime.conductor_capability import (
    build_conductor_capability_state,
    context_graph_bootstrap_command,
    session_resume_command_for_role,
)
from ..runtime.review_state_models import ConductorCapabilityState
from .handoff import (
    BRIDGE_LIVENESS_KEYS,
    expected_rollover_ack_line,
    expected_rollover_ack_section,
)
from .prompt_guards import reviewer_takeover_note, startup_context_follow_up

if TYPE_CHECKING:
    from .core import LaneAssignment


def opening_line(
    *,
    provider_name: str,
    handoff_bundle: dict[str, str] | None,
) -> str:
    """Return the first instruction line for a new conductor prompt."""
    return (
        f"You are the fresh {provider_name} conductor for a planned "
        "review-channel markdown-bridge rollover. Resume the existing "
        "conductor role exactly."
        if handoff_bundle is not None
        else
        f"You are the {provider_name} conductor for the active review-channel "
        "markdown-bridge loop."
    )


def bootstrap_files(
    *,
    capability: ConductorCapabilityState,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    handoff_bundle: dict[str, str] | None,
) -> list[str]:
    """Return the ordered bootstrap commands and files for one conductor."""
    resume_command = session_resume_command_for_role(capability.role)
    files: list[str] = [
        (
            f"Run `{capability.startup_context_command}` first. "
            + startup_context_follow_up(capability)
            + " Then run "
            f"`{resume_command}` for the canonical role bootstrap packet. Then run "
            f"`{context_graph_bootstrap_command()}` for slim startup context "
            "(repo state, active plans, hotspots, key commands). "
            "Do not trust a user summary, prior chat continuity, or memory as a "
            "substitute for this Step 0 receipt. "
            "Do not echo the startup packet back into chat by default; keep any "
            "bootstrap acknowledgement to blocker state plus next step unless the "
            "operator asks for more detail. "
            + reviewer_takeover_note(capability)
            + " "
            "Then follow deep links when task scope requires full authority: "
            "`AGENTS.md` (SDLC policy), `dev/active/INDEX.md` (plan registry), "
            "`dev/active/MASTER_PLAN.md` (execution state). "
            "Use `--query '<term>'` for targeted subgraphs on specific files or MPs."
        ),
        display_path(review_channel_path, repo_root=repo_root),
        display_path(bridge_path, repo_root=repo_root),
    ]
    if handoff_bundle is None:
        return files
    files.extend(
        [
            (
                "Treat the handoff bundle as restart context only. After you "
                "read it, re-read `bridge.md` and prefer the current reviewer-"
                "owned bridge sections plus typed startup/status output over "
                "any stale handoff summary. If the handoff bundle conflicts "
                "with live bridge state, the live bridge wins."
            ),
            display_path(Path(handoff_bundle["markdown_path"]), repo_root=repo_root),
            display_path(Path(handoff_bundle["json_path"]), repo_root=repo_root),
        ]
    )
    return files


def resolve_conductor_capability(
    *,
    provider: str,
    role: str,
    bridge_liveness: dict[str, object] | None,
) -> ConductorCapabilityState:
    """Return the typed capability contract for one conductor prompt."""
    reviewer_mode = str((bridge_liveness or {}).get("reviewer_mode") or "active_dual_agent")
    return build_conductor_capability_state(
        provider=provider,
        role=role,
        reviewer_mode=reviewer_mode,
    )


def resolve_worker_budget(
    *,
    provider: str,
    requested_worker_budget: int | None,
    codex_workers: int,
    claude_workers: int,
) -> int:
    """Return the effective worker budget for one conductor."""
    if requested_worker_budget is not None:
        try:
            return max(0, int(requested_worker_budget))
        except (TypeError, ValueError):
            return 0
    if provider == "codex":
        return max(0, int(codex_workers or 0))
    if provider == "claude":
        return max(0, int(claude_workers or 0))
    return 0


def rollover_ack_details(
    *,
    provider: str,
    handoff_bundle: dict[str, str] | None,
) -> tuple[str | None, str | None]:
    """Return the expected rollover ACK line and bridge section."""
    if handoff_bundle is None:
        return None, None
    return (
        expected_rollover_ack_line(
            provider=provider,
            rollover_id=handoff_bundle["rollover_id"],
        ),
        expected_rollover_ack_section(provider=provider),
    )


def bridge_liveness_lines(bridge_liveness: dict[str, object] | None) -> list[str]:
    """Render the current bridge liveness snapshot for a conductor prompt."""
    if bridge_liveness is None:
        return []
    lines = ["Current bridge liveness snapshot:"]
    for key in BRIDGE_LIVENESS_KEYS:
        if key == "last_reviewed_scope_present":
            continue
        value = bridge_liveness.get(key)
        if key == "last_codex_poll_utc" and not value:
            value = "n/a"
        lines.append(f"- {key}: {value}")
    lines.append("")
    return lines


def rollover_ack_lines(
    *,
    rollover_ack_line: str | None,
    rollover_ack_section: str | None,
) -> list[str]:
    """Render the rollover ACK instructions for a fresh conductor session."""
    if rollover_ack_line is None or rollover_ack_section is None:
        return []
    return [
        (
            "- First action after bootstrap: write this exact rollover "
            f"ACK line into `{rollover_ack_section}` in `bridge.md`: "
            f"`{rollover_ack_line}`"
        ),
        (
            "- Do not start new work until that ACK line is visible in "
            f"`{rollover_ack_section}`; the retiring session uses that "
            "owned-section ACK to prove the fresh conductor is live."
        ),
    ]


def context_escalation_lines(*, lanes: list["LaneAssignment"]) -> list[str]:
    """Render the bounded context-escalation packet for the active lanes."""
    lines = [
        "",
        "Context escalation policy:",
        (
            "- When an instruction mentions an MP, file, guard, or subsystem you "
            "have not read yet, run `python3 dev/scripts/devctl.py context-graph "
            "--query '<term>' --format md` before widening scope."
        ),
        (
            "- Trigger the same query before editing unread files, after repeated "
            "failed attempts, or when blast radius is unclear."
        ),
    ]
    lane_terms = normalize_query_terms(
        (
            "review_channel",
            *collect_query_terms([lane.mp_scope for lane in lanes], max_terms=3),
        ),
        max_terms=4,
    )
    packet = build_context_escalation_packet(
        trigger="review-channel-bootstrap",
        query_terms=lane_terms,
        options={"max_chars": 1200},
    )
    if packet is None:
        return lines
    payload = asdict(packet)
    lines.extend(
        [
            "- Preloaded bounded packet for the active lane scopes:",
            payload["markdown"],
        ]
    )
    return lines
