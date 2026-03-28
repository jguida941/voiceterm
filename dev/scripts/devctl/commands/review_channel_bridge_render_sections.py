"""Section-rendering helpers extracted from review_channel_bridge_render."""

from __future__ import annotations


def _append_handoff_bundle(lines: list[str], handoff_bundle: object) -> None:
    if not isinstance(handoff_bundle, dict):
        return
    lines.append("")
    lines.append("## Handoff Bundle")
    lines.append(f"- bundle_dir: {handoff_bundle['bundle_dir']}")
    lines.append(f"- markdown_path: {handoff_bundle['markdown_path']}")
    lines.append(f"- json_path: {handoff_bundle['json_path']}")
    lines.append(f"- generated_at: {handoff_bundle['generated_at']}")
    lines.append(f"- rollover_id: {handoff_bundle['rollover_id']}")
    lines.append(f"- trigger: {handoff_bundle['trigger']}")
    lines.append(f"- threshold_pct: {handoff_bundle['threshold_pct']}")


def _append_promotion(lines: list[str], promotion: object) -> None:
    if not isinstance(promotion, dict):
        return
    lines.append("")
    lines.append("## Promotion")
    lines.append(f"- instruction: {promotion.get('instruction')}")
    lines.append(f"- source_path: {promotion.get('source_path')}")
    if promotion.get("phase_heading"):
        lines.append(f"- phase_heading: {promotion.get('phase_heading')}")
    lines.append(f"- checklist_item: {promotion.get('checklist_item')}")


def _append_attention(lines: list[str], attention: object) -> None:
    if not isinstance(attention, dict):
        return
    lines.append("")
    lines.append("## Attention")
    lines.append(f"- status: {attention.get('status')}")
    lines.append(f"- owner: {attention.get('owner')}")
    lines.append(f"- summary: {attention.get('summary')}")
    lines.append(
        f"- recommended_action: {attention.get('recommended_action') or 'n/a'}"
    )
    lines.append(
        f"- recommended_command: {attention.get('recommended_command') or 'n/a'}"
    )


def _append_service_identity(lines: list[str], service_identity: object) -> None:
    if not isinstance(service_identity, dict):
        return
    lines.append("")
    lines.append("## Service Identity")
    lines.append(f"- service_id: {service_identity.get('service_id') or 'n/a'}")
    lines.append(f"- project_id: {service_identity.get('project_id') or 'n/a'}")
    lines.append(f"- repo_root: {service_identity.get('repo_root') or 'n/a'}")
    lines.append(f"- worktree_root: {service_identity.get('worktree_root') or 'n/a'}")
    lines.append(f"- bridge_path: {service_identity.get('bridge_path') or 'n/a'}")
    lines.append(
        "- review_channel_path: "
        f"{service_identity.get('review_channel_path') or 'n/a'}"
    )
    lines.append(f"- status_root: {service_identity.get('status_root') or 'n/a'}")


def _append_bridge_heartbeat_refresh(lines: list[str], refresh: object) -> None:
    if not isinstance(refresh, dict):
        return
    lines.append("")
    lines.append("## Bridge Heartbeat Refresh")
    lines.append(f"- bridge_path: {refresh.get('bridge_path')}")
    lines.append(f"- reason: {refresh.get('reason')}")
    lines.append(f"- last_codex_poll_utc: {refresh.get('last_codex_poll_utc')}")
    lines.append(f"- last_codex_poll_local: {refresh.get('last_codex_poll_local')}")
    lines.append(f"- last_worktree_hash: {refresh.get('last_worktree_hash')}")


def _append_reviewer_state_write(lines: list[str], write: object) -> None:
    if not isinstance(write, dict):
        return
    lines.append("")
    lines.append("## Reviewer State Write")
    lines.append(f"- bridge_path: {write.get('bridge_path')}")
    lines.append(f"- action: {write.get('action')}")
    lines.append(f"- reviewer_mode: {write.get('reviewer_mode')}")
    lines.append(f"- reason: {write.get('reason')}")
    lines.append(f"- last_codex_poll_utc: {write.get('last_codex_poll_utc')}")
    lines.append(f"- last_codex_poll_local: {write.get('last_codex_poll_local')}")
    lines.append(f"- last_worktree_hash: {write.get('last_worktree_hash')}")


def _append_bridge_render(lines: list[str], bridge_render: object) -> None:
    if not isinstance(bridge_render, dict):
        return
    lines.append("")
    lines.append("## Bridge Render")
    lines.append(f"- lines_before: {bridge_render.get('lines_before')}")
    lines.append(f"- lines_after: {bridge_render.get('lines_after')}")
    lines.append(f"- bytes_before: {bridge_render.get('bytes_before')}")
    lines.append(f"- bytes_after: {bridge_render.get('bytes_after')}")
    dropped = bridge_render.get("dropped_headings") or []
    lines.append(
        "- dropped_headings: "
        + (", ".join(str(item) for item in dropped) if dropped else "none")
    )
    sanitized = bridge_render.get("sanitized_sections") or []
    lines.append(
        "- sanitized_sections: "
        + (", ".join(str(item) for item in sanitized) if sanitized else "none")
    )


def _append_sessions(lines: list[str], sessions: object) -> None:
    if not isinstance(sessions, list) or not sessions:
        return
    lines.append("")
    lines.append("## Sessions")
    for session in sessions:
        lines.append(f"### {session['session_name']}")
        lines.append(f"- provider: {session['provider']}")
        lines.append(f"- worker_budget: {session['worker_budget']}")
        lines.append(f"- lane_count: {session['lane_count']}")
        lines.append(f"- script_path: {session['script_path']}")
        lines.append(f"- launch_command: {session['launch_command']}")
        for lane in session["lanes"]:
            lines.append(
                f"- lane: {lane['agent_id']} | {lane['lane']} | "
                f"{lane['worktree']} | {lane['branch']}"
            )
