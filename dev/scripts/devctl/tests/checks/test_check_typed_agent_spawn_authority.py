"""Tests for `check_typed_agent_spawn_authority` (A23 G44)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dev.scripts.checks import check_typed_agent_spawn_authority as guard


_NOW = datetime(2026, 5, 22, 23, 50, 0, tzinfo=timezone.utc)


def _utc(seconds_ago: int) -> str:
    return (_NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _spawn_evidence(
    *,
    session_id: str = "019e51d3-8edb-71e3-a8be-640ddac33546",
    rollout_path: str = "/tmp/rollout-2026-05-22T18-34-39.jsonl",
    spawned_seconds_ago: int = 120,
    killed: bool = False,
    provider: str = "codex",
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "rollout_path": rollout_path,
        "spawned_at_utc": _utc(spawned_seconds_ago),
        "killed": killed,
        "provider": provider,
    }


def _spawn_receipt(
    *,
    receipt_id: str = "agent-spawn:rec-1",
    provider: str = "codex",
    role: str = "reviewer",
    row_id: str = "MP-ROW-A",
    session_id: str = "019e51d3-8edb-71e3-a8be-640ddac33546",
    rollout_path: str = "/tmp/rollout-2026-05-22T18-34-39.jsonl",
    bypass_receipt_id: str = "bypass:rec-1",
    spawned_seconds_ago: int = 120,
    spawner_actor_id: str = "claude",
    duplicate_reason: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "receipt_id": receipt_id,
        "provider": provider,
        "role": role,
        "row_id": row_id,
        "session_id": session_id,
        "rollout_path": rollout_path,
        "bypass_receipt_id": bypass_receipt_id,
        "spawned_at_utc": _utc(spawned_seconds_ago),
        "spawner_actor_id": spawner_actor_id,
        "schema_version": 1,
        "contract_id": "AgentSpawnReceipt",
    }
    if duplicate_reason:
        payload["duplicate_reason"] = duplicate_reason
    return payload


def _termination_receipt(
    *,
    receipt_id: str = "agent-term:rec-1",
    spawn_receipt_id: str = "agent-spawn:rec-1",
    session_id: str = "019e51d3-8edb-71e3-a8be-640ddac33546",
    terminated_seconds_ago: int = 10,
    reason: str = "operator_kill",
) -> dict[str, object]:
    return {
        "receipt_id": receipt_id,
        "spawn_receipt_id": spawn_receipt_id,
        "session_id": session_id,
        "terminated_at_utc": _utc(terminated_seconds_ago),
        "terminator_actor_id": "operator",
        "reason": reason,
        "schema_version": 1,
        "contract_id": "AgentTerminationReceipt",
    }


def _bypass_lifecycle(
    *,
    receipt_id: str = "bypass:rec-1",
    expires_seconds_ago: int = -3600,  # default: 1h in future
    revoked_at_utc: str = "",
) -> dict[str, object]:
    return {
        "lifecycle_id": f"gel:{receipt_id}",
        "state": "bypass_active",
        "receipt": {
            "receipt_id": receipt_id,
            "expires_at_utc": _utc(expires_seconds_ago),
            "revoked_at_utc": revoked_at_utc,
            "requested_authority_scope": "agent_spawn_only",
            "state": "bypass_receipt_issued",
        },
    }


# ---------------------------------------------------------------------------
# Rule 1: spawn-without-receipt
# ---------------------------------------------------------------------------


def test_green_spawn_with_matching_receipt():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence()],
        spawn_receipts=[_spawn_receipt()],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    assert report["ok"] is True, report["violations"]
    assert report["violation_count"] == 0


def test_rule_1_spawn_without_receipt_fails():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence(spawned_seconds_ago=120)],
        spawn_receipts=[],
        termination_receipts=[],
        bypass_lifecycles=[],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SPAWN_WITHOUT_RECEIPT in rule_ids


def test_rule_1_fresh_spawn_within_grace_window_does_not_fail():
    # Spawn was 30s ago; default window is 60s, so within grace.
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence(spawned_seconds_ago=30)],
        spawn_receipts=[],
        termination_receipts=[],
        bypass_lifecycles=[],
        now=_NOW,
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SPAWN_WITHOUT_RECEIPT not in rule_ids


def test_rule_1_matches_via_rollout_path_when_session_id_missing():
    evidence = _spawn_evidence(session_id="")
    receipt = _spawn_receipt(session_id="")
    report = guard.build_report(
        spawn_evidence=[evidence],
        spawn_receipts=[receipt],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SPAWN_WITHOUT_RECEIPT not in rule_ids


# ---------------------------------------------------------------------------
# Rule 2: bypass-ref-invalid-or-expired
# ---------------------------------------------------------------------------


def test_rule_2_unknown_bypass_ref_fails():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence()],
        spawn_receipts=[_spawn_receipt(bypass_receipt_id="bypass:does-not-exist")],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BYPASS_REF_INVALID in rule_ids


def test_rule_2_expired_bypass_fails():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence()],
        spawn_receipts=[_spawn_receipt()],
        termination_receipts=[],
        bypass_lifecycles=[
            _bypass_lifecycle(expires_seconds_ago=3600),  # 1h in past
        ],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BYPASS_REF_INVALID in rule_ids


def test_rule_2_revoked_bypass_fails():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence()],
        spawn_receipts=[_spawn_receipt()],
        termination_receipts=[],
        bypass_lifecycles=[
            _bypass_lifecycle(expires_seconds_ago=-3600, revoked_at_utc=_utc(10)),
        ],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BYPASS_REF_INVALID in rule_ids


def test_rule_2_missing_bypass_ref_fails():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence()],
        spawn_receipts=[_spawn_receipt(bypass_receipt_id="")],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BYPASS_REF_INVALID in rule_ids


# ---------------------------------------------------------------------------
# Rule 3: duplicate-live-sessions
# ---------------------------------------------------------------------------


def test_rule_3_duplicate_live_sessions_fails():
    report = guard.build_report(
        spawn_evidence=[
            _spawn_evidence(session_id="sess-A", rollout_path="/tmp/A.jsonl"),
            _spawn_evidence(session_id="sess-B", rollout_path="/tmp/B.jsonl"),
        ],
        spawn_receipts=[
            _spawn_receipt(
                receipt_id="agent-spawn:rec-A",
                session_id="sess-A",
                rollout_path="/tmp/A.jsonl",
            ),
            _spawn_receipt(
                receipt_id="agent-spawn:rec-B",
                session_id="sess-B",
                rollout_path="/tmp/B.jsonl",
            ),
        ],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_DUPLICATE_LIVE_SESSIONS in rule_ids


def test_rule_3_typed_duplicate_reason_allows_dup():
    report = guard.build_report(
        spawn_evidence=[
            _spawn_evidence(session_id="sess-A", rollout_path="/tmp/A.jsonl"),
            _spawn_evidence(session_id="sess-B", rollout_path="/tmp/B.jsonl"),
        ],
        spawn_receipts=[
            _spawn_receipt(
                receipt_id="agent-spawn:rec-A",
                session_id="sess-A",
                rollout_path="/tmp/A.jsonl",
            ),
            _spawn_receipt(
                receipt_id="agent-spawn:rec-B",
                session_id="sess-B",
                rollout_path="/tmp/B.jsonl",
                duplicate_reason="A18_G31_typed_dual_role_review",
            ),
        ],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_DUPLICATE_LIVE_SESSIONS not in rule_ids


def test_rule_3_terminated_session_excluded_from_dup_count():
    report = guard.build_report(
        spawn_evidence=[
            _spawn_evidence(session_id="sess-A", rollout_path="/tmp/A.jsonl"),
            _spawn_evidence(
                session_id="sess-B", rollout_path="/tmp/B.jsonl", killed=True
            ),
        ],
        spawn_receipts=[
            _spawn_receipt(
                receipt_id="agent-spawn:rec-A",
                session_id="sess-A",
                rollout_path="/tmp/A.jsonl",
            ),
            _spawn_receipt(
                receipt_id="agent-spawn:rec-B",
                session_id="sess-B",
                rollout_path="/tmp/B.jsonl",
            ),
        ],
        termination_receipts=[
            _termination_receipt(
                receipt_id="agent-term:rec-B",
                spawn_receipt_id="agent-spawn:rec-B",
                session_id="sess-B",
            )
        ],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_DUPLICATE_LIVE_SESSIONS not in rule_ids


# ---------------------------------------------------------------------------
# Rule 4: termination-receipt-missing
# ---------------------------------------------------------------------------


def test_rule_4_kill_without_termination_receipt_fails():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence(killed=True)],
        spawn_receipts=[_spawn_receipt()],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_TERMINATION_RECEIPT_MISSING in rule_ids


def test_rule_4_kill_with_matching_termination_receipt_passes():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence(killed=True)],
        spawn_receipts=[_spawn_receipt()],
        termination_receipts=[_termination_receipt()],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_TERMINATION_RECEIPT_MISSING not in rule_ids
    assert report["ok"] is True


def test_rule_4_alive_session_does_not_require_termination():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence(killed=False)],
        spawn_receipts=[_spawn_receipt()],
        termination_receipts=[],
        bypass_lifecycles=[_bypass_lifecycle()],
        now=_NOW,
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_TERMINATION_RECEIPT_MISSING not in rule_ids


# ---------------------------------------------------------------------------
# Markdown rendering + main()
# ---------------------------------------------------------------------------


def test_render_markdown_violations_emits_each_rule():
    report = guard.build_report(
        spawn_evidence=[_spawn_evidence(spawned_seconds_ago=120)],
        spawn_receipts=[],
        termination_receipts=[],
        bypass_lifecycles=[],
        now=_NOW,
    )
    rendered = guard.render_markdown(report)
    assert guard.COMMAND in rendered
    assert "ok: False" in rendered
    assert guard.RULE_SPAWN_WITHOUT_RECEIPT in rendered


def test_main_returns_nonzero_when_violations(capsys, tmp_path):
    rollout_dir = tmp_path / "rollouts"
    rollout_dir.mkdir()
    # Drop a stale rollout (no matching receipts -> RULE_SPAWN_WITHOUT_RECEIPT).
    spawn_file = rollout_dir / "rollout-2026-05-22T18-34-39-019e51d3-8edb-71e3-a8be-640ddac33546.jsonl"
    spawn_file.write_text("{}\n", encoding="utf-8")
    # Make it appear old enough to be past the 60s grace window.
    import os, time
    past = time.time() - 3600
    os.utime(spawn_file, (past, past))

    spawn_path = tmp_path / "spawn.jsonl"
    spawn_path.write_text("", encoding="utf-8")
    term_path = tmp_path / "term.jsonl"
    term_path.write_text("", encoding="utf-8")
    bypass_path = tmp_path / "bypass.jsonl"
    bypass_path.write_text("", encoding="utf-8")

    rc = guard.main(
        [
            "--rollout-dir",
            str(rollout_dir),
            "--spawn-receipt-path",
            str(spawn_path),
            "--termination-receipt-path",
            str(term_path),
            "--bypass-lifecycle-path",
            str(bypass_path),
            "--format",
            "md",
        ]
    )
    assert rc == 1
    captured = capsys.readouterr().out
    assert guard.COMMAND in captured


def test_main_json_format_produces_parseable_payload(capsys, tmp_path):
    rollout_dir = tmp_path / "rollouts"
    rollout_dir.mkdir()
    spawn_path = tmp_path / "spawn.jsonl"
    spawn_path.write_text("", encoding="utf-8")
    term_path = tmp_path / "term.jsonl"
    term_path.write_text("", encoding="utf-8")
    bypass_path = tmp_path / "bypass.jsonl"
    bypass_path.write_text("", encoding="utf-8")

    rc = guard.main(
        [
            "--rollout-dir",
            str(rollout_dir),
            "--spawn-receipt-path",
            str(spawn_path),
            "--termination-receipt-path",
            str(term_path),
            "--bypass-lifecycle-path",
            str(bypass_path),
            "--format",
            "json",
        ]
    )
    assert rc == 0
    import json as _json
    payload = _json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["command"] == guard.COMMAND
    assert payload["contract_id"] == guard.CONTRACT_ID


def test_proposed_receipt_dataclasses_round_trip():
    spawn = guard.AgentSpawnReceipt(
        receipt_id="agent-spawn:rec-1",
        provider="codex",
        role="reviewer",
        row_id="MP-ROW-A",
        session_id="sess-A",
        rollout_path="/tmp/A.jsonl",
        bypass_receipt_id="bypass:rec-1",
        spawned_at_utc=_utc(60),
        spawner_actor_id="claude",
    )
    payload = spawn.to_dict()
    assert payload["receipt_id"] == "agent-spawn:rec-1"
    assert payload["contract_id"] == "AgentSpawnReceipt"

    term = guard.AgentTerminationReceipt(
        receipt_id="agent-term:rec-1",
        spawn_receipt_id="agent-spawn:rec-1",
        session_id="sess-A",
        terminated_at_utc=_utc(10),
        terminator_actor_id="operator",
        reason="kill",
    )
    term_payload = term.to_dict()
    assert term_payload["spawn_receipt_id"] == "agent-spawn:rec-1"
    assert term_payload["contract_id"] == "AgentTerminationReceipt"


def test_rollout_filename_parse_extracts_session_id_and_timestamp():
    ts = guard._parse_rollout_timestamp(
        "rollout-2026-05-22T18-34-39-019e51d3-8edb-71e3-a8be-640ddac33546.jsonl"
    )
    assert ts == "2026-05-22T18:34:39Z"
    sess = guard._parse_rollout_session_id(
        "rollout-2026-05-22T18-34-39-019e51d3-8edb-71e3-a8be-640ddac33546.jsonl"
    )
    assert sess == "019e51d3-8edb-71e3-a8be-640ddac33546"


def test_rollout_filename_parse_rejects_garbage():
    with pytest.raises(ValueError):
        guard._parse_rollout_timestamp("not-a-rollout-file.jsonl")
    assert guard._parse_rollout_session_id("notrollout.jsonl") == ""
