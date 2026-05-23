"""Tests for `check_peer_lease_visibility` (A18 G35).

The guard enforces the A18 pre-mutation invariant: before any actor mutates a
PlanRow, the actor's local state must contain an up-to-date view of active
peer write leases on the same row. Three RULE_* failure shapes are exercised
explicitly, plus the green path and edge cases (own-actor lease excluded,
expired/released peer leases excluded, file-load fallback, render_markdown).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from dev.scripts.checks import check_peer_lease_visibility as guard


_NOW = datetime(2026, 5, 22, 23, 0, 0, tzinfo=timezone.utc)
_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _utc(seconds_ago: int) -> str:
    return (_NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _lease(
    *,
    lease_id: str,
    actor_id: str,
    row_id: str = _ROW_ID,
    status: str = "active",
) -> dict[str, object]:
    return {
        "lease_id": lease_id,
        "actor_id": actor_id,
        "row_id": row_id,
        "status": status,
    }


def _actor_view(
    *,
    actor_id: str = "claude",
    row_id: str = _ROW_ID,
    leases: list[dict[str, object]] | None = None,
    observed_seconds_ago: int | None = 30,
    include_observed_at: bool = True,
) -> dict[str, object]:
    view: dict[str, object] = {"actor_id": actor_id, "row_id": row_id}
    if leases is not None:
        view["peer_write_leases"] = leases
    if include_observed_at and observed_seconds_ago is not None:
        view["peer_write_leases_observed_at"] = _utc(observed_seconds_ago)
    return view


def test_green_no_violations_when_view_matches_active_leases():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex")]
    actor_view = _actor_view(
        leases=[_lease(lease_id="lease_codex_1", actor_id="codex")],
        observed_seconds_ago=10,
    )
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["failures"] == []
    assert report["active_peer_lease_count"] == 1
    assert report["local_peer_lease_count"] == 1


def test_rule_missing_when_local_state_omits_peer_leases_field():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex")]
    actor_view = _actor_view(leases=None, observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE in rule_ids
    missing = next(
        f
        for f in report["failures"]
        if f["rule_id"] == guard.RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE
    )
    assert "lease_codex_1" in missing["missing_lease_ids"]


def test_rule_missing_when_peer_leases_is_empty_but_peers_hold_leases():
    peer_leases = [_lease(lease_id="lease_codex_2", actor_id="codex")]
    actor_view = _actor_view(leases=[], observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE in rule_ids


def test_rule_stale_when_local_view_misses_newly_granted_lease():
    peer_leases = [
        _lease(lease_id="lease_codex_old", actor_id="codex"),
        _lease(lease_id="lease_codex_new", actor_id="codex"),
    ]
    actor_view = _actor_view(
        leases=[_lease(lease_id="lease_codex_old", actor_id="codex")],
        observed_seconds_ago=10,
    )
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_STALE_PEER_LEASE_VIEW in rule_ids
    stale = next(
        f
        for f in report["failures"]
        if f["rule_id"] == guard.RULE_STALE_PEER_LEASE_VIEW
    )
    assert "lease_codex_new" in stale["missing_lease_ids"]


def test_rule_stale_when_local_view_references_released_lease():
    peer_leases: list[dict[str, object]] = []
    actor_view = _actor_view(
        leases=[_lease(lease_id="lease_ghost", actor_id="codex")],
        observed_seconds_ago=10,
    )
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_STALE_PEER_LEASE_VIEW in rule_ids


def test_rule_view_age_exceeds_window_with_old_observation():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex")]
    actor_view = _actor_view(
        leases=[_lease(lease_id="lease_codex_1", actor_id="codex")],
        observed_seconds_ago=guard.DEFAULT_VIEW_AGE_WINDOW_SECONDS + 60,
    )
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW in rule_ids


def test_rule_view_age_exceeds_window_when_observed_at_missing():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex")]
    actor_view = _actor_view(
        leases=[_lease(lease_id="lease_codex_1", actor_id="codex")],
        include_observed_at=False,
    )
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW in rule_ids


def test_passes_within_custom_view_age_window():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex")]
    actor_view = _actor_view(
        leases=[_lease(lease_id="lease_codex_1", actor_id="codex")],
        observed_seconds_ago=120,
    )
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        view_age_window_seconds=600,
        now=_NOW,
    )
    assert report["ok"] is True


def test_actor_own_lease_is_not_a_peer_lease():
    # When the only lease in the live ledger belongs to the acting actor, the
    # actor does not need to observe it as a "peer" lease. No active peer leases
    # => no failure even though local view is empty.
    peer_leases = [_lease(lease_id="lease_self", actor_id="claude")]
    actor_view = _actor_view(leases=[], observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["active_peer_lease_count"] == 0


def test_released_peer_lease_is_not_active():
    peer_leases = [
        _lease(lease_id="lease_released", actor_id="codex", status="released"),
    ]
    actor_view = _actor_view(leases=[], observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["active_peer_lease_count"] == 0


def test_other_row_peer_leases_are_ignored():
    peer_leases = [_lease(lease_id="lease_other_row", actor_id="codex", row_id="MP-OTHER")]
    actor_view = _actor_view(leases=[], observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["active_peer_lease_count"] == 0


def test_row_filter_mismatch_flags_missing_visibility():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex", row_id="MP-OTHER")]
    actor_view = _actor_view(row_id="MP-DIFFERENT", leases=[], observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter="MP-OTHER",
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE in rule_ids


def test_output_schema_has_required_fields():
    report = guard.build_report(
        actor_view={"actor_id": "claude", "row_id": _ROW_ID},
        peer_leases=[],
        now=_NOW,
    )
    for field in (
        "ok",
        "actor_id",
        "row_id",
        "view_age_window_seconds",
        "active_peer_lease_count",
        "local_peer_lease_count",
        "peer_write_leases_observed_at",
        "checked_surfaces",
        "failures",
        "warnings",
    ):
        assert field in report, f"missing required field {field!r}"


def test_render_markdown_includes_failures_section():
    peer_leases = [_lease(lease_id="lease_codex_1", actor_id="codex")]
    actor_view = _actor_view(leases=None, observed_seconds_ago=10)
    report = guard.build_report(
        actor_view=actor_view,
        peer_leases=peer_leases,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    md = guard.render_markdown(report)
    assert "## Failures" in md
    assert guard.RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE in md


def test_load_from_disk_paths(tmp_path):
    actor_view_path = tmp_path / "actor_view.json"
    peer_leases_path = tmp_path / "peer_write_leases.json"
    actor_view_path.write_text(
        json.dumps(
            _actor_view(
                leases=[_lease(lease_id="lease_codex_1", actor_id="codex")],
                observed_seconds_ago=10,
            )
        ),
        encoding="utf-8",
    )
    peer_leases_path.write_text(
        json.dumps([_lease(lease_id="lease_codex_1", actor_id="codex")]),
        encoding="utf-8",
    )
    report = guard.build_report(
        actor_view_path=actor_view_path,
        peer_leases_path=peer_leases_path,
        row_id_filter=_ROW_ID,
        now=_NOW,
    )
    assert report["ok"] is True
    assert str(actor_view_path) in report["checked_surfaces"]
    assert str(peer_leases_path) in report["checked_surfaces"]


def test_missing_files_emit_warnings_and_treat_as_empty(tmp_path):
    actor_view_path = tmp_path / "does_not_exist.json"
    peer_leases_path = tmp_path / "also_missing.json"
    report = guard.build_report(
        actor_view_path=actor_view_path,
        peer_leases_path=peer_leases_path,
        now=_NOW,
    )
    assert report["ok"] is True  # no peers => no required visibility
    assert any("actor view missing" in w for w in report["warnings"])
    assert any("peer leases missing" in w for w in report["warnings"])


def test_constants_match_user_specified_names():
    # Operator-specified RULE_* constants must remain stable.
    assert guard.RULE_MISSING_PEER_LEASES_FROM_LOCAL_STATE
    assert guard.RULE_STALE_PEER_LEASE_VIEW
    assert guard.RULE_PEER_LEASE_VIEW_AGE_EXCEEDS_WINDOW
    assert guard.COMMAND == "check_peer_lease_visibility"
    assert guard.CONTRACT_ID == "PeerLeaseVisibilityGuard"
