"""Tests for `check_role_delegation_authority` (G30)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.checks import check_role_delegation_authority as guard


_NOW = datetime(2026, 5, 22, 23, 0, 0, tzinfo=timezone.utc)


def _live_parent(
    *,
    occupancy_id: str = "occ-parent-A",
    delegation_capability: bool = True,
    allowed_child_role_ids: tuple[str, ...] = ("implementer", "research"),
    liveness: str = "live",
) -> dict[str, object]:
    return {
        "role_occupancy_id": occupancy_id,
        "role_id": "orchestrator",
        "delegation_capability": delegation_capability,
        "allowed_child_role_ids": list(allowed_child_role_ids),
        "liveness": liveness,
    }


def _grant(
    *,
    grant_id: str = "grant-A",
    parent_role_occupancy_id: str = "occ-parent-A",
    child_actor_id: str = "actor-child-1",
    role_id: str = "implementer",
    target_plan_row_id: str = "PLAN-ROW-XYZ",
    authority_refs: tuple[str, ...] = ("RoleOccupancyAssignment:occ-parent-A",),
    expires_at_utc: str = "2026-06-01T00:00:00Z",
) -> dict[str, object]:
    return {
        "grant_id": grant_id,
        "parent_role_occupancy_id": parent_role_occupancy_id,
        "child_actor_id": child_actor_id,
        "role_id": role_id,
        "target_plan_row_id": target_plan_row_id,
        "authority_refs": list(authority_refs),
        "expires_at_utc": expires_at_utc,
    }


# ---------------------------------------------------------------------------
# GREEN: typed delegation grants pass.
# ---------------------------------------------------------------------------


def test_green_well_formed_grant_passes():
    report = guard.build_report(
        grants=[_grant()],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["checked_grant_count"] == 1
    assert report["live_actor_count"] == 1


def test_green_multiple_grants_one_parent_pass():
    report = guard.build_report(
        grants=[
            _grant(grant_id="g1", child_actor_id="c1"),
            _grant(grant_id="g2", child_actor_id="c2", role_id="research"),
        ],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["checked_grant_count"] == 2


def test_green_no_grants_passes():
    report = guard.build_report(
        grants=[],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_green_grant_uses_plan_row_id_alias():
    grant = _grant(target_plan_row_id="")
    grant["plan_row_id"] = "PLAN-ROW-ALIAS"
    report = guard.build_report(
        grants=[grant],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is True


# ---------------------------------------------------------------------------
# RED: each failure condition produces a typed violation.
# ---------------------------------------------------------------------------


def test_red_missing_parent_role_occupancy_fails():
    grant = _grant(parent_role_occupancy_id="")
    report = guard.build_report(
        grants=[grant],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PARENT_ROLE_OCCUPANCY in rule_ids


def test_red_parent_not_in_live_actor_index_fails():
    report = guard.build_report(
        grants=[_grant(parent_role_occupancy_id="occ-ghost")],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_PARENT_NOT_LIVE in rule_ids


def test_red_parent_retired_fails():
    report = guard.build_report(
        grants=[_grant()],
        live_actors=[_live_parent(liveness="retired")],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_PARENT_NOT_LIVE in rule_ids


def test_red_missing_delegation_capability_fails():
    report = guard.build_report(
        grants=[_grant()],
        live_actors=[
            _live_parent(delegation_capability=False, allowed_child_role_ids=())
        ],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_DELEGATION_CAPABILITY in rule_ids


def test_red_child_role_not_in_allowed_set_fails():
    report = guard.build_report(
        grants=[_grant(role_id="merge_coordinator")],
        live_actors=[_live_parent(allowed_child_role_ids=("implementer",))],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ROLE_NOT_ALLOWED in rule_ids


def test_red_missing_authority_refs_fails():
    report = guard.build_report(
        grants=[_grant(authority_refs=())],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_AUTHORITY_REFS in rule_ids


def test_red_expired_delegation_fails():
    past = (_NOW - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    report = guard.build_report(
        grants=[_grant(expires_at_utc=past)],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_EXPIRED_DELEGATION in rule_ids


def test_red_missing_expiry_fails():
    report = guard.build_report(
        grants=[_grant(expires_at_utc="")],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_EXPIRED_DELEGATION in rule_ids


def test_red_missing_plan_row_fails():
    grant = _grant(target_plan_row_id="")
    report = guard.build_report(
        grants=[grant],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_PLAN_ROW in rule_ids


def test_red_multiple_field_failures_all_reported():
    grant = _grant(authority_refs=(), expires_at_utc="", target_plan_row_id="")
    report = guard.build_report(
        grants=[grant],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_AUTHORITY_REFS in rule_ids
    assert guard.RULE_EXPIRED_DELEGATION in rule_ids
    assert guard.RULE_MISSING_PLAN_ROW in rule_ids


# ---------------------------------------------------------------------------
# Filters and projection helpers.
# ---------------------------------------------------------------------------


def test_row_id_filter_excludes_other_rows():
    report = guard.build_report(
        grants=[_grant(target_plan_row_id="PLAN-ROW-OTHER")],
        live_actors=[_live_parent()],
        row_id_filter="PLAN-ROW-XYZ",
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["checked_grant_count"] == 0


def test_row_id_filter_includes_matching_grant():
    report = guard.build_report(
        grants=[_grant(target_plan_row_id="PLAN-ROW-XYZ")],
        live_actors=[_live_parent()],
        row_id_filter="PLAN-ROW-XYZ",
        now=_NOW,
    )
    assert report["ok"] is True
    assert report["checked_grant_count"] == 1


def test_render_markdown_includes_violation_detail():
    report = guard.build_report(
        grants=[_grant(authority_refs=())],
        live_actors=[_live_parent()],
        now=_NOW,
    )
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert guard.RULE_MISSING_AUTHORITY_REFS in md
    assert "grant-A" in md
