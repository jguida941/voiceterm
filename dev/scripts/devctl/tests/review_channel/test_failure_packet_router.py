"""Tests for failure_packet_router (Plan r2 Slice 0).

The router must: (a) reject ActionResult envelopes that are not opted
in to auto-replay, (b) emit packet_posted events shaped to pass the
existing safe_auto_apply allowlist when they are eligible, and
(c) compose with safe_auto_apply.append_safe_auto_apply_events without
new decision logic.

Live fixture below mirrors the actual `staged_scope_missing_dirty_work`
FAIL envelope captured in this session at 2026-05-02T14:43:14Z. Once
``vcs.stage`` enters SAFE_AUTO_APPLY_ACTION_REQUESTS (Slice 2) the
router will auto-replay that exact failure shape.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dev.scripts.devctl.review_channel.event_store import (
    ReviewChannelArtifactPaths,
    load_events,
)
from dev.scripts.devctl.review_channel.failure_packet_router import (
    FailureRouterContext,
    _build_action_request_event,
    _default_evidence,
    _default_target_ref,
    _result_is_routable,
    route_action_result_failure,
)
from dev.scripts.devctl.review_channel.safe_auto_apply import (
    SAFE_AUTO_APPLY_ACTION_REQUESTS,
    _packet_allows_safe_auto_apply,
)


_LIVE_24_FILE_REPRO_RESULT = {
    "schema_version": 1,
    "contract_id": "ActionResult",
    "action_id": "vcs.stage",
    "ok": False,
    "status": "fail",
    "reason": "staged_scope_missing_dirty_work",
    "auto_executable": True,
    "remediation": "stage_commit_pipeline",
    "operator_guidance": (
        "The ReviewSnapshot refresh staged only receipt artifacts while "
        "real work remains dirty. Stage the intended paths first, or use "
        "`review-snapshot --write --receipt-commit` for a snapshot-only receipt."
    ),
    "warnings": (
        "dev/active/MASTER_PLAN.md",
        "dev/scripts/devctl/review_channel/follow_controller.py",
        "dev/scripts/devctl/review_channel/reviewer_follow_guard.py",
    ),
    "errors": (),
    "reason_chain": ("commit_failed", "staged_scope_missing_dirty_work"),
    "findings_count": 0,
    "artifact_paths": (),
}


def _artifact_paths(tmp_path: Path) -> ReviewChannelArtifactPaths:
    artifact_root = tmp_path / "review_channel"
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "events").mkdir(parents=True, exist_ok=True)
    (artifact_root / "state").mkdir(parents=True, exist_ok=True)
    return ReviewChannelArtifactPaths(
        artifact_root=artifact_root,
        event_log_path=artifact_root / "events" / "trace.ndjson",
        state_path=artifact_root / "state" / "latest.json",
        projections_root=artifact_root / "projections" / "latest",
    )


def _context(tmp_path: Path) -> FailureRouterContext:
    return FailureRouterContext(
        repo_root=tmp_path,
        artifact_paths=_artifact_paths(tmp_path),
        project_id="codex-voice-test",
        plan_id="MP-377",
        session_id="failure-router-test",
        controller_run_id="run-test",
    )


def test_result_is_not_routable_when_ok_true():
    result = {**_LIVE_24_FILE_REPRO_RESULT, "ok": True}
    assert _result_is_routable(result) is False


def test_result_is_not_routable_when_auto_executable_false():
    result = {**_LIVE_24_FILE_REPRO_RESULT, "auto_executable": False}
    assert _result_is_routable(result) is False


def test_result_is_not_routable_when_remediation_empty():
    result = {**_LIVE_24_FILE_REPRO_RESULT, "remediation": ""}
    assert _result_is_routable(result) is False


def test_result_is_not_routable_when_remediation_not_in_allowlist():
    result = {
        **_LIVE_24_FILE_REPRO_RESULT,
        "remediation": "vcs.stage",  # NOT yet in allowlist (Slice 2 adds it)
    }
    assert "vcs.stage" not in SAFE_AUTO_APPLY_ACTION_REQUESTS
    assert _result_is_routable(result) is False


def test_result_is_routable_for_stage_commit_pipeline():
    """Slice 0 baseline: existing allowlist entry must route cleanly."""
    assert "stage_commit_pipeline" in SAFE_AUTO_APPLY_ACTION_REQUESTS
    assert _result_is_routable(_LIVE_24_FILE_REPRO_RESULT) is True


def test_route_returns_empty_list_when_not_routable(tmp_path):
    result = {**_LIVE_24_FILE_REPRO_RESULT, "ok": True}
    written = route_action_result_failure(
        result=result,
        context=_context(tmp_path),
        existing_events=[],
    )
    assert written == []


def test_emitted_packet_passes_safe_auto_apply_allowlist(tmp_path):
    """The router's emitted event must be accepted by safe_auto_apply."""
    context = _context(tmp_path)
    event = _build_action_request_event(
        result=_LIVE_24_FILE_REPRO_RESULT,
        context=context,
        existing_events=[],
        target_ref="",
        full_guard_bundle_evidence="",
        completed_handoff_session_id="completed-handoff-1",
    )
    assert _packet_allows_safe_auto_apply(event) is True


