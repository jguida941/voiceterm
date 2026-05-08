"""Summary reducers for ``SessionOrientationPacket`` payloads."""

from __future__ import annotations

from .session_orientation_models import SessionOrientationStep, mapping, text


def summary_items(*items: tuple[str, object]) -> dict[str, object]:
    """Build an ordered JSON-ready summary without large schema literals."""
    return {key: value for key, value in items}


def startup_summary(payload: dict[str, object]) -> dict[str, object]:
    """Reduce StartupContext to the fields used by fresh-session routing."""
    authority = mapping(payload.get("authority_snapshot"))
    startup_authority = mapping(payload.get("startup_authority"))
    push_decision = mapping(payload.get("push_decision"))
    work_intake = mapping(payload.get("work_intake"))
    return summary_items(
        (
            "advisory_action",
            text(payload.get("advisory_action") or payload.get("action")),
        ),
        (
            "advisory_reason",
            text(payload.get("advisory_reason") or payload.get("reason")),
        ),
        (
            "implementation_permission",
            text(
                authority.get("implementation_permission")
                or payload.get("implementation_permission")
            ),
        ),
        (
            "observed_control_topology",
            text(
                authority.get("observed_control_topology")
                or payload.get("observed_control_topology")
            ),
        ),
        ("push_decision", push_decision_summary(push_decision)),
        ("startup_authority", startup_authority_summary(startup_authority)),
        ("work_intake", work_intake_summary(work_intake)),
    )


def push_decision_summary(push_decision: dict[str, object]) -> dict[str, object]:
    """Reduce push-decision routing fields."""
    return {
        "action": text(push_decision.get("action")),
        "reason": text(push_decision.get("reason")),
        "next_step_command": text(push_decision.get("next_step_command")),
    }


def startup_authority_summary(
    startup_authority: dict[str, object],
) -> dict[str, object]:
    """Reduce startup-authority result fields."""
    return {
        "ok": startup_authority.get("ok"),
        "checks_run": startup_authority.get("checks_run"),
        "error_count": startup_authority.get("error_count"),
    }


def work_intake_summary(work_intake: dict[str, object]) -> dict[str, object]:
    """Reduce work-intake routing fields."""
    return {
        "active_target": mapping(work_intake.get("active_target")),
        "plan_routing": mapping(work_intake.get("plan_routing")),
    }


def session_resume_summary(payload: dict[str, object]) -> dict[str, object]:
    """Reduce SessionCachePacket fields for the orientation packet."""
    authority = mapping(payload.get("authority_snapshot"))
    packet_inbox = mapping(payload.get("packet_inbox"))
    return summary_items(
        ("blockers", text(payload.get("blockers"))),
        (
            "interaction_mode",
            text(
                payload.get("operator_interaction_mode")
                or payload.get("interaction_mode")
            ),
        ),
        ("resolved_phase", text(payload.get("resolved_phase"))),
        ("attention_status", text(payload.get("attention_status"))),
        ("current_instruction", text(payload.get("current_instruction"))),
        (
            "instruction_revision",
            text(
                payload.get("instruction_revision")
                or payload.get("current_instruction_revision")
            ),
        ),
        ("ack_state", text(payload.get("ack_state"))),
        ("next_guard_bundle", text(payload.get("next_guard_bundle"))),
        ("review_candidate", payload.get("review_candidate")),
        ("authority_snapshot", authority_reduced(authority)),
        ("packet_inbox", packet_inbox_summary(packet_inbox)),
    )


def review_status_summary(payload: dict[str, object]) -> dict[str, object]:
    """Reduce review-channel status fields for the orientation packet."""
    authority = mapping(payload.get("authority_snapshot"))
    return summary_items(
        ("ok", payload.get("ok")),
        ("attention", mapping(payload.get("attention"))),
        ("current_session", current_session_summary(payload)),
        (
            "reviewer_runtime",
            reviewer_runtime_summary(mapping(payload.get("reviewer_runtime"))),
        ),
        ("reviewer_worker", mapping(payload.get("reviewer_worker"))),
        ("recommended_command", review_status_recommended_command(payload)),
        ("authority_snapshot", authority_reduced(authority)),
    )


