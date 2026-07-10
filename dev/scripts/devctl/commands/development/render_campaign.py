"""Markdown rendering for the remote-control campaign section."""

from __future__ import annotations

from ..render_vocabulary import action_label, reason_label


def campaign_lines(campaign) -> list[str]:
    if not isinstance(campaign, dict):
        return []
    lines = ["", "## Remote-Control Campaign", ""]
    lines.append(f"- contract_id: {campaign.get('contract_id')}")
    lines.append(f"- plan_row_id: {campaign.get('plan_row_id')}")
    lines.append(f"- mode_id: {campaign.get('mode_id')}")
    lines.append(f"- status: {reason_label(campaign.get('status'))}")
    lines.append(f"- current_phase: {reason_label(campaign.get('current_phase'))}")
    lines.append(f"- summary: {campaign.get('summary')}")
    lines.extend(_transport_lines(campaign))
    lines.extend(_proof_lines(campaign))
    lines.extend(_packet_lines(campaign))
    lines.extend(_role_lines(campaign))
    lines.extend(_requirements_lines(campaign))
    return lines


def _transport_lines(campaign: dict[str, object]) -> list[str]:
    return [
        "- remote_control: "
        f"provider={campaign.get('remote_control_provider') or '(none)'} "
        f"status={campaign.get('remote_control_status') or '(none)'} "
        f"active={campaign.get('remote_control_active')} "
        f"identity_bound={campaign.get('remote_control_identity_bound')} "
        f"age={campaign.get('remote_control_age_seconds')}s "
        f"session={campaign.get('remote_control_session_id') or '(none)'}",
        "- typed_mode: "
        f"topology={campaign.get('coordination_topology') or '(none)'} "
        f"compatibility_legacy={campaign.get('legacy_reviewer_mode') or '(none)'} "
        f"compatibility_effective={campaign.get('effective_reviewer_mode') or '(none)'} "
        f"operator={campaign.get('operator_interaction_mode') or '(none)'}",
        "- topology_note: compatibility reviewer modes are drift evidence; "
        "workstreams, leases, packets, and authority snapshots decide runtime work",
        f"- mode_drift: {campaign.get('mode_drift')}",
        f"- fail_closed: {campaign.get('fail_closed')}",
        f"- mutation_allowed: {campaign.get('mutation_allowed')}",
        f"- publication_allowed: {campaign.get('publication_allowed')}",
    ]


def _proof_lines(campaign: dict[str, object]) -> list[str]:
    lines = [
        "- folded_plan_row_ids: "
        f"{_list_text(campaign.get('folded_plan_row_ids'))}",
        "- governed_exceptions: "
        f"status={campaign.get('governed_exception_status') or '(none)'} "
        f"pending={campaign.get('governed_exception_pending_count')} "
        f"errors={campaign.get('governed_exception_error_count')} "
        f"store={campaign.get('governed_exception_store_path') or '(none)'}",
        "- bypass_posture: "
        f"{campaign.get('bypass_posture') or '(none)'} "
        f"retired={campaign.get('bypass_publication_transport_retired')}",
        "- latest_push_report: "
        f"path={campaign.get('latest_push_report_path') or '(none)'} "
        f"status={campaign.get('latest_push_report_status') or '(none)'} "
        f"head={campaign.get('latest_push_report_head_commit') or '(none)'} "
        f"published={campaign.get('latest_push_report_published_remote')} "
        f"post_push_green={campaign.get('latest_push_report_post_push_green')} "
        f"matches_head={campaign.get('latest_push_report_matches_current_head')}",
    ]
    if campaign.get("publication_proof_summary"):
        lines.append(
            "- publication_proof_summary: "
            f"{campaign.get('publication_proof_summary')}"
        )
    return lines


def _packet_lines(campaign: dict[str, object]) -> list[str]:
    lines = [
        f"- pending_packet_id: {campaign.get('pending_packet_id') or '(none)'}"
    ]
    if campaign.get("pending_packet_required_command"):
        lines.append(
            "- pending_packet_required_command: "
            f"{campaign.get('pending_packet_required_command')}"
        )
    if campaign.get("codex_next_command"):
        lines.append(f"- codex_next_command: {campaign.get('codex_next_command')}")
    if campaign.get("claude_next_command"):
        lines.append(f"- claude_next_command: {campaign.get('claude_next_command')}")
    return lines


def _role_lines(campaign: dict[str, object]) -> list[str]:
    roles = campaign.get("roles") if isinstance(campaign.get("roles"), list) else []
    lines: list[str] = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        lines.append(
            f"- {role.get('actor_id')}:{role.get('role')} "
            f"status={role.get('status')} mutate={role.get('may_mutate')} "
            f"action={action_label(role.get('user_action') or role.get('required_action')) or '(none)'} "
            f"goal={role.get('continuation_goal') or '(none)'} "
            f"packet={role.get('active_packet_id') or '(none)'} "
            f"blocker={_clip(role.get('blocker'), limit=120) or '(none)'}"
        )
    return lines


def _requirements_lines(campaign: dict[str, object]) -> list[str]:
    requirements = campaign.get("proof_requirements")
    if not isinstance(requirements, list) or not requirements:
        return []
    return ["- proof_requirements: " + "; ".join(str(item) for item in requirements)]


def _list_text(value) -> str:
    if not isinstance(value, list) or not value:
        return "(none)"
    return ", ".join(str(item) for item in value)


def _clip(value: object, *, limit: int = 220) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


__all__ = ["campaign_lines"]
