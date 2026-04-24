"""Shared section renderers for review-channel conductor prompts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..runtime.review_state_models import ConductorCapabilityState
from .prompt_contract import shared_post_edit_verification_lines
from .prompt_guards import provider_bootstrap_guard_lines


@dataclass(frozen=True, slots=True)
class OperatingContractInput:
    """Inputs required to render the shared operating contract block."""

    capability: ConductorCapabilityState
    provider_id: str
    provider_name: str
    counterpart_provider_id: str
    counterpart_provider_name: str
    repo_root: Path
    approval_mode: str
    rollover_threshold_pct: int
    promote_command: str


def operating_contract_lines(contract: OperatingContractInput) -> list[str]:
    """Return the shared operating-contract lines for one conductor prompt."""
    capability = contract.capability
    owned_sections = (
        "the reviewer-owned sections `Poll Status`, `Current Verdict`, "
        "`Open Findings`, `Current Instruction For Claude`, plus the "
        "reviewer-heartbeat compatibility field `Last Codex poll`"
        if capability.role == "reviewer"
        else "the implementer-owned compatibility sections `Claude Status`, "
        "`Claude Questions`, `Claude Ack`"
    )
    queue_progress_line = (
        "- Read the active queue from `bridge.md`, keep the review loop live, "
        "and continue reviewing, promoting, or waiting until the scoped plan work "
        "is exhausted or a real blocker/approval boundary is hit. In "
        "`active_dual_agent`, do not start local implementation unless the repo-"
        "owned workflow explicitly enters takeover (`reviewer_mode=single_agent` "
        f"or `{capability.takeover_command}`)."
        if capability.queue_policy == "review_only"
        else "- Read the active queue from `bridge.md`, keep the conductor loop "
        "moving, and continue until the scoped plan work is exhausted or a real "
        "blocker/approval boundary is hit."
    )
    return [
        "- `dev/active/review_channel.md` is the static review plan and planned lane table.",
        "- `bridge.md` is the only live cross-team coordination surface.",
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
        *shared_post_edit_verification_lines(repo_root=contract.repo_root),
        (
            "- Shared approval mode for this conductor session is "
            f"`{contract.approval_mode}`. Destructive/publish-class actions still require "
            "explicit approval even when provider CLI prompts are relaxed."
        ),
        (
            f"- Only the {contract.provider_name} conductor updates {owned_sections} "
            "in `bridge.md`."
        ),
        (
            f"- Specialist {contract.provider_name} workers must report back to the "
            f"{contract.provider_name} conductor instead of editing `bridge.md` directly."
        ),
        (
            "- Treat scratch/reference artifacts such as `convo.md` and "
            "`dev/audits/**` as advisory context unless the live instruction "
            "explicitly scopes them. Do not let them redefine the active lane "
            "or `Last Reviewed Scope` by default."
        ),
        queue_progress_line,
        (
            "- If a context packet or downstream packet carries `## Probe "
            "Guidance`, treat it as the default repair/delegation plan unless "
            "you can record a concrete waiver reason."
        ),
        (
            "- A bridge summary, `waiting_on_peer` note, or \"all green so far\" "
            "update is never terminal by itself. After every owned-section write, "
            "re-read `bridge.md` and continue the loop instead of ending the "
            "conductor session."
        ),
        (
            f"- On each repoll, also poll the {contract.provider_name}-targeted packet "
            f"inbox/watch surface (`review-channel --action inbox --target {contract.provider_id} "
            f"--actor {contract.provider_id} --status pending --format json` or "
            "equivalent) so reviewer packets cannot be missed behind bridge-only "
            "polling. The `--actor` must match the target so the runtime stamps "
            "`delivery_observed_at_utc`; otherwise packets stay `unseen`."
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
            f"- When the interface shows {contract.rollover_threshold_pct}% context remaining "
            "or lower, finish the current atomic step, update your owned bridge "
            "state, and trigger a planned rollover before compaction."
        ),
        *provider_bootstrap_guard_lines(
            capability=capability,
            provider_name=contract.provider_name,
            provider_id=contract.provider_id,
            counterpart_provider_name=contract.counterpart_provider_name,
            counterpart_provider_id=contract.counterpart_provider_id,
            promote_command=contract.promote_command,
        ),
    ]


def worker_budget_lines(
    *,
    capability: ConductorCapabilityState,
    provider_name: str,
    planned_lane_count: int,
    provider_worker_budget: int,
) -> list[str]:
    """Render worker-fanout instructions for one provider."""
    worker_fallback = (
        "If worker fanout is unavailable, stay in reviewer-only conductor "
        "mode, keep the review loop alive yourself, and do not start local "
        "implementation unless the workflow explicitly switches to takeover "
        "(`reviewer_mode=single_agent` or "
        f"`{capability.takeover_command}`)."
        if capability.worker_unavailable_policy == "stay_reviewer_only"
        else "If worker fanout is unavailable, stay in conductor mode and keep "
        "executing the loop yourself."
    )
    missing_lane_fallback = (
        "Before worker fanout, verify each assigned lane worktree exists and "
        "is usable. If a listed worktree is missing or unavailable, do not "
        "substitute a live-repo or read-only fallback lane; skip that lane, stay "
        "reviewer-only, and use repo-owned review/promote/wait paths until the "
        "repo-owned worktree contract is repaired."
        if capability.worker_unavailable_policy == "stay_reviewer_only"
        else "Before worker fanout, verify each assigned lane worktree exists and "
        "is usable. If a listed worktree is missing or unavailable, do not "
        "substitute a live-repo or read-only fallback lane; skip that lane "
        "and stay conductor-only until the repo-owned worktree contract is "
        "repaired."
    )
    lines = [
        f"Static planned lane count: {planned_lane_count}",
        f"Requested worker fanout budget: {provider_worker_budget}",
    ]
    if provider_worker_budget > 0:
        lines.append(
            "If this interface supports worker/sub-agent fanout, you may launch "
            f"up to {provider_worker_budget} additional {provider_name} worker "
            "lanes from the planned assignments below. Treat those assignments "
            "as planned scope, not proof that repo-owned worker sessions "
            f"already exist. {worker_fallback}"
        )
    else:
        lines.append(
            "No additional worker fanout is requested by default. Treat the "
            "assignments below as planned lane scope and stay conductor-owned "
            "unless an explicit runtime capability or later typed packet says "
            f"otherwise. {worker_fallback}"
        )
    lines.append(missing_lane_fallback)
    return lines
