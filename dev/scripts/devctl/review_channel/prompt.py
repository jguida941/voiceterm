"""Prompt-building helpers for the transitional review-channel launcher."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from ..approval_mode import DEFAULT_APPROVAL_MODE
from ..common import display_path
from ..context_graph.escalation import (
    build_context_escalation_packet,
    collect_query_terms,
    normalize_query_terms,
)
from ..runtime.role_profile import role_for_provider
from .handoff import BRIDGE_LIVENESS_KEYS, expected_rollover_ack_line, expected_rollover_ack_section
from .prompt_sections import operating_contract_lines

if TYPE_CHECKING:
    from .core import LaneAssignment


def build_conductor_prompt(
    *,
    provider: str,
    provider_name: str,
    other_name: str,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    lanes: list["LaneAssignment"],
    codex_workers: int,
    claude_workers: int,
    dangerous: bool,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    retirement_note: str,
    rollover_command: str,
    promote_command: str,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    bridge_liveness: dict[str, object] | None = None,
    handoff_bundle: dict[str, str] | None = None,
) -> str:
    """Render the initial conductor prompt for Codex or Claude."""
    provider_worker_budget = codex_workers if role_for_provider(provider) == "reviewer" else claude_workers
    rollover_ack_line, rollover_ack_section = _rollover_ack_details(
        provider=provider,
        handoff_bundle=handoff_bundle,
    )
    lane_lines = [
        (
            f"- {lane.agent_id}: {lane.lane} | worktree {lane.worktree} | "
            f"branch {lane.branch} | scope {lane.mp_scope}"
        )
        for lane in lanes
    ]
    context_lines = _context_escalation_lines(lanes=lanes)
    return "\n".join(
        [
            _opening_line(provider_name=provider_name, handoff_bundle=handoff_bundle),
            "",
            "Bootstrap in this exact order before acting:",
            *[
                f"- {item}"
                for item in _bootstrap_files(
                    repo_root=repo_root,
                    review_channel_path=review_channel_path,
                    bridge_path=bridge_path,
                    handoff_bundle=handoff_bundle,
                )
            ],
            "",
            "Operating contract:",
            *operating_contract_lines(
                provider_name=provider_name,
                repo_root=repo_root,
                approval_mode=approval_mode,
                rollover_threshold_pct=rollover_threshold_pct,
                promote_command=promote_command,
            ),
            f"- Planned rollover command: `{rollover_command}`",
            f"- Planned next-task promotion command: `{promote_command}`",
            (
                "- After the fresh conductor sessions launch and acknowledge the "
                "handoff bundle, exit the old session cleanly so it does not linger "
                "in memory or on the host."
            ),
            *_bridge_liveness_lines(bridge_liveness),
            *_rollover_ack_lines(
                rollover_ack_line=rollover_ack_line,
                rollover_ack_section=rollover_ack_section,
            ),
            "",
            *_worker_budget_lines(
                provider_name=provider_name,
                provider_worker_budget=provider_worker_budget,
            ),
            *context_lines,
            "",
            f"{provider_name} lane assignments:",
            *lane_lines,
            "",
            "Execution reminders:",
            (
                "- Keep `bridge.md` current-state only; do not turn it into a "
                "transcript dump."
            ),
            (
                "- Keep the active markdown bridge disciplined until the structured "
                "`review-channel` / overlay-native path replaces it."
            ),
            retirement_note,
            "",
            (
                f"Coordinate with {other_name} only through `bridge.md` plus the "
                "required operator-visible progress updates."
            ),
        ]
    )


def _opening_line(
    *,
    provider_name: str,
    handoff_bundle: dict[str, str] | None,
) -> str:
    if handoff_bundle is not None:
        return (
            f"You are the fresh {provider_name} conductor for a planned VoiceTerm "
            "markdown-bridge rollover. Resume the existing conductor role exactly."
        )
    return (
        f"You are the {provider_name} conductor for the active VoiceTerm "
        "MP-355 markdown-bridge swarm."
    )


def _bootstrap_files(
    *,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    handoff_bundle: dict[str, str] | None,
) -> list[str]:
    files: list[str] = [
        (
            "Run `python3 dev/scripts/devctl.py startup-context --format summary` first. "
            "If it exits non-zero, checkpoint or repair the repo state before coding "
            "or relaunching conductor work. Then run "
            "`python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md` "
            "for slim startup context (repo state, active plans, hotspots, key commands). "
            "Do not trust a user summary, prior chat continuity, or memory as a "
            "substitute for this Step 0 receipt. "
            "Do not echo the startup packet back into chat by default; keep any "
            "bootstrap acknowledgement to blocker state plus next step unless the "
            "operator asks for more detail. "
            "Then follow deep links when task scope requires full authority: "
            "`AGENTS.md` (SDLC policy), `dev/active/INDEX.md` (plan registry), "
            "`dev/active/MASTER_PLAN.md` (execution state). "
            "Use `--query '<term>'` for targeted subgraphs on specific files or MPs."
        ),
        display_path(review_channel_path, repo_root=repo_root),
        display_path(bridge_path, repo_root=repo_root),
    ]
    if handoff_bundle is not None:
        files.extend(
            [
                display_path(Path(handoff_bundle["markdown_path"]), repo_root=repo_root),
                display_path(Path(handoff_bundle["json_path"]), repo_root=repo_root),
            ]
        )
    return files


def _rollover_ack_details(
    *,
    provider: str,
    handoff_bundle: dict[str, str] | None,
) -> tuple[str | None, str | None]:
    if handoff_bundle is None:
        return None, None
    return (
        expected_rollover_ack_line(
            provider=provider,
            rollover_id=handoff_bundle["rollover_id"],
        ),
        expected_rollover_ack_section(provider=provider),
    )


def _bridge_liveness_lines(bridge_liveness: dict[str, object] | None) -> list[str]:
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


def _rollover_ack_lines(
    *,
    rollover_ack_line: str | None,
    rollover_ack_section: str | None,
) -> list[str]:
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


def _worker_budget_lines(
    *,
    provider_name: str,
    provider_worker_budget: int,
) -> list[str]:
    return [
        f"Worker budget target: {provider_worker_budget}",
        (
            f"If this interface supports worker/sub-agent fanout, launch up to "
            f"{provider_worker_budget} {provider_name} worker lanes matching the "
            "assignments below. If worker fanout is unavailable, stay in conductor "
            "mode and keep executing the loop yourself."
        ),
        (
            "Before worker fanout, verify each assigned lane worktree exists and "
            "is usable. If a listed worktree is missing or unavailable, do not "
            "substitute a live-repo or read-only fallback lane; skip that lane "
            "and stay conductor-only until the repo-owned worktree contract is "
            "repaired."
        ),
    ]


def _context_escalation_lines(*, lanes: list["LaneAssignment"]) -> list[str]:
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
        ("review_channel", *collect_query_terms([lane.mp_scope for lane in lanes], max_terms=3)),
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
