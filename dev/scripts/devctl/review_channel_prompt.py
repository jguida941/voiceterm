"""Prompt-building helpers for the transitional review-channel launcher."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .common import display_path
from .review_channel_handoff import (
    BRIDGE_LIVENESS_KEYS,
    expected_rollover_ack_line,
    expected_rollover_ack_section,
)

if TYPE_CHECKING:
    from .review_channel import LaneAssignment


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
    bridge_liveness: dict[str, object] | None = None,
    handoff_bundle: dict[str, str] | None = None,
) -> str:
    """Render the initial conductor prompt for Codex or Claude."""
    provider_worker_budget = codex_workers if provider == "codex" else claude_workers
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
            *_operating_contract_lines(
                provider_name=provider_name,
                rollover_threshold_pct=rollover_threshold_pct,
            ),
            f"- Planned rollover command: `{rollover_command}`",
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
            "",
            f"{provider_name} lane assignments:",
            *lane_lines,
            "",
            "Execution reminders:",
            (
                "- Keep `code_audit.md` current-state only; do not turn it into a "
                "transcript dump."
            ),
            (
                "- Keep the active markdown bridge disciplined until the structured "
                "`review-channel` / overlay-native path replaces it."
            ),
            retirement_note,
            "",
            (
                f"Coordinate with {other_name} only through `code_audit.md` plus the "
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
    files: list[str] = []
    if handoff_bundle is not None:
        files.extend(
            [
                display_path(Path(handoff_bundle["markdown_path"]), repo_root=repo_root),
                display_path(Path(handoff_bundle["json_path"]), repo_root=repo_root),
            ]
        )
    files.extend(
        [
            "AGENTS.md",
            "dev/active/INDEX.md",
            "dev/active/MASTER_PLAN.md",
            display_path(review_channel_path, repo_root=repo_root),
            display_path(bridge_path, repo_root=repo_root),
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


def _operating_contract_lines(
    *,
    provider_name: str,
    rollover_threshold_pct: int,
) -> list[str]:
    owned_sections = (
        "`Poll Status`, `Current Verdict`, `Open Findings`, "
        "`Current Instruction For Claude`"
        if provider_name == "Codex"
        else "`Claude Status`, `Claude Questions`, `Claude Ack`"
    )
    return [
        "- `dev/active/review_channel.md` is the static swarm plan.",
        "- `code_audit.md` is the only live cross-team coordination surface.",
        (
            "- Do not rely on automatic context compaction or recovery summaries "
            "to preserve the conductor role. Relaunch before compaction instead."
        ),
        (
            "- Treat this as a tooling/process/CI lane and follow repo policy through "
            "`AGENTS.md`, `dev/scripts/README.md`, and `dev/guides/DEVCTL_AUTOGUIDE.md`."
        ),
        (
            "- Use the repo-owned `devctl`/check scripts instead of ad-hoc shell "
            "work whenever policy already defines the command path."
        ),
        f"- Only the {provider_name} conductor updates {owned_sections} in `code_audit.md`.",
        (
            f"- Specialist {provider_name} workers must report back to the "
            f"{provider_name} conductor instead of editing `code_audit.md` directly."
        ),
        (
            "- Read the active queue from `code_audit.md`, keep the 8+8 swarm "
            "moving, and continue until the scoped plan work is exhausted or a "
            "real blocker/approval boundary is hit."
        ),
        (
            "- Ask the human only for destructive actions, credentials/auth, "
            "push/publish approval, or required manual validation."
        ),
        (
            "- Before merge/handoff, satisfy the tooling lane governance path: "
            "`docs-check --strict-tooling`, `check_review_channel_bridge.py`, "
            "`check_active_plan_sync.py`, `check_multi_agent_sync.py`, and the "
            "rest of the required `bundle.tooling` surfaces in `AGENTS.md`."
        ),
        (
            f"- When the interface shows {rollover_threshold_pct}% context remaining "
            "or lower, finish the current atomic step, update your owned bridge "
            "state, and trigger a planned rollover before compaction."
        ),
    ]


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
            f"ACK line into `{rollover_ack_section}` in `code_audit.md`: "
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
    ]
