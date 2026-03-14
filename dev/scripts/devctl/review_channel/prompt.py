"""Prompt-building helpers for the transitional review-channel launcher."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..approval_mode import DEFAULT_APPROVAL_MODE
from ..common import display_path
from .handoff import BRIDGE_LIVENESS_KEYS, expected_rollover_ack_line, expected_rollover_ack_section
from .prompt_contract import shared_post_edit_verification_lines

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
    files: list[str] = [
        "AGENTS.md",
        "dev/active/INDEX.md",
        "dev/active/MASTER_PLAN.md",
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


def _operating_contract_lines(
    *,
    provider_name: str,
    repo_root: Path,
    approval_mode: str,
    rollover_threshold_pct: int,
    promote_command: str,
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
        *shared_post_edit_verification_lines(repo_root=repo_root),
        (
            "- Shared approval mode for this conductor session is "
            f"`{approval_mode}`. Destructive/publish-class actions still require "
            "explicit approval even when provider CLI prompts are relaxed."
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
            "- A bridge summary, `waiting_on_peer` note, or \"all green so far\" "
            "update is never terminal by itself. After every owned-section write, "
            "re-read `code_audit.md` and continue the loop instead of ending the "
            "conductor session."
        ),
        (
            "- `waiting_on_peer` means the loop stays live while you keep polling "
            "for the next bridge change; it does not mean the conductor should "
            "exit or park silently."
        ),
        (
            "- Never treat one completed slice, one proof bundle, or one peer "
            "handoff summary as permission to stop while the markdown bridge "
            "remains the active operating mode."
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
        *_provider_bootstrap_guard_lines(
            provider_name=provider_name,
            promote_command=promote_command,
        ),
    ]


def _provider_bootstrap_guard_lines(
    *,
    provider_name: str,
    promote_command: str,
) -> list[str]:
    """Return provider-specific guardrails for unattended conductor sessions."""
    if provider_name == "Codex":
        return [
            (
                "- First action after bootstrap on every fresh launch: refresh "
                "`Last Codex poll`, `Last non-audit worktree hash`, and `Poll Status` "
                "in `code_audit.md` before worker fan-out or long-running analysis."
            ),
            (
                "- Do not spawn workers, start side investigations, or wait on "
                "Claude until that refreshed `Last Codex poll` is visible in "
                "repo state. If you cannot advance the bridge heartbeat "
                "immediately, treat the launch as failed instead of pretending "
                "the reviewer loop is live."
            ),
            (
                "- Do not leave the reviewer parked on unanswered approval prompts. "
                "If a command or worker branch needs human approval, record the "
                "blocked state in `Poll Status`, skip or defer that branch, and keep "
                "the reviewer heartbeat current instead of waiting silently."
            ),
            (
                "- If Claude reports a slice complete and scoped work still remains, "
                f"run `{promote_command}` to derive the next highest-priority "
                "unchecked plan item and rewrite `Current Instruction For Claude` "
                "instead of inventing the next task by hand or ending on a summary."
            ),
        ]
    return [
        (
            "- If you are waiting on Codex review or the next instruction, stay in "
            "the conductor role, keep polling the bridge on the documented cadence, "
            "and resume as soon as `Current Instruction For Claude` changes."
        ),
        (
            "- Posting `Claude Status` or `Claude Ack` is not the end of the loop. "
            "After each coding summary, re-read the bridge, look for the next live "
            "instruction, and keep the session alive instead of exiting."
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
