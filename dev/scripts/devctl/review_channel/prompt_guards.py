"""Role-driven, provider-aware guard lines for review-channel conductor prompts."""

from __future__ import annotations

from .ack_contract import ack_contract_prompt_line
from ..runtime.review_state_models import ConductorCapabilityState


def startup_context_follow_up(capability: ConductorCapabilityState) -> str:
    """Return the bootstrap guidance that follows startup-context."""
    if capability.role == "reviewer":
        return (
            "If it exits non-zero, read the summary fields before widening scope. "
            "`action=continue_editing` with `reason=review_pending` and "
            "`action=await_review` with `reason=review_pending_before_push` are "
            "normal reviewer-bootstrap receipts while the collaboration lane is "
            "still live; continue bootstrap, poll `python3 dev/scripts/devctl.py "
            "review-channel --action status --terminal none --format json`, and "
            "refresh the reviewer-owned bridge heartbeat before attempting repair. "
            "Treat only `action=repair_reviewer_loop`, checkpoint/budget blockers, "
            "or typed review-channel status showing stale/non-live reviewer runtime "
            "as a repair or relaunch boundary."
        )
    return (
        "If it exits non-zero, checkpoint or repair the repo state before coding "
        "or relaunching conductor work."
    )


def reviewer_takeover_note(capability: ConductorCapabilityState) -> str:
    """Return the reviewer takeover warning when dual-agent mode is active."""
    return (
        "Reviewer startup is fail-closed in `active_dual_agent`; do not add "
        "`--reviewer-override` unless you are intentionally taking implementation "
        "ownership."
        if capability.requires_explicit_takeover
        else ""
    )


def provider_bootstrap_guard_lines(
    *,
    capability: ConductorCapabilityState,
    provider_name: str,
    provider_id: str,
    counterpart_provider_name: str,
    counterpart_provider_id: str,
    promote_command: str,
) -> list[str]:
    """Return role-driven guardrails for unattended conductor sessions."""
    if capability.role == "reviewer":
        return _reviewer_guard_lines(
            capability=capability,
            counterpart_provider_name=counterpart_provider_name,
            counterpart_provider_id=counterpart_provider_id,
            provider_name=provider_name,
            promote_command=promote_command,
        )
    return _implementer_guard_lines(
        provider_id=provider_id,
        provider_name=provider_name,
        counterpart_provider_name=counterpart_provider_name,
    )


def _reviewer_guard_lines(
    *,
    capability: ConductorCapabilityState,
    counterpart_provider_name: str,
    counterpart_provider_id: str,
    provider_name: str,
    promote_command: str,
) -> list[str]:
    reviewer_poll_note = (
        ""
        if provider_name == "Codex"
        else (
            " `Last Codex poll` remains the reviewer-heartbeat compatibility "
            "field even when the reviewer provider is not Codex."
        )
    )
    return [
        (
            "- A non-zero reviewer startup receipt is not automatically a loop-"
            "repair signal. `action=continue_editing` with `reason=review_pending` "
            "and `action=await_review` with `reason=review_pending_before_push` "
            "still mean the reviewer owns the next live turn; continue bootstrap, "
            "poll `review-channel --action status`, and refresh `bridge.md` before "
            "escalating into relaunch/repair."
        ),
        (
            "- First action after bootstrap on every fresh launch: refresh "
            "`Last Codex poll`, `Last non-audit worktree hash`, and `Poll Status` "
            f"in `bridge.md` before worker fan-out or long-running analysis.{reviewer_poll_note}"
        ),
        (
            "- Do not spawn workers, start side investigations, or wait on "
            f"{counterpart_provider_name} until that refreshed `Last Codex poll` is visible in "
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
            "- When an interactive permission prompt blocks progress (commit, "
            "push, process kill, or dialog dismissal) and the operator is not "
            "available in the terminal, post a typed action request via "
            "`review-channel --action post` with "
            "`PacketPostRequest(kind=\"action_request\")`. "
            "Supported actions: `commit`, `run_check`, `push`, `kill_process`. "
            "Do not write to the `## Action Requests` bridge section directly; "
            "it is a projection-only surface rendered from packet state. "
            f"{counterpart_provider_name} will execute pending requests on the next packet poll."
        ),
        (
            f"- If you are waiting on {counterpart_provider_name}-owned progress, ACK changes, or a "
            "fresh diff to review, use the repo-owned `review-channel --action "
            "reviewer-wait` path instead of ad-hoc shell sleep loops, and "
            "resume the review pass as soon as implementer-owned state changes."
        ),
        (
            f"- `review-channel --action reviewer-wait` now includes the "
            f"{counterpart_provider_name}-targeted pending-packet wake path, so "
            "reviewer-side wait does not depend on a separately started packet "
            "watcher. Use the standalone watch/inbox surface only for observer "
            "dashboards or explicit queue inspection."
        ),
        (
            "- In `active_dual_agent`, reviewer mode is review-only by default. "
            "Missing worker worktrees, absent fanout, or a promising fix are "
            "not permission to code locally. Use the repo-owned "
            "review/promote/wait paths unless the workflow explicitly switches "
            "to takeover with `reviewer_mode=single_agent` or "
            f"`{capability.takeover_command}`."
        ),
        (
            f"- If {counterpart_provider_name} reports a slice complete and scoped work still remains, "
            f"run `{promote_command}` to derive the next highest-priority "
            "unchecked plan item and rewrite `Current Instruction For Claude` "
            "instead of inventing the next task by hand or ending on a summary."
        ),
    ]


