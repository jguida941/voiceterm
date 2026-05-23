from __future__ import annotations

import pytest

from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
    validate_post_request,
)
from dev.scripts.devctl.review_channel.packet_route_resolution import (
    resolve_packet_post_route_scope,
)


def _request(
    *,
    target_role: str = "",
    target_session_id: str = "",
    requested_action: str = "review_only",
) -> PacketPostRequest:
    return PacketPostRequest(
        from_agent="codex",
        to_agent="claude",
        kind="action_request",
        summary="Route work",
        body="Route work to one typed session.",
        requested_action=requested_action,
        target=PacketTargetFields.from_values(
            target_kind="plan",
            target_ref="plan://MP-377/router",
            target_revision="sha256:abc",
            anchor_refs=("checklist:router",),
            intake_ref="intake://rev_pkt_1",
            mutation_op="append",
            target_role=target_role,
            target_session_id=target_session_id,
        ),
    )


def _row(
    *,
    role: str = "implementer",
    session_id: str = "s1",
    status: str = "polling",
    idle_seconds: int = 1,
    stale_after_seconds: int = 600,
) -> dict[str, object]:
    return {
        "actor_id": "claude",
        "role": role,
        "session_id": session_id,
        "status": status,
        "idle_seconds": idle_seconds,
        "stale_after_seconds": stale_after_seconds,
        "confidence_class": "derived_typed_event",
    }


def _state(*rows: dict[str, object]) -> dict[str, object]:
    return {"agent_work_board": {"rows": list(rows)}}


def test_packet_route_resolution_rejects_ambiguous_provider_post() -> None:
    with pytest.raises(ValueError, match="multiple fresh sessions"):
        resolve_packet_post_route_scope(
            _request(),
            review_state=_state(_row(session_id="s1"), _row(session_id="s2")),
        )


def test_packet_route_resolution_auto_scopes_single_fresh_session_and_preserves_plan_fields() -> None:
    resolved = resolve_packet_post_route_scope(
        _request(),
        review_state=_state(_row(role="coder", session_id="s1")),
    )

    assert resolved.target.target_role == "implementer"
    assert resolved.target.target_session_id == "s1"
    assert resolved.target.target_kind == "plan"
    assert resolved.target.target_ref == "plan://MP-377/router"
    assert resolved.target.target_revision == "sha256:abc"
    assert resolved.target.anchor_refs == ("checklist:router",)
    assert resolved.target.intake_ref == "intake://rev_pkt_1"
    assert resolved.target.mutation_op == "append"


def test_plan_scoped_continuation_anchor_validates_plan_target() -> None:
    validate_post_request(
        PacketPostRequest(
            from_agent="claude",
            to_agent="codex",
            kind="continuation_anchor",
            summary="Continue MP-377",
            body="Continue the plan-scoped goal.",
            target=PacketTargetFields.from_values(
                target_kind="plan",
                target_ref="plan:MP-377",
                anchor_scope="plan",
            ),
        ),
        valid_agent_ids=("codex", "claude"),
    )


def test_plan_scoped_continuation_anchor_requires_plan_target() -> None:
    with pytest.raises(ValueError, match="--plan-scoped anchors require"):
        validate_post_request(
            PacketPostRequest(
                from_agent="claude",
                to_agent="codex",
                kind="continuation_anchor",
                summary="Continue MP-377",
                body="Continue the plan-scoped goal.",
                target=PacketTargetFields.from_values(anchor_scope="plan"),
            ),
            valid_agent_ids=("codex", "claude"),
        )


def test_session_scoped_continuation_anchor_requires_session_id() -> None:
    with pytest.raises(ValueError, match="--session-scoped anchors require"):
        validate_post_request(
            PacketPostRequest(
                from_agent="claude",
                to_agent="codex",
                kind="continuation_anchor",
                summary="Continue session",
                body="Continue this exact session.",
                target=PacketTargetFields.from_values(anchor_scope="session"),
            ),
            valid_agent_ids=("codex", "claude"),
        )


def test_stop_anchor_requires_typed_scope() -> None:
    with pytest.raises(ValueError, match="stop_anchor packets require typed scope"):
        validate_post_request(
            PacketPostRequest(
                from_agent="claude",
                to_agent="codex",
                kind="stop_anchor",
                summary="Stop later",
                body="Target session: dead-session",
            ),
            valid_agent_ids=("codex", "claude"),
        )


def test_packet_route_resolution_scoped_role_must_resolve_to_one_fresh_session() -> None:
    resolved = resolve_packet_post_route_scope(
        _request(target_role="dashboard"),
        review_state=_state(
            _row(role="implementer", session_id="s1"),
            _row(role="dashboard", session_id="s2"),
        ),
    )

    assert resolved.target.target_role == "dashboard"
    assert resolved.target.target_session_id == "s2"


def test_packet_route_resolution_session_id_fills_missing_role_from_fresh_session() -> None:
    resolved = resolve_packet_post_route_scope(
        _request(target_session_id="s1"),
        review_state=_state(_row(role="implementer", session_id="s1")),
    )

    assert resolved.target.target_role == "implementer"
    assert resolved.target.target_session_id == "s1"


def test_packet_route_resolution_preserves_explicit_role_with_session_scope() -> None:
    resolved = resolve_packet_post_route_scope(
        _request(target_role="implementer", target_session_id="s1"),
        review_state=_state(_row(role="dashboard", session_id="s1")),
    )

    assert resolved.target.target_role == "implementer"
    assert resolved.target.target_session_id == "s1"


def test_non_runtime_action_request_keeps_ambiguous_role_scope() -> None:
    resolved = resolve_packet_post_route_scope(
        _request(target_role="reviewer", requested_action="restore_reviewer_turn"),
        review_state=_state(
            _row(role="implementer", session_id="s1"),
            _row(role="dashboard", session_id="s2"),
        ),
    )

    assert resolved.target.target_role == "reviewer"
    assert resolved.target.target_session_id == ""


def test_packet_route_resolution_rejects_stale_or_wrong_session() -> None:
    with pytest.raises(ValueError, match="target_session_id"):
        resolve_packet_post_route_scope(
            _request(target_role="implementer", target_session_id="s-old"),
            review_state=_state(
                _row(
                    role="implementer",
                    session_id="s-old",
                    status="idle",
                    idle_seconds=999,
                    stale_after_seconds=600,
                ),
                _row(role="implementer", session_id="s-new"),
            ),
        )