def current_session_summary(payload: dict[str, object]) -> dict[str, object]:
    """Return current-session state from bridge or collaboration liveness."""
    bridge_session = mapping(payload.get("bridge_liveness")).get("current_session")
    collaboration_session = mapping(payload.get("collaboration")).get(
        "current_session"
    )
    return mapping(bridge_session or collaboration_session)


def review_status_recommended_command(payload: dict[str, object]) -> str:
    """Return the status-level next command from status or doctor output."""
    return text(
        payload.get("next_command")
        or mapping(payload.get("doctor")).get("recommended_command")
    )


def context_graph_summary(payload: dict[str, object]) -> dict[str, object]:
    """Reduce ContextGraph bootstrap fields for the orientation packet."""
    snapshot = mapping(payload.get("snapshot"))
    return {
        "snapshot": {
            "path": text(snapshot.get("path")),
            "commit_hash": text(snapshot.get("commit_hash")),
            "node_count": snapshot.get("node_count"),
            "edge_count": snapshot.get("edge_count"),
        },
        "active_plans": payload.get("active_plans") or [],
        "hotspots": payload.get("hotspots") or [],
        "quality_signals": mapping(payload.get("quality_signals")),
        "bootstrap_links": mapping(payload.get("bootstrap_links")),
    }


def final_summary(
    payloads: dict[str, dict[str, object]],
    *,
    steps: list[SessionOrientationStep],
    role: str,
) -> dict[str, object]:
    """Select the final next action from the preferred AuthoritySnapshot."""
    authority, source = preferred_authority(payloads)
    next_command = review_status_attention_command(payloads)
    if next_command:
        source = "review_status.attention"
    authority_next_command = text(authority.get("next_command"))
    push_command = startup_push_command(payloads)
    if not next_command:
        if push_command and authority_allows_startup_push(authority):
            next_command = push_command
            source = "startup.push_decision"
        elif authority_next_command:
            next_command = authority_next_command
    if not next_command:
        next_command = fallback_next_command(payloads)
        if next_command:
            source = "fallback"
    blocking_step = first_unparsed_step(steps)
    return summary_items(
        ("orientation_complete", blocking_step == ""),
        ("role", role),
        ("safe_to_continue", authority.get("safe_to_continue")),
        ("root_cause", text(authority.get("root_cause"))),
        ("required_action", text(authority.get("required_action"))),
        ("next_command", next_command),
        ("next_command_source", source),
        ("blocking_step", blocking_step),
        ("packet_target", mapping(authority.get("packet_target"))),
        ("active_target_path", text(authority.get("active_target_path"))),
        ("current_slice", text(authority.get("current_slice"))),
        ("safe_to_fanout", safe_to_fanout(payloads)),
        ("resync_required", authority.get("resync_required")),
    )


def preferred_authority(
    payloads: dict[str, dict[str, object]],
) -> tuple[dict[str, object], str]:
    """Return the preferred live authority payload and its source."""
    for payload_key, source in (
        ("review_status", "review_status"),
        ("session_resume", "session_resume"),
        ("startup", "startup"),
    ):
        authority = mapping(payloads.get(payload_key, {}).get("authority_snapshot"))
        if authority:
            return authority, source
    return {}, ""


def review_status_attention_command(
    payloads: dict[str, dict[str, object]],
) -> str:
    """Return the live status attention command when it names real work."""
    attention = mapping(payloads.get("review_status", {}).get("attention"))
    command = text(attention.get("recommended_command"))
    if command:
        return command
    return ""


def startup_push_command(payloads: dict[str, dict[str, object]]) -> str:
    """Return the governed push command when startup proves it is next."""
    startup = mapping(payloads.get("startup", {}))
    push_decision = mapping(startup.get("push_decision"))
    if text(push_decision.get("action")) != "run_devctl_push":
        return ""
    return text(push_decision.get("next_step_command"))


