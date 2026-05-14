from __future__ import annotations

from dev.scripts.devctl.runtime.agent_mind_slice import AgentMindSlice
from dev.scripts.devctl.runtime.review_state_models import (
    RecoveryAssessmentState,
    RecoveryDecisionState,
    RecoveryDiagnosisState,
)
from dev.scripts.devctl.runtime.session_activity_log import SessionActivityEntry
from dev.scripts.devctl.runtime.session_liveness_signal import SessionLivenessSignal
from dev.scripts.devctl.runtime.session_status_projection import (
    SESSION_STATUS_DETACHED_RUNTIME_ONLY,
    SESSION_STATUS_MID_TASK_DEATH,
    SESSION_STATUS_RUNNING,
    SESSION_STATUS_TASK_COMPLETED,
    SESSION_STATUS_UNKNOWN,
    build_session_status_projection,
    session_status_projection_from_mapping,
)


def test_session_status_projection_prefers_task_complete_over_dead_liveness() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        bridge_liveness={
            "session_liveness_signals": [
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "state": "dead",
                    "process_live": False,
                }
            ]
        },
        agent_minds={
            "codex": {
                "session_id": "s-codex",
                "latest_task_complete_at": "2026-05-14T12:59:00Z",
            }
        },
    )

    assert projection.status == SESSION_STATUS_TASK_COMPLETED
    assert projection.answer == "task_complete"
    assert projection.rows[0].reason == "agent_mind_task_complete_observed"


def test_session_status_projection_marks_dead_without_completion_as_mid_task_death() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        bridge_liveness={
            "session_liveness_signals": [
                {
                    "provider": "claude",
                    "role": "implementer",
                    "state": "dead",
                    "process_live": False,
                }
            ]
        },
    )

    assert projection.status == SESSION_STATUS_MID_TASK_DEATH
    assert projection.answer == "mid_task_death"
    assert projection.rows[0].reason == "session_dead_without_task_complete"


def test_session_status_projection_ignores_stale_task_complete_from_old_session() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        collaboration={
            "participants": [
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "session_id": "s-current",
                }
            ]
        },
        bridge_liveness={
            "session_liveness_signals": [
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "state": "dead",
                    "process_live": False,
                }
            ]
        },
        agent_minds={
            "codex": {
                "session_id": "s-old",
                "latest_task_complete_at": "2026-05-14T12:59:00Z",
                "generated_at_utc": "2026-05-14T12:59:05Z",
            }
        },
    )

    assert projection.status == SESSION_STATUS_MID_TASK_DEATH
    assert projection.rows[0].agent_mind_session_matches_current is False
    assert projection.rows[0].agent_mind_stale is True
    assert projection.rows[0].reason == "session_dead_without_task_complete"


def test_session_status_projection_completed_handoff_outcome_wins() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        collaboration={
            "session_outcomes": [
                {
                    "provider": "claude",
                    "session_actor_role": "implementer",
                    "outcome": "completed_handoff",
                    "finished_at_utc": "2026-05-14T12:55:00Z",
                }
            ]
        },
    )

    assert projection.status == SESSION_STATUS_TASK_COMPLETED
    assert projection.rows[0].answer == "task_complete"
    assert projection.rows[0].reason == "agent_session_outcome_completed_handoff"


def test_session_status_projection_reports_running_from_live_liveness() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        bridge_liveness={
            "session_liveness_signals": [
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "state": "alive",
                    "process_live": True,
                }
            ],
            "push_enforcement": {
                "current_head_commit": "abc123",
                "worktree_dirty": True,
            },
        },
        worktree_hash="worktree:sha256:test",
    )

    assert projection.status == SESSION_STATUS_RUNNING
    assert projection.rows[0].head_sha == "abc123"
    assert projection.rows[0].worktree_hash == "worktree:sha256:test"
    assert projection.rows[0].worktree_dirty is True


def test_session_status_projection_mapping_parser_normalizes_contract() -> None:
    payload = session_status_projection_from_mapping({"rows": [{"provider": "codex"}]})

    assert payload["contract_id"] == "SessionStatusProjection"
    assert payload["schema_version"] == 1
    assert payload["status"] == "unknown"
    assert payload["rows"] == [{"provider": "codex"}]


