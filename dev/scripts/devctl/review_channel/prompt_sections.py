"""Shared prompt section builders for review-channel conductor prompts."""

from __future__ import annotations

from pathlib import Path

from ..runtime.role_profile import role_for_provider
from .prompt_guards import provider_bootstrap_guard_lines
from .prompt_contract import shared_post_edit_verification_lines


def operating_contract_lines(
    *,
    provider_name: str,
    repo_root: Path,
    approval_mode: str,
    rollover_threshold_pct: int,
    promote_command: str,
) -> list[str]:
    """Return the shared operating-contract lines for one conductor prompt."""
    owned_sections = (
        "`Poll Status`, `Current Verdict`, `Open Findings`, "
        "`Current Instruction For Claude`"
        if role_for_provider(provider_name) == "reviewer"
        else "`Claude Status`, `Claude Questions`, `Claude Ack`"
    )
    return [
        "- `dev/active/review_channel.md` is the static swarm plan.",
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
        *shared_post_edit_verification_lines(repo_root=repo_root),
        (
            "- Shared approval mode for this conductor session is "
            f"`{approval_mode}`. Destructive/publish-class actions still require "
            "explicit approval even when provider CLI prompts are relaxed."
        ),
        f"- Only the {provider_name} conductor updates {owned_sections} in `bridge.md`.",
        (
            f"- Specialist {provider_name} workers must report back to the "
            f"{provider_name} conductor instead of editing `bridge.md` directly."
        ),
        (
            "- Treat scratch/reference artifacts such as `convo.md` and "
            "`dev/audits/**` as advisory context unless the live instruction "
            "explicitly scopes them. Do not let them redefine the active lane "
            "or `Last Reviewed Scope` by default."
        ),
        (
            "- Read the active queue from `bridge.md`, keep the 8+8 swarm "
            "moving, and continue until the scoped plan work is exhausted or a "
            "real blocker/approval boundary is hit."
        ),
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
        *provider_bootstrap_guard_lines(provider_name=provider_name, promote_command=promote_command),
    ]
