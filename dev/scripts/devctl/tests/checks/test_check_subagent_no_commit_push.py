"""Tests for `check_subagent_no_commit_push` (A18 G39)."""

from __future__ import annotations

from dev.scripts.checks import check_subagent_no_commit_push as guard


def _subagent_action(
    *,
    attempt_id: str,
    action_kind: str = guard.ACTION_KIND_COMMIT,
    child_actor_id: str = "implementation.worker.runtime",
    parent_role_occupancy_id: str = "occ-implementation-lead-1",
    route_kind: str = "",
    authority_refs: tuple[str, ...] = (),
    authority_source: str = "",
    target_plan_row_id: str = "MP-ROW-A",
    is_subagent: bool = True,
    remote_control_as_authority: bool = False,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "attempt_id": attempt_id,
        "action_kind": action_kind,
        "child_actor_id": child_actor_id,
        "parent_role_occupancy_id": parent_role_occupancy_id,
        "route_kind": route_kind,
        "authority_refs": list(authority_refs),
        "authority_source": authority_source,
        "target_plan_row_id": target_plan_row_id,
        "is_subagent": is_subagent,
        "remote_control_as_authority": remote_control_as_authority,
    }
    if extra:
        payload.update(extra)
    return payload


def test_green_no_subagent_attempts():
    report = guard.build_report(actions=[])
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["checked_attempt_count"] == 0


def test_subagent_attempted_commit_without_route_fails():
    actions = [
        _subagent_action(
            attempt_id="att-commit-1",
            action_kind=guard.ACTION_KIND_COMMIT,
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_COMMIT in rules


def test_subagent_attempted_push_without_route_fails():
    actions = [
        _subagent_action(
            attempt_id="att-push-1",
            action_kind=guard.ACTION_KIND_PUSH,
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_PUSH in rules


def test_subagent_attempted_row_closure_without_route_fails():
    actions = [
        _subagent_action(
            attempt_id="att-row-1",
            action_kind=guard.ACTION_KIND_ROW_CLOSURE,
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_ROW_CLOSURE in rules


def test_subagent_attempted_generated_surface_rewrite_fails():
    actions = [
        _subagent_action(
            attempt_id="att-surface-1",
            action_kind=guard.ACTION_KIND_GENERATED_SURFACE_REWRITE,
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_GENERATED_SURFACE_REWRITE in rules


def test_subagent_attempted_receipt_store_mutation_fails():
    actions = [
        _subagent_action(
            attempt_id="att-receipt-1",
            action_kind=guard.ACTION_KIND_RECEIPT_STORE_MUTATION,
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_RECEIPT_STORE_MUTATION in rules


def test_remote_control_treated_as_authority_fails():
    actions = [
        _subagent_action(
            attempt_id="att-rc-1",
            action_kind=guard.ACTION_KIND_COMMIT,
            authority_source="remote_control",
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REMOTE_CONTROL_TREATED_AS_AUTHORITY in rules


def test_remote_control_flag_treated_as_authority_fails():
    actions = [
        _subagent_action(
            attempt_id="att-rc-2",
            action_kind=guard.ACTION_KIND_PUSH,
            remote_control_as_authority=True,
        )
    ]
    report = guard.build_report(actions=actions)
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REMOTE_CONTROL_TREATED_AS_AUTHORITY in rules


def test_governed_parent_route_with_authority_passes():
    actions = [
        _subagent_action(
            attempt_id="att-ok-1",
            action_kind=guard.ACTION_KIND_COMMIT,
            route_kind="parent_role_coordinator",
            authority_refs=("RoleOccupancyAssignment:occ-impl-lead-1",),
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_governed_push_adapter_route_passes():
    actions = [
        _subagent_action(
            attempt_id="att-ok-2",
            action_kind=guard.ACTION_KIND_PUSH,
            route_kind="governed_push_adapter",
            authority_refs=("PushAuthorizationRecord:push-001",),
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is True


def test_remote_control_transport_label_is_not_authority_violation():
    # Remote control labeled as transport/routing is the correct framing and
    # must not trip the authority rule.
    actions = [
        _subagent_action(
            attempt_id="att-rc-transport-1",
            action_kind=guard.ACTION_KIND_COMMIT,
            authority_source="remote_control_transport",
            route_kind="parent_role_coordinator",
            authority_refs=("RoleOccupancyAssignment:occ-impl-lead-1",),
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is True
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REMOTE_CONTROL_TREATED_AS_AUTHORITY not in rules


def test_route_without_authority_refs_still_fails():
    # A sanctioned route name without typed authority_refs is not proof of
    # the typed parent/transport/approval chain.
    actions = [
        _subagent_action(
            attempt_id="att-empty-refs-1",
            action_kind=guard.ACTION_KIND_COMMIT,
            route_kind="parent_role_coordinator",
            authority_refs=(),
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_COMMIT in rules


def test_non_subagent_actor_is_skipped():
    # A parent-role actor (not a child/sub-agent) is out of scope for this
    # guard; G33/G36 cover other lanes.
    actions = [
        {
            "attempt_id": "att-parent-1",
            "action_kind": guard.ACTION_KIND_COMMIT,
            "actor_id": "implementation_lead",
            "is_subagent": False,
            "is_child_actor": False,
        }
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["checked_attempt_count"] == 1


def test_row_id_filter_excludes_other_rows():
    actions = [
        _subagent_action(
            attempt_id="att-other-row",
            action_kind=guard.ACTION_KIND_COMMIT,
            target_plan_row_id="MP-ROW-OTHER",
        )
    ]
    report = guard.build_report(actions=actions, row_id_filter="MP-ROW-A")
    assert report["ok"] is True
    assert report["checked_attempt_count"] == 0


def test_row_id_filter_includes_matching_row():
    actions = [
        _subagent_action(
            attempt_id="att-matching-row",
            action_kind=guard.ACTION_KIND_COMMIT,
            target_plan_row_id="MP-ROW-A",
        )
    ]
    report = guard.build_report(actions=actions, row_id_filter="MP-ROW-A")
    assert report["ok"] is False
    assert report["checked_attempt_count"] == 1


def test_git_commit_alias_normalized():
    actions = [
        _subagent_action(
            attempt_id="att-git-commit-1",
            action_kind="git_commit",
        )
    ]
    report = guard.build_report(actions=actions)
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SUBAGENT_ATTEMPTED_COMMIT in rules


def test_unknown_action_kind_does_not_fail_unless_remote_control():
    # Unknown action kinds are not in scope for the five enumerated rules,
    # but a remote-control-as-authority claim must still surface.
    actions = [
        _subagent_action(
            attempt_id="att-unknown-1",
            action_kind="emit_status_heartbeat",
            authority_source="remote_control_authority",
        )
    ]
    report = guard.build_report(actions=actions)
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REMOTE_CONTROL_TREATED_AS_AUTHORITY in rules
    # The unknown kind itself should not trigger a per-kind violation.
    per_kind_rules = rules & set(guard._ACTION_KIND_TO_RULE.values())
    assert not per_kind_rules


def test_render_markdown_includes_violations():
    actions = [
        _subagent_action(
            attempt_id="att-md-1",
            action_kind=guard.ACTION_KIND_COMMIT,
        )
    ]
    report = guard.build_report(actions=actions)
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "att-md-1" in md
    assert guard.RULE_SUBAGENT_ATTEMPTED_COMMIT in md