def test_session_status_projection_task_complete_clean() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        agent_minds={
            "codex": {
                "contract_id": "AgentMindSlice",
                "agent_provider": "codex",
                "session_id": "s-codex",
                "latest_task_complete_at": "2026-05-14T12:59:00Z",
            }
        },
        worktree_dirty=False,
    )

    assert projection.status == SESSION_STATUS_TASK_COMPLETED
    assert projection.answer == "task_complete"
    assert projection.worktree_dirty is False
    assert projection.rows[0].reason == "agent_mind_task_complete_observed"


def test_session_status_projection_process_killed_mid_outcome() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        collaboration={
            "session_outcomes": [
                {
                    "provider": "codex",
                    "session_actor_role": "reviewer",
                    "outcome": "process_died",
                    "reason": "pid exited",
                    "finished_at_utc": "2026-05-14T12:59:00Z",
                }
            ]
        },
    )

    assert projection.status == SESSION_STATUS_MID_TASK_DEATH
    assert projection.rows[0].reason == "agent_session_outcome_process_died"


def test_session_status_projection_unresolved_outcome_escalates() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        collaboration={
            "session_outcomes": [
                {
                    "provider": "claude",
                    "outcome": "unresolved",
                    "reason": "missing handoff",
                    "finished_at_utc": "2026-05-14T12:59:00Z",
                }
            ]
        },
        bridge_liveness={
            "session_liveness_signals": [
                {"provider": "claude", "state": "dead", "process_live": False}
            ]
        },
    )

    assert projection.status == SESSION_STATUS_MID_TASK_DEATH
    assert projection.rows[0].reason == "agent_session_outcome_unresolved"


def test_session_status_projection_detached_runtime_no_conductor() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        bridge_liveness={
            "session_liveness_signals": [
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "state": "detached_runtime_only",
                    "process_live": False,
                }
            ]
        },
    )

    assert projection.status == SESSION_STATUS_DETACHED_RUNTIME_ONLY
    assert projection.answer == "runtime_detached"
    assert projection.rows[0].reason == "runtime_activity_without_live_conductor"


def test_session_status_projection_multiple_participants_any_dead_escalates() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        bridge_liveness={
            "session_liveness_signals": [
                {
                    "provider": "codex",
                    "role": "reviewer",
                    "state": "alive",
                    "process_live": True,
                },
                {
                    "provider": "claude",
                    "role": "implementer",
                    "state": "dead",
                    "process_live": False,
                },
            ]
        },
    )

    assert projection.status == SESSION_STATUS_MID_TASK_DEATH
    assert {row.provider: row.status for row in projection.rows} == {
        "codex": SESSION_STATUS_RUNNING,
        "claude": SESSION_STATUS_MID_TASK_DEATH,
    }


def test_session_status_projection_insufficient_evidence_returns_unknown() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
    )

    assert projection.status == SESSION_STATUS_UNKNOWN
    assert projection.answer == "unknown"
    assert projection.rows == ()


def test_session_status_projection_consumes_typed_contracts_for_evidence() -> None:
    projection = build_session_status_projection(
        generated_at_utc="2026-05-14T13:00:00Z",
        bridge_liveness={
            "session_liveness_signals": (
                SessionLivenessSignal(
                    provider="codex",
                    role="reviewer",
                    state="alive",
                    reason="conductor and runtime daemons active",
                    process_live=True,
                ),
            )
        },
        agent_minds={
            "codex": AgentMindSlice(
                schema_version=1,
                contract_id="AgentMindSlice",
                agent_provider="codex",
                session_id="s-codex",
                session_path="/tmp/codex.jsonl",
                generated_at_utc="2026-05-14T12:59:00Z",
                last_cursor="42",
            )
        },
        recovery_assessment=RecoveryAssessmentState(
            diagnosis=RecoveryDiagnosisState(
                status="healthy",
                root_cause="none",
            ),
            decision=RecoveryDecisionState(
                action_id="continue",
            ),
        ),
        session_activity_entries=(
            SessionActivityEntry(
                entry_id="entry-1",
                session_id="s-codex",
                actor_id="codex",
                occurred_at_utc="2026-05-14T12:58:00Z",
                activity_type="dogfood_self_check",
                summary="status projection exercised",
            ),
        ),
    )

    assert projection.status == SESSION_STATUS_RUNNING
    assert "session_activity:entry-1" in projection.rows[0].evidence_refs
    assert "recovery_assessment_status:healthy" in projection.evidence_refs
