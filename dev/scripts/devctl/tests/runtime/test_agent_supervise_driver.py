"""Tests for typed agent supervision decisions."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc

from dev.scripts.devctl.runtime.agent_supervise_driver import (
    AgentSuperviseInput,
    execute_agent_supervision_spawn,
    evaluate_agent_supervision,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassReceipt,
)


def _receipt(**overrides: object) -> BypassReceipt:
    values = {
        "receipt_id": "bypass:spawn:test",
        "reason": "Operator approved scoped supervise-driver spawn.",
        "operator_signature": "operator",
        "ai_approval_evidence": "rev_pkt_3685",
        "requested_authority_scope": BypassAuthorityScope.AGENT_SPAWN_ONLY,
        "granted_at_utc": "2026-05-12T00:00:00Z",
        "granted_by_operator_actor_id": "operator",
    }
    values.update(overrides)
    return BypassReceipt(**values)


def _review_state(**overrides: object) -> dict[str, object]:
    state: dict[str, object] = {
        "packets": [
            {
                "packet_id": "rev_pkt_anchor",
                "kind": "continuation_anchor",
                "to_agent": "codex",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "posted_at": "2026-05-12T00:00:00Z",
            }
        ],
        "collaboration": {
            "loop_autonomy_ok": True,
            "loop_wake_mode": "continuous",
            "loop_driver_agent": "claude",
        },
    }
    state.update(overrides)
    return state


def _session_file(tmp_path: Path, *, mtime_epoch: float) -> Path:
    session = tmp_path / "rollout-2026-05-12T01-00-00-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl"
    session.write_text("{}\n", encoding="utf-8")
    os.utime(session, (mtime_epoch, mtime_epoch))
    return session


def test_supervise_driver_authorizes_spawn_on_freeze_with_existing_gates(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            pid=0,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "spawn_authorized"
    assert report.freeze_detected is True
    assert report.process_exit_detected is False
    assert report.spawn_action is not None
    assert report.spawn_action.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert "review-channel --action launch" in report.next_command


def test_supervise_driver_blocks_freeze_without_bypass_receipt(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=None,
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "blocked"
    assert report.freeze_detected is True
    assert "bypass_receipt_missing" in report.blocked_reasons
    assert report.spawn_action is None


def test_supervise_driver_authorizes_spawn_on_process_exit_without_waiting_for_mtime(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp())

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            pid=99_999_999,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "spawn_authorized"
    assert report.process_exit_detected is True
    assert report.freeze_detected is False
    assert report.spawn_action is not None
    assert report.spawn_action.staleness_seconds == 900


def test_supervise_driver_healthy_when_no_exit_or_freeze(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 30)

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "healthy"
    assert report.trigger_reason == ""
    assert report.spawn_action is None


def test_supervise_driver_execute_launches_authorized_spawn(tmp_path: Path) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)
    launched: dict[str, object] = {}

    class _Process:
        pid = 12345

    def _launcher(args: list[str], **kwargs: object) -> _Process:
        launched["args"] = args
        launched["kwargs"] = kwargs
        return _Process()

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            pid=0,
            repo_root=tmp_path,
            review_state=_review_state(),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    executed = execute_agent_supervision_spawn(
        report,
        launcher=_launcher,
        cwd=tmp_path,
    )

    assert executed.launch_result is not None
    assert executed.launch_result.status == "spawned"
    assert executed.launch_result.pid == 12345
    assert launched["args"] == [
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "launch",
        "--remote-role",
        "reviewer",
        "--policy-hint",
        "review_only",
        "--terminal",
        "none",
        "--format",
        "md",
    ]
    kwargs = launched["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["cwd"] == tmp_path


def test_v4551_closed_helper_sidecar_status_is_ignored_not_blocked(
    tmp_path: Path,
) -> None:
    """v4.55.1 priority 1 (rev_pkt_4762/4763) regression.

    When CLI invokes `agent-supervise --session-id <sidecar-uuid>` to
    audit a CLOSED read-only helper sidecar, the supervise outcome must
    surface as the typed nonblocking status `ignored_helper_closed`, NOT
    `blocked`. Otherwise `develop next` / orchestration consumers
    promote a dead helper sidecar into a controller blocker via
    bypass_receipt_missing / loop_autonomy_not_green even after the
    anchor is suppressed. Uses rev_pkt_4381-shape projected anchor
    (target_session_id, target_role, anchor_scope all empty after
    review_state projection drops the local-review sentinel).
    """
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 1621)
    legacy_anchor = {
        "packet_id": "rev_pkt_4381_shape",
        "kind": "continuation_anchor",
        "to_agent": "codex",
        "target_role": "",
        "target_session_id": "",
        "session_id": None,
        "anchor_scope": "",
        "status": "acked",
        "lifecycle_current_state": "acknowledged",
        "posted_at": "2026-05-12T00:00:00Z",
    }

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_id="019e4a49-5c2c-7292-84cb-272045b48c92",
            session_path=session,
            repo_root=tmp_path,
            review_state={"packets": [legacy_anchor]},
            bypass_receipt=None,
            now_utc=now,
            staleness_threshold_seconds=600,
        )
    )

    assert report.process_state == "detached_runtime_only"
    assert report.status == "ignored_helper_closed"
    assert report.continuation_anchor_live is False


def test_v4551_session_scoped_anchor_for_other_session_does_not_leak(
    tmp_path: Path,
) -> None:
    """A session-scoped continuation anchor explicitly targeted at a
    different session must not appear in the supervise report for an
    audited helper sidecar (rev_pkt_4481 shape: anchor_scope=session,
    target_session_id pointing at a different reviewer session)."""
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)
    other_session_anchor = {
        "packet_id": "rev_pkt_4481_shape",
        "kind": "continuation_anchor",
        "to_agent": "codex",
        "anchor_scope": "session",
        "target_session_id": "019e3d46-5e44-7741-b2e9-e956dc12adbf",
        "session_id": "019e3d46-5e44-7741-b2e9-e956dc12adbf",
        "target_role": "reviewer",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "posted_at": "2026-05-12T00:00:00Z",
    }

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_id="019e4a49-5c2c-7292-84cb-272045b48c92",
            role="reviewer",
            session_path=session,
            repo_root=tmp_path,
            review_state={"packets": [other_session_anchor]},
            bypass_receipt=None,
            now_utc=now,
            staleness_threshold_seconds=600,
        )
    )

    assert report.continuation_anchor_packet_id == ""
    assert report.status == "ignored_helper_closed"


def test_v4551_role_scoped_anchor_visible_to_freeze_resurrection(
    tmp_path: Path,
) -> None:
    """rev_pkt_4760 acceptance: a role-scoped anchor for
    target_role=reviewer must remain visible to the legitimate
    freeze-and-spawn flow (no explicit `--session-id`, path-derived
    session). Spawn must still be authorized with bypass_receipt present.
    """
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)
    role_scoped_anchor = {
        "packet_id": "rev_pkt_role_anchor",
        "kind": "continuation_anchor",
        "to_agent": "codex",
        "anchor_scope": "role",
        "target_role": "reviewer",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "posted_at": "2026-05-12T00:00:00Z",
    }

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,  # no explicit session_id
            pid=0,
            repo_root=tmp_path,
            review_state={
                "packets": [role_scoped_anchor],
                "collaboration": {
                    "loop_autonomy_ok": True,
                    "loop_wake_mode": "continuous",
                    "loop_driver_agent": "claude",
                },
            },
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    assert report.status == "spawn_authorized"
    assert report.continuation_anchor_live is True
    assert report.continuation_anchor_packet_id == "rev_pkt_role_anchor"


def test_supervise_driver_execute_refuses_without_authorized_spawn(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 5, 12, 0, 20, tzinfo=UTC)
    session = _session_file(tmp_path, mtime_epoch=now.timestamp() - 901)
    launched = False

    def _launcher(args: list[str], **kwargs: object) -> object:
        nonlocal launched
        launched = True
        return object()

    report = evaluate_agent_supervision(
        AgentSuperviseInput(
            session_path=session,
            repo_root=tmp_path,
            review_state=_review_state(packets=[]),
            bypass_receipt=_receipt(),
            now_utc=now,
            staleness_threshold_seconds=900,
        )
    )

    executed = execute_agent_supervision_spawn(report, launcher=_launcher, cwd=tmp_path)

    assert launched is False
    assert executed.launch_result is not None
    assert executed.launch_result.status == "not_authorized"
    assert executed.launch_result.reason == "spawn_action_missing"