def authority_allows_startup_push(authority: dict[str, object]) -> bool:
    """Return True when the preferred authority does not block publication."""
    if authority.get("safe_to_continue") is not True:
        return False
    blocked_actions = authority.get("blocked_actions")
    if isinstance(blocked_actions, list) and "vcs.push" in blocked_actions:
        return False
    return True


def authority_reduced(authority: dict[str, object]) -> dict[str, object]:
    """Reduce AuthoritySnapshot to stable orientation fields."""
    return summary_items(
        ("required_action", text(authority.get("required_action"))),
        ("next_command", text(authority.get("next_command"))),
        ("safe_to_continue", authority.get("safe_to_continue")),
        ("root_cause", text(authority.get("root_cause"))),
        ("attention_status", text(authority.get("attention_status"))),
        ("packet_target", mapping(authority.get("packet_target"))),
        ("allowed_actions", authority.get("allowed_actions") or []),
        ("blocked_actions", authority.get("blocked_actions") or []),
        ("actor_authorities", authority.get("actor_authorities") or []),
    )


def packet_inbox_summary(packet_inbox: dict[str, object]) -> dict[str, object]:
    """Reduce PacketInboxState to per-agent attention rows."""
    agents = packet_inbox.get("agents")
    if not isinstance(agents, list):
        return {"agents": []}
    rows = []
    for row in agents:
        if not isinstance(row, dict):
            continue
        rows.append(packet_inbox_agent_summary(row))
    return {"agents": rows}


def packet_inbox_agent_summary(row: dict[str, object]) -> dict[str, object]:
    """Reduce one packet-inbox agent row."""
    return {
        "agent": text(row.get("agent")),
        "attention_status": text(row.get("attention_status")),
        "latest_finding_packet_id": text(row.get("latest_finding_packet_id")),
        "pending_actionable_packet_ids": row.get("pending_actionable_packet_ids")
        or [],
        "required_command": text(row.get("required_command")),
    }


def reviewer_runtime_summary(runtime: dict[str, object]) -> dict[str, object]:
    """Reduce reviewer runtime status for session orientation."""
    return {
        "reviewer_freshness": text(runtime.get("reviewer_freshness")),
        "publish_clear": runtime.get("publish_clear"),
        "packet_attention": mapping(runtime.get("packet_attention")),
        "remote_control_attachment": mapping(runtime.get("remote_control_attachment")),
    }


def fallback_next_command(payloads: dict[str, dict[str, object]]) -> str:
    """Return the next command from push decisions when authority omits one."""
    review_status = payloads.get("review_status", {})
    startup = payloads.get("startup", {})
    return first_text(
        {
            "review_status": review_status,
            "startup": startup,
        },
        ("review_status", "push_decision", "next_step_command"),
        ("startup", "push_decision", "next_step_command"),
    )


def safe_to_fanout(payloads: dict[str, dict[str, object]]) -> object:
    """Resolve the fanout advisory from startup/status payloads."""
    coordination = mapping(mapping(payloads.get("startup", {})).get("coordination"))
    if "safe_to_fanout" in coordination:
        return coordination.get("safe_to_fanout")
    return mapping(payloads.get("review_status", {})).get("safe_to_fanout")


def first_unparsed_step(steps: list[SessionOrientationStep]) -> str:
    """Return the first child command that failed JSON parsing."""
    for step in steps:
        if not step.parsed:
            return step.name
    return ""


def first_text(
    payloads: dict[str, dict[str, object]],
    *paths: tuple[str, ...],
) -> str:
    """Return the first non-empty nested text value."""
    for path in paths:
        resolved = text_at_path(payloads, path)
        if resolved:
            return resolved
    return ""


def text_at_path(payloads: dict[str, dict[str, object]], path: tuple[str, ...]) -> str:
    """Return one nested text value or an empty string when the path breaks."""
    value: object = payloads
    for key in path:
        if not isinstance(value, dict):
            return ""
        value = value.get(key)
    return text(value)