def test_emitted_packet_fields_match_safe_auto_apply_shape(tmp_path):
    """Spot-check the contract shape every consumer of safe_auto_apply expects."""
    context = _context(tmp_path)
    event = _build_action_request_event(
        result=_LIVE_24_FILE_REPRO_RESULT,
        context=context,
        existing_events=[],
        target_ref="",
        full_guard_bundle_evidence="",
        completed_handoff_session_id="completed-handoff-1",
    )
    assert event["event_type"] == "packet_posted"
    assert event["from_agent"] == "system"
    assert event["to_agent"] == "claude"
    assert event["kind"] == "action_request"
    assert event["policy_hint"] == "safe_auto_apply"
    assert event["approval_required"] is False
    assert event["requested_action"] == "stage_commit_pipeline"
    assert event["target_kind"] == "runtime"
    assert str(event["target_ref"]).startswith("devctl_commit:")
    assert event["full_guard_bundle_evidence"]
    assert any(
        str(ref).startswith("agent_session_outcome:")
        for ref in event["evidence_refs"]
    )


def test_default_target_ref_uses_action_id_and_reason():
    target_ref = _default_target_ref("vcs.stage", "staged_scope_missing_dirty_work")
    assert target_ref == "devctl_commit:vcs.stage:staged_scope_missing_dirty_work"


def test_default_target_ref_falls_back_when_action_and_reason_empty():
    target_ref = _default_target_ref("", "")
    assert target_ref == "devctl_commit:auto_executable_failure"


def test_default_evidence_uses_reason_chain_when_present():
    result = {"reason_chain": ("commit_failed", "guard_failed"), "reason": "x"}
    assert _default_evidence(result) == "failure_envelope:commit_failed,guard_failed"


def test_default_evidence_falls_back_to_reason_when_chain_empty():
    result = {"reason_chain": (), "reason": "lonely_reason"}
    assert _default_evidence(result) == "failure_envelope:lonely_reason"


def test_route_writes_packet_then_safe_auto_apply_transitions(tmp_path):
    """End-to-end: routable result -> 1 packet event + 2 transitions on disk."""
    context = _context(tmp_path)
    written = route_action_result_failure(
        result=_LIVE_24_FILE_REPRO_RESULT,
        context=context,
        existing_events=[],
    )
    assert len(written) == 3
    types = [str(event.get("event_type") or "") for event in written]
    assert types[0] == "packet_posted"
    assert types[1] == "packet_acked"
    assert types[2] == "packet_applied"
    on_disk = load_events(Path(context.artifact_paths.event_log_path))
    assert [str(e.get("event_type") or "") for e in on_disk] == types
