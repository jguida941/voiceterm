"""Tests for `check_write_lease_conflicts` (A18 G32).

Per delete_after_ingest.md A18, the guard fails closed when two live
mutation-capable actors hold overlapping write scope for the same
PlanRow/path/file/symbol/worktree/branch/receipt target/packet target unless a
typed merge coordinator explicitly owns the conflict.

The tests below pin one RED+GREEN pair per scope dimension plus a few
explicit merge-coordinator scenarios so the typed-coordinator escape hatch is
behaviorally specified.
"""

from __future__ import annotations

from typing import Any

from dev.scripts.checks import check_write_lease_conflicts as guard


_PLAN_ROW = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _lease(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "actor_id": "codex",
        "role_id": "implementer",
        "state": "live",
        "mutation_capable": True,
        "plan_row_id": _PLAN_ROW,
        "path_scope": [],
        "file_scope": [],
        "symbol_scope": [],
        "receipt_scope": [],
        "packet_scope": [],
        "worktree_identity": "",
        "branch_identity": "",
        "merge_coordinator_id": "",
    }
    payload.update(overrides)
    return payload


def _rule_ids(report: dict[str, Any]) -> set[str]:
    return {str(v["rule_id"]) for v in report["violations"]}


def test_green_disjoint_path_scope_passes():
    leases = [
        _lease(actor_id="codex", path_scope=["dev/scripts/devctl/runtime/a.py"]),
        _lease(actor_id="claude", path_scope=["dev/scripts/devctl/runtime/b.py"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is True
    assert report["live_mutation_capable_count"] == 2
    assert report["violations"] == []


def test_red_overlapping_path_lease_fails():
    leases = [
        _lease(actor_id="codex", path_scope=["dev/scripts/devctl/runtime/"]),
        _lease(actor_id="claude", path_scope=["dev/scripts/devctl/runtime/foo.py"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_PATH_LEASE in _rule_ids(report)
    violation = next(
        v for v in report["violations"]
        if v["rule_id"] == guard.RULE_OVERLAPPING_PATH_LEASE
    )
    assert {violation["left_actor_id"], violation["right_actor_id"]} == {"codex", "claude"}


def test_red_overlapping_file_lease_fails():
    leases = [
        _lease(actor_id="codex", file_scope=["foo.py"]),
        _lease(actor_id="claude", file_scope=["foo.py"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_FILE_LEASE in _rule_ids(report)


def test_red_overlapping_symbol_lease_fails():
    leases = [
        _lease(actor_id="codex", symbol_scope=["module.func_x"]),
        _lease(actor_id="claude", symbol_scope=["module.func_x"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_SYMBOL_LEASE in _rule_ids(report)


def test_red_overlapping_worktree_lease_fails():
    leases = [
        _lease(actor_id="codex", worktree_identity="wt-A"),
        _lease(actor_id="claude", worktree_identity="wt-A"),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_WORKTREE_LEASE in _rule_ids(report)


def test_green_disjoint_worktree_passes():
    leases = [
        _lease(actor_id="codex", worktree_identity="wt-A"),
        _lease(actor_id="claude", worktree_identity="wt-B"),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is True


def test_red_overlapping_branch_lease_fails():
    leases = [
        _lease(actor_id="codex", branch_identity="feature/x"),
        _lease(actor_id="claude", branch_identity="feature/x"),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_BRANCH_LEASE in _rule_ids(report)


def test_red_overlapping_receipt_lease_fails():
    leases = [
        _lease(
            actor_id="codex",
            receipt_scope=["dev/state/plan_row_closure_receipts.jsonl"],
        ),
        _lease(
            actor_id="claude",
            receipt_scope=["dev/state/plan_row_closure_receipts.jsonl"],
        ),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_RECEIPT_LEASE in _rule_ids(report)


def test_red_overlapping_packet_lease_fails():
    leases = [
        _lease(actor_id="codex", packet_scope=["rev_pkt_4810"]),
        _lease(actor_id="claude", packet_scope=["rev_pkt_4810"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_PACKET_LEASE in _rule_ids(report)


def test_green_merge_coordinator_owns_path_conflict_passes():
    leases = [
        _lease(
            actor_id="codex",
            path_scope=["dev/scripts/devctl/runtime/foo.py"],
            merge_coordinator_id="coord-1",
        ),
        _lease(
            actor_id="claude",
            path_scope=["dev/scripts/devctl/runtime/foo.py"],
            merge_coordinator_id="coord-1",
        ),
    ]
    coords = [
        {
            "coordinator_id": "coord-1",
            "conflict_id": "conflict-A",
            "scope_dimension": "path_scope",
            "scope_values": ["dev/scripts/devctl/runtime/foo.py"],
            "owned_actor_ids": ["codex", "claude"],
        }
    ]
    report = guard.build_report(leases=leases, merge_coordinators=coords)
    assert report["ok"] is True
    assert report["violations"] == []


def test_red_merge_coordinator_missing_actor_does_not_excuse_conflict():
    leases = [
        _lease(
            actor_id="codex",
            path_scope=["dev/scripts/devctl/runtime/foo.py"],
            merge_coordinator_id="coord-1",
        ),
        _lease(
            actor_id="claude",
            path_scope=["dev/scripts/devctl/runtime/foo.py"],
            merge_coordinator_id="coord-1",
        ),
    ]
    # Coordinator names only one of the colliding actors → still overlap.
    coords = [
        {
            "coordinator_id": "coord-1",
            "conflict_id": "conflict-A",
            "scope_dimension": "path_scope",
            "scope_values": ["dev/scripts/devctl/runtime/foo.py"],
            "owned_actor_ids": ["codex"],
        }
    ]
    report = guard.build_report(leases=leases, merge_coordinators=coords)
    assert report["ok"] is False
    assert guard.RULE_OVERLAPPING_PATH_LEASE in _rule_ids(report)


def test_red_dangling_merge_coordinator_reference_fails():
    leases = [
        _lease(
            actor_id="codex",
            path_scope=["dev/scripts/devctl/runtime/a.py"],
            merge_coordinator_id="coord-ghost",
        ),
        _lease(
            actor_id="claude",
            path_scope=["dev/scripts/devctl/runtime/b.py"],
            merge_coordinator_id="",
        ),
    ]
    report = guard.build_report(leases=leases, merge_coordinators=[])
    assert report["ok"] is False
    assert guard.RULE_NO_TYPED_MERGE_COORDINATOR in _rule_ids(report)


def test_green_idle_actor_is_not_live_mutation_capable():
    leases = [
        _lease(actor_id="codex", state="live", path_scope=["dev/foo.py"]),
        _lease(actor_id="claude", state="idle", path_scope=["dev/foo.py"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is True
    assert report["live_mutation_capable_count"] == 1


def test_green_non_mutation_capable_actor_excluded():
    leases = [
        _lease(actor_id="codex", path_scope=["dev/foo.py"]),
        _lease(
            actor_id="observer",
            mutation_capable=False,
            path_scope=["dev/foo.py"],
        ),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is True
    assert report["live_mutation_capable_count"] == 1


def test_red_three_actor_overlap_emits_pairwise_violations():
    leases = [
        _lease(actor_id="codex", path_scope=["dev/scripts/devctl/runtime/foo.py"]),
        _lease(actor_id="claude", path_scope=["dev/scripts/devctl/runtime/foo.py"]),
        _lease(actor_id="ralph", path_scope=["dev/scripts/devctl/runtime/foo.py"]),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is False
    path_violations = [
        v for v in report["violations"]
        if v["rule_id"] == guard.RULE_OVERLAPPING_PATH_LEASE
    ]
    # Three pairwise overlaps: codex-claude, codex-ralph, claude-ralph.
    assert len(path_violations) == 3


def test_green_disjoint_branches_pass_even_with_shared_worktree_role():
    leases = [
        _lease(
            actor_id="codex",
            branch_identity="feature/codex",
            worktree_identity="wt-A",
        ),
        _lease(
            actor_id="claude",
            branch_identity="feature/claude",
            worktree_identity="wt-B",
        ),
    ]
    report = guard.build_report(leases=leases)
    assert report["ok"] is True


def test_main_cli_reads_inventory_and_returns_nonzero_on_overlap(tmp_path):
    import json

    inventory = {
        "leases": [
            _lease(actor_id="codex", file_scope=["x.py"]),
            _lease(actor_id="claude", file_scope=["x.py"]),
        ],
        "merge_coordinators": [],
    }
    inventory_path = tmp_path / "leases.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    rc = guard.main(
        [
            "--lease-inventory-path",
            str(inventory_path),
            "--format",
            "json",
        ]
    )
    assert rc == 1


def test_main_cli_returns_zero_on_disjoint_leases(tmp_path):
    import json

    inventory = {
        "leases": [
            _lease(actor_id="codex", file_scope=["a.py"]),
            _lease(actor_id="claude", file_scope=["b.py"]),
        ],
        "merge_coordinators": [],
    }
    inventory_path = tmp_path / "leases.json"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    rc = guard.main(
        [
            "--lease-inventory-path",
            str(inventory_path),
            "--format",
            "json",
        ]
    )
    assert rc == 0
