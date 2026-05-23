"""Tests for ``check_shared_round_state_observed`` (A18 G34).

Per delete_after_ingest.md lines 1113-1117 (and shared worker awareness
requirements at lines 938-950), the G34 guard fails closed when an actor
starts mutation without observing the current shared round digest. These
tests exercise each RULE_* failure path and the green-path schema contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from dev.scripts.checks import check_shared_round_state_observed as guard


_NOW = datetime(2026, 5, 22, 23, 0, 0, tzinfo=timezone.utc)
_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
_SOURCE_HASH = "abc123deadbeef"


def _utc(seconds_ago: int) -> str:
    return (_NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _full_observation(
    *,
    actor_id: str = "codex",
    row_id: str = _ROW_ID,
    plan_row_observed: bool = True,
    source_hash_observed: str = _SOURCE_HASH,
    peer_occupancies_observed: tuple[str, ...] = ("claude-reviewer",),
    peer_write_leases_observed: tuple[str, ...] = ("lease-1",),
    active_packets_observed: tuple[str, ...] = ("rev_pkt_1",),
    blockers_observed: tuple[str, ...] = ("blocker-1",),
    proof_obligations_observed: tuple[str, ...] = ("proof-1",),
    observed_at_seconds_ago: int = 30,
) -> dict[str, object]:
    return {
        "actor_id": actor_id,
        "row_id": row_id,
        "plan_row_observed": plan_row_observed,
        "source_hash_observed": source_hash_observed,
        "peer_occupancies_observed": list(peer_occupancies_observed),
        "peer_write_leases_observed": list(peer_write_leases_observed),
        "active_packets_observed": list(active_packets_observed),
        "blockers_observed": list(blockers_observed),
        "proof_obligations_observed": list(proof_obligations_observed),
        "observed_at_utc": _utc(observed_at_seconds_ago),
    }


def _expectation(**overrides: object) -> guard.SharedRoundExpectation:
    payload: dict[str, object] = {"row_id": _ROW_ID, "source_hash": _SOURCE_HASH}
    payload.update(overrides)
    return guard.SharedRoundExpectation(
        row_id=str(payload["row_id"]),
        source_hash=str(payload["source_hash"]),
        requires_peer_occupancies=bool(payload.get("requires_peer_occupancies", True)),
        requires_peer_write_leases=bool(payload.get("requires_peer_write_leases", True)),
        requires_active_packets=bool(payload.get("requires_active_packets", True)),
        requires_blockers=bool(payload.get("requires_blockers", True)),
        requires_proof_obligations=bool(payload.get("requires_proof_obligations", True)),
    )


def test_green_full_observation_passes():
    observations = [_full_observation()]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is True, report
    assert report["observation_count"] == 1
    assert report["failure_count"] == 0
    assert report["failures"] == []
    assert report["rule_counts"] == {}


def test_rule_missing_plan_row_observation():
    observations = [_full_observation(plan_row_observed=False)]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PLAN_ROW_OBSERVATION in rule_ids


def test_rule_missing_plan_row_observation_row_id_mismatch():
    observations = [_full_observation(row_id="MP-OTHER-ROW")]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PLAN_ROW_OBSERVATION in rule_ids


def test_rule_missing_source_hash_observation_empty():
    observations = [_full_observation(source_hash_observed="")]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_SOURCE_HASH_OBSERVATION in rule_ids


def test_rule_missing_source_hash_observation_mismatch():
    observations = [_full_observation(source_hash_observed="stale_hash")]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_SOURCE_HASH_OBSERVATION in rule_ids


def test_rule_missing_peer_occupancy_observation():
    observations = [_full_observation(peer_occupancies_observed=())]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PEER_OCCUPANCY_OBSERVATION in rule_ids


def test_rule_missing_peer_lease_observation():
    observations = [_full_observation(peer_write_leases_observed=())]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PEER_LEASE_OBSERVATION in rule_ids


def test_rule_missing_active_packet_observation():
    observations = [_full_observation(active_packets_observed=())]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_ACTIVE_PACKET_OBSERVATION in rule_ids


def test_rule_missing_blocker_observation():
    observations = [_full_observation(blockers_observed=())]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_BLOCKER_OBSERVATION in rule_ids


def test_rule_missing_proof_obligation_observation():
    observations = [_full_observation(proof_obligations_observed=())]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PROOF_OBLIGATION_OBSERVATION in rule_ids


def test_rule_stale_observed_at_missing_timestamp():
    observations = [_full_observation()]
    observations[0]["observed_at_utc"] = ""
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_STALE_OBSERVED_AT in rule_ids


def test_rule_stale_observed_at_beyond_freshness_window():
    observations = [
        _full_observation(
            observed_at_seconds_ago=guard.DEFAULT_FRESHNESS_WINDOW_SECONDS + 30
        )
    ]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_STALE_OBSERVED_AT in rule_ids


def test_multiple_actors_each_evaluated():
    observations = [
        _full_observation(actor_id="codex"),
        _full_observation(actor_id="claude", blockers_observed=()),
    ]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    assert report["observation_count"] == 2
    # Only the claude observation should fail blocker rule.
    failed_actors = {f["actor_id"] for f in report["failures"]}
    assert failed_actors == {"claude"}
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert rule_ids == {guard.RULE_MISSING_BLOCKER_OBSERVATION}


def test_optional_expectation_skips_disabled_categories():
    observations = [
        _full_observation(
            peer_occupancies_observed=(),
            peer_write_leases_observed=(),
            active_packets_observed=(),
            blockers_observed=(),
            proof_obligations_observed=(),
        )
    ]
    expectation = guard.SharedRoundExpectation(
        row_id=_ROW_ID,
        source_hash=_SOURCE_HASH,
        requires_peer_occupancies=False,
        requires_peer_write_leases=False,
        requires_active_packets=False,
        requires_blockers=False,
        requires_proof_obligations=False,
    )
    report = guard.build_report(
        observations=observations,
        expectation=expectation,
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["failures"] == []


def test_state_path_load_when_observations_not_passed(tmp_path: Path):
    state_path = tmp_path / "shared_round.json"
    state_path.write_text(
        '{"expectation": {"row_id": "%s", "source_hash": "%s"},'
        ' "observations": [%s]}'
        % (
            _ROW_ID,
            _SOURCE_HASH,
            '{"actor_id": "codex", "row_id": "%s",'
            ' "plan_row_observed": true,'
            ' "source_hash_observed": "%s",'
            ' "peer_occupancies_observed": ["claude"],'
            ' "peer_write_leases_observed": ["lease-1"],'
            ' "active_packets_observed": ["rev_pkt_1"],'
            ' "blockers_observed": ["b1"],'
            ' "proof_obligations_observed": ["p1"],'
            ' "observed_at_utc": "%s"}'
            % (_ROW_ID, _SOURCE_HASH, _utc(30)),
        ),
        encoding="utf-8",
    )
    report = guard.build_report(state_path=state_path, now=_NOW)
    assert report["ok"] is True
    assert str(state_path) in report["checked_surfaces"]
    assert report["observation_count"] == 1


def test_state_path_missing_emits_warning(tmp_path: Path):
    state_path = tmp_path / "nonexistent.json"
    report = guard.build_report(state_path=state_path, now=_NOW)
    assert report["ok"] is True  # no observations, no failures
    assert any("missing" in str(w) for w in report["warnings"])


def test_output_schema_contract():
    report = guard.build_report(
        observations=[],
        expectation=_expectation(),
        now=_NOW,
    )
    for field in (
        "schema_version",
        "contract_id",
        "command",
        "timestamp",
        "ok",
        "current_plan_row_id",
        "expected_source_hash",
        "freshness_window_seconds",
        "observation_count",
        "failure_count",
        "rule_counts",
        "checked_surfaces",
        "failures",
        "warnings",
    ):
        assert field in report, f"missing required field {field!r}"
    assert report["command"] == "check_shared_round_state_observed"
    assert report["contract_id"] == "SharedRoundStateObservedGuard"


def test_render_markdown_includes_failures():
    observations = [_full_observation(plan_row_observed=False, source_hash_observed="")]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    md = guard.render_markdown(report)
    assert "## Failures" in md
    assert guard.RULE_MISSING_PLAN_ROW_OBSERVATION in md
    assert guard.RULE_MISSING_SOURCE_HASH_OBSERVATION in md


def test_render_markdown_green_path_omits_failures_section():
    observations = [_full_observation()]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    md = guard.render_markdown(report)
    assert "## Failures" not in md


def test_rule_counts_aggregates_per_rule():
    observations = [
        _full_observation(actor_id="actor1", plan_row_observed=False),
        _full_observation(actor_id="actor2", plan_row_observed=False),
        _full_observation(actor_id="actor3", source_hash_observed=""),
    ]
    report = guard.build_report(
        observations=observations,
        expectation=_expectation(),
        now=_NOW,
    )
    assert report["ok"] is False
    assert report["rule_counts"][guard.RULE_MISSING_PLAN_ROW_OBSERVATION] == 2
    assert report["rule_counts"][guard.RULE_MISSING_SOURCE_HASH_OBSERVATION] == 1
