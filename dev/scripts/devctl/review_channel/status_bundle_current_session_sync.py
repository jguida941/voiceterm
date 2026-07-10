"""Current-session synchronization helpers for status bundles."""

from __future__ import annotations

from collections.abc import Mapping


def sync_current_session_runtime_context(review_state: dict[str, object]) -> None:
    """Keep dependent projections coherent after current-session preservation."""
    current_session = review_state.get("current_session")
    if not isinstance(current_session, Mapping):
        return
    _sync_bridge_from_current_session(review_state, current_session)
    _sync_collaboration_from_current_session(review_state, current_session)
    _sync_agent_rows_from_current_session(review_state, current_session)


def _sync_bridge_from_current_session(
    review_state: dict[str, object],
    current_session: Mapping[str, object],
) -> None:
    bridge = review_state.get("bridge")
    if not isinstance(bridge, Mapping):
        return
    updated = dict(bridge)
    for target_field, source_field in _BRIDGE_FIELD_COPIES:
        _copy_if_present(updated, target_field, current_session, source_field)
    if "implementer_ack_state" in current_session:
        updated["implementer_ack_current"] = (
            str(current_session.get("implementer_ack_state") or "") == "current"
        )
        updated["claude_ack_current"] = updated["implementer_ack_current"]
    review_state["bridge"] = updated


def _sync_collaboration_from_current_session(
    review_state: dict[str, object],
    current_session: Mapping[str, object],
) -> None:
    collaboration = review_state.get("collaboration")
    if not isinstance(collaboration, Mapping):
        return
    updated = dict(collaboration)
    peer_review = updated.get("peer_review")
    if isinstance(peer_review, Mapping):
        peer = dict(peer_review)
        for field in _PEER_REVIEW_FIELDS:
            _copy_if_present(peer, field, current_session)
        updated["peer_review"] = peer
    current_slice = _text_value(
        current_session.get("current_instruction")
    ) or _text_value(current_session.get("last_reviewed_scope"))
    if current_slice:
        updated["current_slice"] = current_slice
    review_state["collaboration"] = updated


def _sync_agent_rows_from_current_session(
    review_state: dict[str, object],
    current_session: Mapping[str, object],
) -> None:
    job_state = _implementer_job_state_from_current_session(current_session)
    if not job_state:
        return
    _sync_agent_row_container(review_state, "registry", job_state=job_state)
    _sync_agent_row_container(
        review_state,
        "_compat",
        job_state=job_state,
        legacy_status=True,
    )


def _sync_agent_row_container(
    review_state: dict[str, object],
    key: str,
    *,
    job_state: str,
    legacy_status: bool = False,
) -> None:
    container = review_state.get(key)
    if not isinstance(container, Mapping):
        return
    updated = dict(container)
    updated["agents"] = _sync_implementer_agent_rows(
        updated.get("agents"),
        job_state=job_state,
        legacy_status=legacy_status,
    )
    review_state[key] = updated


def _sync_implementer_agent_rows(
    agents: object,
    *,
    job_state: str,
    legacy_status: bool = False,
) -> list[object]:
    if not isinstance(agents, (list, tuple)):
        return []
    return [
        _sync_implementer_agent_row(
            agent,
            job_state=job_state,
            legacy_status=legacy_status,
        )
        for agent in agents
    ]


def _sync_implementer_agent_row(
    agent: object,
    *,
    job_state: str,
    legacy_status: bool,
) -> object:
    if not isinstance(agent, Mapping):
        return agent
    row = dict(agent)
    current_job = _text_value(row.get("current_job") or row.get("role"))
    provider = _text_value(row.get("provider") or row.get("agent_id"))
    if current_job == "implementer" or provider == "claude":
        row["job_state"] = job_state
        if legacy_status:
            row["status"] = job_state
        if job_state.startswith("waiting") and not _text_value(row.get("waiting_on")):
            row["waiting_on"] = "reviewer"
    return row


def _implementer_job_state_from_current_session(
    current_session: Mapping[str, object],
) -> str:
    status = _text_value(current_session.get("implementer_status")).lower()
    if status in {"waiting", "waiting_for_ack", "implementing"}:
        return status
    if status and status not in {"(missing)", "inactive", "status unavailable"}:
        return status
    if _text_value(current_session.get("current_instruction")):
        return "waiting"
    return ""


def _copy_if_present(
    target: dict[str, object],
    target_field: str,
    source: Mapping[str, object],
    source_field: str | None = None,
) -> None:
    value = _text_value(source.get(source_field or target_field))
    if value:
        target[target_field] = value


def _text_value(value: object) -> str:
    text = str(value or "").strip()
    return "" if text == "(missing)" else text


_BRIDGE_FIELD_COPIES = (
    ("current_instruction", None),
    ("current_instruction_revision", None),
    ("open_findings", None),
    ("last_reviewed_scope", None),
    ("implementer_status", None),
    ("claude_status", "implementer_status"),
    ("implementer_ack", None),
    ("claude_ack", "implementer_ack"),
    ("implementer_ack_revision", None),
    ("claude_ack_revision", "implementer_ack_revision"),
    ("implementer_state_hash", None),
)

_PEER_REVIEW_FIELDS = (
    "current_instruction",
    "current_instruction_revision",
    "open_findings",
    "implementer_status",
    "implementer_ack",
    "implementer_ack_state",
    "implementer_state_hash",
    "last_reviewed_scope",
)


__all__ = ["sync_current_session_runtime_context"]
