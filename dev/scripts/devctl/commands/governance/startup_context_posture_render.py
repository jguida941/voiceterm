"""Posture and packet-anchor rendering for startup-context markdown."""

from __future__ import annotations


def interaction_mode(ctx_dict: dict) -> str:
    """Resolve the startup interaction mode from canonical SessionPosture."""
    posture = ctx_dict.get("session_posture")
    if isinstance(posture, dict):
        mode = str(posture.get("interaction_mode") or "").strip()
        if mode and mode != "unresolved":
            return mode
    gate = ctx_dict.get("reviewer_gate")
    if isinstance(gate, dict):
        return str(gate.get("operator_interaction_mode") or "unresolved").strip()
    return str(ctx_dict.get("interaction_mode") or "unresolved").strip()


def append_remote_control_boundaries(lines: list[str], ctx_dict: dict) -> None:
    """Render remote-control-only local action boundaries."""
    if interaction_mode(ctx_dict) != "remote_control":
        return
    lines.append("## Remote Control Boundaries")
    lines.append("- no local GUI/process intervention")
    lines.append("- no ad hoc kill commands")
    lines.append("- no local commit/push authority")
    lines.append(
        "- privileged, commit, and push work routes through typed "
        "`action_request` packets or bounded repo commands."
    )
    lines.append("")


def append_packet_intent_anchors(lines: list[str], ctx_dict: dict) -> None:
    """Render packet-derived plan anchors without implying plan authority."""
    anchors = ctx_dict.get("packet_intent_anchors")
    if not isinstance(anchors, list) or not anchors:
        return
    lines.append("## Packet Intent Anchors")
    lines.append(
        "These anchors preserve plan intent only; pending/expired packets do "
        "not become MasterPlan execution authority."
    )
    for row in anchors[:6]:
        if not isinstance(row, dict):
            continue
        packet_id = str(row.get("packet_id") or "").strip()
        lifecycle = str(row.get("lifecycle_state") or "").strip()
        target = str(row.get("target_plan") or "plan").strip()
        summary = str(row.get("summary") or "").strip()
        lines.append(f"- `{packet_id}` {lifecycle}: {target} ({summary})")
    lines.append("")


__all__ = [
    "append_packet_intent_anchors",
    "append_remote_control_boundaries",
    "interaction_mode",
]
