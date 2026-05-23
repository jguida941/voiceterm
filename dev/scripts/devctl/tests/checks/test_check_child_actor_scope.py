"""Tests for `check_child_actor_scope` (A18 G33)."""

from __future__ import annotations

from dev.scripts.checks import check_child_actor_scope as guard


def _child_action_event(
    *,
    actor_id: str = "child-impl-A",
    role_id: str = "implementer",
    parent_role_occupancy_id: str = "parent-coord-1",
    action_kind: str = guard.ACTION_EDIT,
    target_paths: tuple[str, ...] = ("dev/sandbox/child_a/widget.py",),
    capability: str = "implementation.edit",
    target_ref: str = "plan:MP-ROW-A",
    plan_id: str = "MP-ROW-A",
    delegation: dict | None = None,
    actor_kind: str = "",
) -> dict[str, object]:
    event: dict[str, object] = {
        "event_type": guard.EVENT_CHILD_ACTION_ATTEMPTED,
        "event_id": f"evt-child-{actor_id}-{action_kind}",
        "actor_id": actor_id,
        "role_id": role_id,
        "parent_role_occupancy_id": parent_role_occupancy_id,
        "actor_kind": actor_kind,
        "action_kind": action_kind,
        "target_paths": list(target_paths),
        "capability": capability,
        "target_ref": target_ref,
        "plan_id": plan_id,
    }
    if delegation is not None:
        event["delegation"] = delegation
    else:
        event["delegation"] = {
            "delegation_id": "DEL-001",
            "plan_row_id": "MP-ROW-A",
            "allowed_paths": ["dev/sandbox/child_a/"],
            "allowed_capabilities": ["implementation.edit"],
        }
    return event


def test_green_edit_inside_delegated_scope_passes():
    report = guard.build_report(events=[_child_action_event()])
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["checked_event_count"] == 1
    assert report["checked_actor_ids"] == ["child-impl-A"]


