"""Provider-specific guard lines for review-channel conductor prompts."""

from __future__ import annotations

from ..runtime.role_profile import role_for_provider


def provider_bootstrap_guard_lines(
    *,
    provider_name: str,
    promote_command: str,
) -> list[str]:
    """Return role-driven guardrails for unattended conductor sessions."""
    if role_for_provider(provider_name) == "reviewer":
        return [
            (
                "- First action after bootstrap on every fresh launch: refresh "
                "`Last Codex poll`, `Last non-audit worktree hash`, and `Poll Status` "
                "in `bridge.md` before worker fan-out or long-running analysis."
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
                "- If you are waiting on Claude-owned progress, ACK changes, or a "
                "fresh diff to review, use the repo-owned `review-channel --action "
                "reviewer-wait` path instead of ad-hoc shell sleep loops, and "
                "resume the review pass as soon as implementer-owned state changes."
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
            "- `bridge.md` is the first thing to re-read whenever you need "
            "to know what to do next in dual-agent mode. Do not wait for the "
            "operator to restate the reviewer process in chat."
        ),
        (
            "- If reviewer-owned bridge state says `hold steady`, `waiting for "
            "reviewer promotion`, `Codex committing/pushing`, or equivalent "
            "wait language, that is a hard polling state. Do not scan plan docs "
            "for side work or reopen an accepted tranche until the reviewer-owned "
            "instruction changes."
        ),
        (
            "- If you are waiting on Codex review or the next instruction, stay in "
            "the conductor role, use the repo-owned `review-channel --action "
            "implementer-wait` path instead of ad-hoc shell sleep loops, and "
            "resume as soon as reviewer-owned bridge state or a fresh Claude-"
            "targeted review packet changes."
        ),
        (
            "- On each repoll, read `Last Codex poll` / `Poll Status` first, then "
            "re-read `Current Verdict`, `Open Findings`, and `Current Instruction "
            "For Claude` together. On the same cadence, also poll the Claude-"
            "targeted packet inbox/watch surface (`review-channel --action inbox "
            "--target claude --status pending --format json` or equivalent) so "
            "reviewer packets cannot be missed. If those reviewer-owned sections "
            "and the pending Claude-targeted packet set are unchanged after you "
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
        (
            "- If `Current Instruction For Claude` still contains active work and "
            "the reviewer has not written an explicit wait state, do not say "
            "\"instruction unchanged\", \"done from my side\", or \"Codex should "
            "review\" and park. Keep executing the current bounded slice or post a "
            "concrete blocker in `Claude Questions`."
        ),
        (
            "- Posting `Claude Status` or `Claude Ack` is not the end of the loop. "
            "After each coding summary, re-read the bridge, poll fresh Claude-"
            "targeted review packets, look for the next live instruction, and "
            "keep the session alive instead of exiting."
        ),
        (
            "- A completed slice, green proof bundle, or accepted reviewer note is "
            "not permission to self-promote the next task. Only reviewer-owned "
            "`Current Instruction For Claude` may start a new slice."
        ),
    ]
