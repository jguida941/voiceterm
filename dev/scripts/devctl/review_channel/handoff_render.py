"""Markdown rendering helpers for review-channel handoff bundles."""

from __future__ import annotations

from .handoff_constants import BRIDGE_LIVENESS_KEYS, ROLLOVER_ACK_PREFIX


def render_handoff_markdown(
    payload: dict[str, object],
    *,
    expected_rollover_ack_line,
) -> str:
    """Render one handoff payload into markdown."""
    lines = ["# Review Channel Handoff", ""]
    lines.append(f"- generated_at: {payload['generated_at']}")
    lines.append(f"- rollover_id: {payload['rollover_id']}")
    lines.append(f"- trigger: {payload['trigger']}")
    lines.append(f"- threshold_pct: {payload['threshold_pct']}")
    lines.append(f"- bridge_path: {payload['bridge_path']}")
    lines.append(f"- review_channel_path: {payload['review_channel_path']}")
    rollover_id = str(payload["rollover_id"])
    for provider in ROLLOVER_ACK_PREFIX:
        lines.append(
            f"- required_{provider}_ack: "
            f"{expected_rollover_ack_line(provider=provider, rollover_id=rollover_id)}"
        )

    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and metadata:
        lines.append("")
        lines.append("## Metadata")
        for key, value in metadata.items():
            lines.append(f"- {key}: {value}")

    liveness = payload.get("liveness")
    if isinstance(liveness, dict) and liveness:
        lines.append("")
        lines.append("## Liveness")
        for key in BRIDGE_LIVENESS_KEYS:
            lines.append(f"- {key}: {liveness.get(key)}")

    resume_state = payload.get("resume_state")
    if isinstance(resume_state, dict) and resume_state:
        lines.append("")
        lines.append("## Resume State")
        lines.append(f"- next_action: {resume_state.get('next_action') or 'n/a'}")
        lines.append(
            "- reviewed_worktree_hash: "
            f"{resume_state.get('reviewed_worktree_hash') or 'n/a'}"
        )
        lines.append(
            "- current_atomic_step: "
            f"{resume_state.get('current_atomic_step') or 'n/a'}"
        )

        current_blockers = resume_state.get("current_blockers")
        if isinstance(current_blockers, list):
            lines.append("")
            lines.append("### Current Blockers")
            if current_blockers:
                for blocker in current_blockers:
                    lines.append(f"- {blocker}")
            else:
                lines.append("- (none)")

        owned_lanes = resume_state.get("owned_lanes")
        if isinstance(owned_lanes, dict):
            lines.append("")
            lines.append("### Owned Lanes")
            for provider in ROLLOVER_ACK_PREFIX:
                provider_lanes = owned_lanes.get(provider, [])
                lines.append(f"- {provider}:")
                if isinstance(provider_lanes, list) and provider_lanes:
                    for lane in provider_lanes:
                        if not isinstance(lane, dict):
                            continue
                        lines.append(
                            "  - "
                            f"{lane.get('agent_id')} | {lane.get('lane')} | "
                            f"{lane.get('worktree')} | {lane.get('branch')} | "
                            f"{lane.get('mp_scope')}"
                        )
                else:
                    lines.append("  - (none)")

        launch_ack_state = resume_state.get("launch_ack_state")
        if isinstance(launch_ack_state, dict):
            lines.append("")
            lines.append("### Launch ACK State")
            for provider in ROLLOVER_ACK_PREFIX:
                ack_state = launch_ack_state.get(provider, {})
                if not isinstance(ack_state, dict):
                    continue
                status = "observed" if ack_state.get("observed") else "pending"
                lines.append(
                    f"- {provider}: {status} | {ack_state.get('required_section')} | "
                    f"{ack_state.get('required_line')}"
                )

    sections = payload.get("sections")
    if isinstance(sections, dict) and sections:
        for name, value in sections.items():
            lines.append("")
            lines.append(f"## {name}")
            lines.append(str(value).strip() or "(empty)")

    return "\n".join(lines)