def _implementer_guard_lines(
    *,
    provider_id: str,
    provider_name: str,
    counterpart_provider_name: str,
) -> list[str]:
    return [
        (
            "- `bridge.md` is the first thing to re-read whenever you need "
            "to know what to do next in dual-agent mode. Do not wait for the "
            "operator to restate the reviewer process in chat."
        ),
        (
            "- On each bridge repoll, also poll the packet inbox for pending "
            f"`action_request` packets via `review-channel --action inbox "
            f"--target {provider_id} --status pending --format json`. When {counterpart_provider_name} is "
            "blocked on an interactive permission prompt (commit, push, "
            "dialog dismissal), it posts a typed action request via "
            "`PacketPostRequest(kind=\"action_request\")` instead of waiting. "
            "Execute pending requests in order, then transition each packet "
            "to `completed` or `failed` via the packet transport. Do not "
            "read or write the `## Action Requests` bridge section directly; "
            "it is a projection-only surface."
        ),
        (
            "- Before you summarize state for the operator or ask a question "
            "based on rollover/handoff context, re-read the live reviewer-"
            "owned bridge sections and discard stale bundle conclusions. A "
            "handoff packet is restart context, not live authority."
        ),
        (
            "- If reviewer-owned bridge state says `hold steady`, `waiting for "
            f"reviewer promotion`, `{counterpart_provider_name} committing/pushing`, or equivalent "
            "wait language, that is a hard polling state. Do not scan plan docs "
            "for side work or reopen an accepted tranche until the reviewer-owned "
            "instruction changes."
        ),
        (
            f"- If a stale handoff summary says {counterpart_provider_name} is offline but the current "
            "bridge shows a newer reviewer checkpoint or fresh `Last Codex poll`, "
            "discard the stale summary and follow the live reviewer-owned bridge "
            "state."
        ),
        (
            f"- If you are waiting on {counterpart_provider_name} review or the next instruction, stay in "
            "the conductor role, use the repo-owned `review-channel --action "
            "implementer-wait` path instead of ad-hoc shell sleep loops, and "
            f"resume as soon as reviewer-owned bridge state or a fresh {provider_name}-"
            "targeted review packet changes."
        ),
        (
            "- If the reviewer still owns the next turn (`hold steady`, push in "
            "progress, promotion pending, or equivalent wait state), do not ask "
            "the operator to choose between polling, push, or side work. Keep "
            "polling repo-owned state until the reviewer-owned instruction or "
            "packet set changes."
        ),
        (
            "- If the live bridge says `hold steady` or the only missing state is "
            "`Claude Status` / `Claude Ack`, do not ask the operator what to do "
            "next. Rewrite your owned bridge sections, acknowledge the current "
            "instruction revision, then use the repo-owned wait path and keep "
            "polling."
        ),
        (
            "- On each repoll, read `Last Codex poll` / `Poll Status` first, then "
            "re-read `Current Verdict`, `Open Findings`, and `Current Instruction "
            "For Claude` together. On the same cadence, also poll the "
            f"{provider_name}-targeted packet inbox/watch surface (`review-channel --action inbox "
            f"--target {provider_id} --status pending --format json` or equivalent) so "
            "reviewer packets cannot be missed. If those reviewer-owned sections "
            f"and the pending {provider_name}-targeted packet set are unchanged after you "
            "already finished the current bounded work, that is a live wait "
            "state; do not hammer one fixed offset or one cached line range."
        ),
        (
            "- If you use `review-channel --action bridge-poll`, treat "
            "`next_turn_role`, `next_turn_reason`, and `turn_state_token` as the "
            "authority for whose turn it is and what exact reviewer-owned state "
            "you observed. `changed_since_last_ack` only tells you whether the "
            "instruction revision changed; it does not tell you whether the "
            "reviewer owns the next turn on a changed tree."
        ),
        ack_contract_prompt_line(),
        (
            "- If `Current Instruction For Claude` still contains active work and "
            "the reviewer has not written an explicit wait state, do not say "
            "\"instruction unchanged\", \"done from my side\", \"No change. "
            f"Continuing.\", or \"{counterpart_provider_name} should review\" and park. Keep executing "
            "the current bounded slice or post a concrete blocker in `Claude "
            "Questions`."
        ),
        (
            "- While active work is still assigned, every `Claude Status` / "
            "`Claude Ack` update must name concrete files, subsystems, findings, "
            "or one concrete blocker/question. Low-information polling/completion "
            "notes are contract violations, not acceptable progress reports."
        ),
        (
            "- Do not use raw shell idling such as `sleep 60` or "
            "`bash -lc 'sleep 60'` to emulate waiting. Use the repo-owned "
            "`review-channel --action implementer-wait` path only when the "
            "reviewer-owned bridge state is explicitly in a wait posture."
        ),
        (
            "- Posting `Claude Status` or `Claude Ack` is not the end of the loop. "
            f"After each coding summary, re-read the bridge, poll fresh {provider_name}-"
            "targeted review packets, look for the next live instruction, and "
            "keep the session alive instead of exiting."
        ),
        (
            "- A completed slice, green proof bundle, or accepted reviewer note is "
            "not permission to self-promote the next task. Only reviewer-owned "
            "`Current Instruction For Claude` may start a new slice."
        ),
    ]