def test_child_acted_outside_delegated_path():
    event = _child_action_event(
        target_paths=("dev/scripts/checks/check_role_lane_mutation_authority.py",),
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    assert report["violation_count"] == 1
    violation = report["violations"][0]
    assert violation["rule_id"] == guard.RULE_ACTED_OUTSIDE_DELEGATED_SCOPE
    assert violation["actor_id"] == "child-impl-A"
    assert violation["delegation_id"] == "DEL-001"


def test_child_capability_outside_delegated_capability_fails():
    event = _child_action_event(
        capability="repo.push",
        target_paths=("dev/sandbox/child_a/widget.py",),
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ACTED_OUTSIDE_DELEGATED_SCOPE in rules


def test_child_attempted_stage_without_authority_fails():
    event = _child_action_event(action_kind=guard.ACTION_STAGE)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_STAGE in rules


def test_child_attempted_commit_without_authority_fails():
    event = _child_action_event(action_kind=guard.ACTION_COMMIT)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_COMMIT in rules


def test_child_attempted_push_without_authority_fails():
    event = _child_action_event(action_kind=guard.ACTION_PUSH)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_PUSH in rules


def test_child_attempted_row_closure_fails():
    event = _child_action_event(action_kind=guard.ACTION_ROW_CLOSURE)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_ROW_CLOSURE in rules


def test_child_attempted_plan_row_mutation_fails():
    event = _child_action_event(action_kind=guard.ACTION_PLAN_ROW_MUTATION)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_PLAN_ROW_MUTATION in rules


def test_child_attempted_receipt_store_mutation_fails():
    event = _child_action_event(action_kind=guard.ACTION_RECEIPT_STORE_MUTATION)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_RECEIPT_STORE_MUTATION in rules


def test_child_attempted_generated_surface_rewrite_fails():
    event = _child_action_event(
        action_kind=guard.ACTION_GENERATED_SURFACE_REWRITE,
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_GENERATED_SURFACE_REWRITE in rules


def test_child_attempted_grand_child_spawn_without_authority_fails():
    event = _child_action_event(action_kind=guard.ACTION_SPAWN_CHILD)
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert (
        guard.RULE_CHILD_ATTEMPTED_GRAND_CHILD_SPAWN_WITHOUT_AUTHORITY in rules
    )


def test_explicit_delegation_authority_permits_stage_and_commit():
    delegation = {
        "delegation_id": "DEL-perm-stage",
        "plan_row_id": "MP-ROW-A",
        "allowed_paths": ["dev/sandbox/child_a/"],
        "allowed_capabilities": [
            "implementation.edit",
            "repo.stage",
            "repo.commit",
        ],
        "may_stage": True,
        "may_commit": True,
    }
    events = [
        _child_action_event(
            action_kind=guard.ACTION_STAGE,
            capability="repo.stage",
            delegation=delegation,
        ),
        _child_action_event(
            action_kind=guard.ACTION_COMMIT,
            capability="repo.commit",
            delegation=delegation,
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_explicit_delegation_authority_permits_grand_child_spawn():
    delegation = {
        "delegation_id": "DEL-perm-spawn",
        "plan_row_id": "MP-ROW-A",
        "allowed_paths": ["dev/sandbox/child_a/"],
        "allowed_capabilities": ["implementation.edit"],
        "may_spawn_grand_children": True,
    }
    event = _child_action_event(
        action_kind=guard.ACTION_SPAWN_CHILD,
        delegation=delegation,
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is True


def test_non_child_actor_event_ignored():
    event = _child_action_event(
        action_kind=guard.ACTION_COMMIT,
        parent_role_occupancy_id="",
        actor_kind="parent_role_coordinator",
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is True
    assert report["checked_event_count"] == 0


def test_actor_kind_subagent_treated_as_child():
    event = _child_action_event(
        action_kind=guard.ACTION_PUSH,
        parent_role_occupancy_id="",
        actor_kind="subagent",
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_PUSH in rules


def test_target_ref_mismatch_with_delegated_row_fails():
    delegation = {
        "delegation_id": "DEL-row-bound",
        "plan_row_id": "MP-ROW-A",
        "allowed_paths": ["dev/sandbox/child_a/"],
        "allowed_capabilities": ["implementation.edit"],
    }
    event = _child_action_event(
        target_ref="plan:OTHER-ROW",
        plan_id="OTHER-ROW",
        delegation=delegation,
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ACTED_OUTSIDE_DELEGATED_SCOPE in rules


def test_row_id_filter_limits_check():
    event_a = _child_action_event(
        action_kind=guard.ACTION_COMMIT,
        target_ref="plan:MP-ROW-FILTERED",
        plan_id="MP-ROW-FILTERED",
    )
    event_b = _child_action_event(
        action_kind=guard.ACTION_COMMIT,
        target_ref="plan:OTHER-ROW",
        plan_id="OTHER-ROW",
    )
    report = guard.build_report(
        events=[event_a, event_b],
        row_id_filter="MP-ROW-FILTERED",
    )
    assert report["ok"] is False
    assert report["checked_event_count"] == 1


def test_actor_id_filter_limits_check():
    event_a = _child_action_event(
        actor_id="child-impl-A",
        action_kind=guard.ACTION_COMMIT,
    )
    event_b = _child_action_event(
        actor_id="child-impl-B",
        action_kind=guard.ACTION_COMMIT,
    )
    report = guard.build_report(
        events=[event_a, event_b],
        actor_id_filter=("child-impl-A",),
    )
    assert report["ok"] is False
    assert report["checked_actor_ids"] == ["child-impl-A"]
    assert report["checked_event_count"] == 1


def test_multiple_violations_in_single_event():
    delegation = {
        "delegation_id": "DEL-tight",
        "plan_row_id": "MP-ROW-A",
        "allowed_paths": ["dev/sandbox/child_a/"],
        "allowed_capabilities": ["implementation.edit"],
    }
    # Commit AND outside-scope paths -> both rules should fire.
    event = _child_action_event(
        action_kind=guard.ACTION_COMMIT,
        capability="repo.commit",
        target_paths=("dev/scripts/devctl/runtime/scope_path_claims.py",),
        delegation=delegation,
    )
    report = guard.build_report(events=[event])
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CHILD_ATTEMPTED_COMMIT in rules
    assert guard.RULE_ACTED_OUTSIDE_DELEGATED_SCOPE in rules


def test_render_markdown_lists_violations():
    event = _child_action_event(action_kind=guard.ACTION_PUSH)
    report = guard.build_report(events=[event])
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "child-impl-A" in md
    assert guard.RULE_CHILD_ATTEMPTED_PUSH in md


def test_render_markdown_clean_report_omits_violations_section():
    report = guard.build_report(events=[_child_action_event()])
    md = guard.render_markdown(report)
    assert "## Violations" not in md
    assert "ok: True" in md


def test_unrelated_event_type_ignored():
    event = {
        "event_type": "packet_posted",
        "packet_id": "rev_pkt_X",
        "actor_id": "child-impl-A",
        "action_kind": guard.ACTION_COMMIT,
        "parent_role_occupancy_id": "parent-coord-1",
    }
    report = guard.build_report(events=[event])
    assert report["ok"] is True
    assert report["checked_event_count"] == 0


def test_empty_action_kind_skipped():
    event = _child_action_event(action_kind="")
    report = guard.build_report(events=[event])
    assert report["ok"] is True
    assert report["checked_event_count"] == 1


def test_missing_event_log_emits_warning_but_passes():
    report = guard.build_report(
        event_log_path=(
            guard._default_event_log_path().parent / "no-such-file.ndjson"
        ),
    )
    assert report["ok"] is True
    assert any("event log missing" in w for w in report["warnings"])
