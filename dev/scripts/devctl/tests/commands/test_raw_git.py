import json
from argparse import Namespace
from pathlib import Path

from dev.scripts.devctl.commands.raw_git import (
    GitCommandResult,
    run_raw_git_action,
)
from dev.scripts.devctl.runtime.governed_exception_store import (
    load_governed_exception_lifecycles,
)
from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FeatureProofReceipt,
    feature_proof_receipt_artifact_relpath,
    feature_proof_receipt_from_mapping,
)
from dev.scripts.devctl.runtime.commit_to_plan_row_reducer import (
    DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL,
    reduce_feature_proof_to_plan_rows,
)
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow
from dev.scripts.devctl.runtime.master_plan_store import (
    read_plan_rows_jsonl,
    write_plan_rows_jsonl,
)
from dev.scripts.devctl.runtime.raw_git_bypass_receipts import (
    read_raw_git_bypass_receipts,
)


def _real_test_ref(repo_root: Path, test_name: str = "test_raw_git_real_proof") -> str:
    path = repo_root / "dev/scripts/devctl/tests/commands/test_raw_git.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"def {test_name}():\n    assert True\n", encoding="utf-8")
    return f"{path.relative_to(repo_root)}::{test_name}"


def test_raw_git_commit_wrapper_emits_receipt(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []
    state = {"committed": False}
    real_test_ref = _real_test_ref(tmp_path, "test_raw_git_commit_wrapper_emits_receipt")

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        calls.append(args)
        if args == ("rev-parse", "HEAD"):
            return GitCommandResult(0, "abc123\n" if state["committed"] else "base\n", "")
        if args == ("rev-parse", "--verify", "@{u}"):
            return GitCommandResult(1, "", "no upstream")
        if args == ("commit", "--no-verify", "-m", "slice"):
            state["committed"] = True
            return GitCommandResult(0, "committed\n", "")
        if args == ("diff-tree", "--no-commit-id", "--name-only", "-r", "abc123"):
            return GitCommandResult(0, "dev/scripts/devctl.py\n", "")
        return GitCommandResult(1, "", "not found")

    args = Namespace(
        raw_git_action="commit",
        git_args=["--no-verify", "-m", "slice"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=["packet:rev_pkt_4022"],
        feature_id="MP-NEW-P207-FEATURE-PROOF-RECEIPT-EMISSION-S2",
        test_command=[real_test_ref],
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guard=["check_feature_has_proof_receipt"],
        connectivity_guards_passed="true",
        dogfood_evidence_ref=real_test_ref,
        review_fleet_role=["FeatureLifecycleProof"],
        review_fleet_actor="claude",
        real_life_test_status="proven_passed",
        not_tested_rationale="",
        evidence_artifact=["dev/state/raw_git_bypass_receipts.jsonl"],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 0
    assert report["ok"] is True
    assert ("commit", "--no-verify", "-m", "slice") in calls
    receipts = read_raw_git_bypass_receipts(
        tmp_path / "dev/state/raw_git_bypass_receipts.jsonl"
    )
    assert len(receipts) == 1
    assert receipts[0].commit_sha == "abc123"
    assert receipts[0].governed_exception_id.startswith("gel:raw-git:commit:")
    assert receipts[0].skipped_pre_hooks == ("pre-commit", "commit-msg")
    assert receipts[0].operator_quote_evidence_ref == "packet:rev_pkt_4022"
    exceptions = load_governed_exception_lifecycles(
        tmp_path / "dev/state/governed_exception_lifecycles.jsonl"
    )
    assert exceptions[0].lifecycle_id == receipts[0].governed_exception_id
    proof_path = tmp_path / feature_proof_receipt_artifact_relpath("abc123")
    proof = feature_proof_receipt_from_mapping(
        json.loads(proof_path.read_text(encoding="utf-8"))
    )
    assert proof.feature_id == "MP-NEW-P207-FEATURE-PROOF-RECEIPT-EMISSION-S2"
    assert proof.commit_sha == "abc123"
    assert proof.real_life_test_status == "proven_passed"
    assert proof.connectivity_guards_passed is True
    assert f"raw_git_bypass_receipt:{receipts[0].receipt_id}" in proof.bypass_audit_trail_refs


def test_raw_git_commit_wrapper_validates_lifecycle_before_git(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        calls.append(args)
        return GitCommandResult(0, "", "")

    args = Namespace(
        raw_git_action="commit",
        git_args=["-m", "slice"],
        actor="codex",
        authority="bypass_lifecycle_receipt",
        bypass_lifecycle_id="gel:bypass:fabricated",
        operator_quote_evidence_ref=["packet:rev_pkt_4022"],
        feature_id="MP-NEW-P207-FEATURE-PROOF-RECEIPT-EMISSION-S2",
        test_command=[],
        tests_passed_count=0,
        tests_failed_count=0,
        connectivity_guard=[],
        connectivity_guards_passed="true",
        dogfood_evidence_ref="",
        review_fleet_role=[],
        review_fleet_actor="claude",
        real_life_test_status="not_tested_with_rationale",
        not_tested_rationale="preflight failure",
        evidence_artifact=[],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 1
    assert report["ok"] is False
    assert report["reason"] == "bypass_authority_invalid"
    assert calls == []


def test_raw_git_commit_wrapper_records_raw_commit_when_hook_advances_head(
    tmp_path: Path,
) -> None:
    state = {"committed": False}
    real_test_ref = _real_test_ref(
        tmp_path,
        "test_raw_git_commit_wrapper_records_raw_commit_when_hook_advances_head",
    )

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        if args == ("rev-parse", "HEAD"):
            return GitCommandResult(0, "snapshot456\n" if state["committed"] else "base\n", "")
        if args == ("rev-parse", "--verify", "@{u}"):
            return GitCommandResult(1, "", "no upstream")
        if args == ("commit", "--no-verify", "-m", "slice"):
            state["committed"] = True
            return GitCommandResult(0, "committed\n", "")
        if args == ("rev-list", "--reverse", "base..snapshot456"):
            return GitCommandResult(0, "raw123\nsnapshot456\n", "")
        if args == ("diff-tree", "--no-commit-id", "--name-only", "-r", "raw123"):
            return GitCommandResult(0, "dev/state/plan_index.jsonl\n", "")
        return GitCommandResult(1, "", "not found")

    args = Namespace(
        raw_git_action="commit",
        git_args=["--no-verify", "-m", "slice"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=["packet:rev_pkt_4026"],
        feature_id="",
        test_command=[real_test_ref],
        tests_passed_count=1,
        tests_failed_count=None,
        connectivity_guard=["check_non_trivial_output_proof"],
        connectivity_guards_passed="true",
        dogfood_evidence_ref=real_test_ref,
        review_fleet_role=[],
        review_fleet_actor="raw-git-wrapper",
        real_life_test_status="",
        not_tested_rationale="",
        evidence_artifact=[],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 0
    assert report["ok"] is True
    receipts = read_raw_git_bypass_receipts(
        tmp_path / "dev/state/raw_git_bypass_receipts.jsonl"
    )
    assert receipts[0].commit_sha == "raw123"
    assert receipts[0].affected_paths == ("dev/state/plan_index.jsonl",)
    proof_path = tmp_path / feature_proof_receipt_artifact_relpath("raw123")
    assert proof_path.exists()


def test_raw_git_commit_wrapper_transitions_plan_rows_to_applied(
    tmp_path: Path,
) -> None:
    first_row = "MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1"
    second_row = "MP-NEW-P220-P40-TYPED-DISPOSITION-S3"
    plan_index_path = tmp_path / "dev/state/plan_index.jsonl"
    write_plan_rows_jsonl(
        plan_index_path,
        (
            PlanRow(
                row_id=first_row,
                title="Close feature rows from raw git",
                status="queued",
                sdlc_stage="impl",
                anchor_refs=("packet:rev_pkt_4147",),
            ),
            PlanRow(
                row_id=second_row,
                title="Close secondary row from commit body",
                status="in_progress",
                sdlc_stage="impl",
            ),
        ),
    )
    state = {"committed": False}
    real_test_ref = _real_test_ref(
        tmp_path,
        "test_raw_git_commit_wrapper_transitions_plan_rows_to_applied",
    )

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        if args == ("rev-parse", "HEAD"):
            return GitCommandResult(0, "abc123\n" if state["committed"] else "base\n", "")
        if args == ("rev-parse", "--verify", "@{u}"):
            return GitCommandResult(1, "", "no upstream")
        if args == ("commit", "--no-verify", "-m", "slice"):
            state["committed"] = True
            return GitCommandResult(0, "committed\n", "")
        if args == ("rev-list", "--reverse", "base..abc123"):
            return GitCommandResult(0, "abc123\n", "")
        if args == ("diff-tree", "--no-commit-id", "--name-only", "-r", "abc123"):
            return GitCommandResult(0, "dev/scripts/devctl/commands/raw_git.py\n", "")
        if args == ("log", "-1", "--format=%B", "abc123"):
            return GitCommandResult(
                0,
                (
                    f"{first_row}: add reducer\n\n"
                    f"Plan-Row: {second_row}\n"
                    "Packet: rev_pkt_4147\n"
                ),
                "",
            )
        return GitCommandResult(1, "", "not found")

    args = Namespace(
        raw_git_action="commit",
        git_args=["--no-verify", "-m", "slice"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=["packet:rev_pkt_4147"],
        feature_id="",
        test_command=[real_test_ref],
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guard=["check_feature_has_proof_receipt"],
        connectivity_guards_passed="true",
        dogfood_evidence_ref=real_test_ref,
        review_fleet_role=["FeatureLifecycleProof"],
        review_fleet_actor="claude",
        real_life_test_status="proven_passed",
        not_tested_rationale="",
        evidence_artifact=["dev/state/plan_index.jsonl"],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 0
    assert report["ok"] is True
    rows = {row.row_id: row for row in read_plan_rows_jsonl(plan_index_path)}
    for row_id in (first_row, second_row):
        row = rows[row_id]
        assert row.status == "applied"
        assert row.commit_anchor_ref == "commit:abc123"
        assert row.applied_at_utc
        assert "commit:abc123" in row.anchor_refs
        assert (
            "feature_proof_receipt:"
            + feature_proof_receipt_artifact_relpath("abc123")
        ) in row.work_evidence_ids
    receipt_store = tmp_path / DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL
    receipt_lines = receipt_store.read_text(encoding="utf-8").splitlines()
    assert len(receipt_lines) == 2
    assert all("transitioned_to_applied" in line for line in receipt_lines)


def test_commit_to_plan_row_reducer_skips_noop_receipt_for_applied_row(
    tmp_path: Path,
) -> None:
    row_id = "MP-NEW-P229-COMMIT-TO-PLAN-ROW-REDUCER-S1"
    plan_index_path = tmp_path / "dev/state/plan_index.jsonl"
    write_plan_rows_jsonl(
        plan_index_path,
        (
            PlanRow(
                row_id=row_id,
                title="Already closed row",
                status="applied",
                sdlc_stage="impl",
                commit_anchor_ref="commit:first",
                applied_at_utc="2026-05-16T00:31:01Z",
                anchor_refs=("commit:first",),
                work_evidence_ids=("feature_proof_receipt:first.json",),
            ),
        ),
    )
    feature_proof = FeatureProofReceipt(
        feature_id=row_id,
        commit_sha="second",
        implementer_actor="codex",
        review_fleet_roles_ran=("FeatureLifecycleProof",),
        review_fleet_actor="claude",
        tests_run=("pytest",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_feature_has_proof_receipt",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="test:already-applied-row",
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=("raw_git_bypass_receipt:receipt",),
        proven_at_utc="2026-05-16T00:32:01Z",
        evidence_artifacts=("dev/state/plan_index.jsonl",),
    )

    results = reduce_feature_proof_to_plan_rows(
        repo_root=tmp_path,
        feature_proof=feature_proof,
        feature_ids=(row_id,),
        feature_proof_receipt_path="dev/reports/feature_proof_receipts/second.json",
    )

    assert len(results) == 1
    assert results[0].outcome == "already_applied"
    assert results[0].changed is False
    assert not (tmp_path / DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL).exists()
    row = read_plan_rows_jsonl(plan_index_path)[0]
    assert row.commit_anchor_ref == "commit:first"
    assert row.anchor_refs == ("commit:first",)
    assert row.work_evidence_ids == ("feature_proof_receipt:first.json",)


def test_raw_git_commit_wrapper_fails_closed_on_trivial_feature_proof(
    tmp_path: Path,
) -> None:
    state = {"committed": False}

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        if args == ("rev-parse", "HEAD"):
            return GitCommandResult(0, "abc123\n" if state["committed"] else "base\n", "")
        if args == ("rev-parse", "--verify", "@{u}"):
            return GitCommandResult(1, "", "no upstream")
        if args == ("commit", "--no-verify", "-m", "slice"):
            state["committed"] = True
            return GitCommandResult(0, "committed\n", "")
        if args == ("rev-list", "--reverse", "base..abc123"):
            return GitCommandResult(0, "abc123\n", "")
        if args == ("diff-tree", "--no-commit-id", "--name-only", "-r", "abc123"):
            return GitCommandResult(0, "dev/scripts/devctl.py\n", "")
        return GitCommandResult(1, "", "not found")

    args = Namespace(
        raw_git_action="commit",
        git_args=["--no-verify", "-m", "slice"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=["packet:rev_pkt_4022"],
        feature_id="MP-NEW-P207-S4",
        test_command=["python3 dev/scripts/devctl.py test-python"],
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guard=["check_feature_has_proof_receipt"],
        connectivity_guards_passed="true",
        dogfood_evidence_ref="test:raw-git-wrapper",
        review_fleet_role=["FeatureLifecycleProof"],
        review_fleet_actor="claude",
        real_life_test_status="proven_passed",
        not_tested_rationale="",
        evidence_artifact=["dev/state/raw_git_bypass_receipts.jsonl"],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 1
    assert report["ok"] is False
    assert "non_trivial_output_proof_ref_failure" in str(report["error"])
    assert "no_real_tests" in str(report["error"])
    assert not (tmp_path / feature_proof_receipt_artifact_relpath("abc123")).exists()


def test_raw_git_commit_wrapper_fails_closed_when_feature_proof_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state = {"committed": False}
    real_test_ref = _real_test_ref(
        tmp_path,
        "test_raw_git_commit_wrapper_fails_closed_when_feature_proof_write_fails",
    )

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        if args == ("rev-parse", "HEAD"):
            return GitCommandResult(0, "abc123\n" if state["committed"] else "base\n", "")
        if args == ("rev-parse", "--verify", "@{u}"):
            return GitCommandResult(1, "", "no upstream")
        if args == ("commit", "--no-verify", "-m", "slice"):
            state["committed"] = True
            return GitCommandResult(0, "committed\n", "")
        if args == ("rev-list", "--reverse", "base..abc123"):
            return GitCommandResult(0, "abc123\n", "")
        if args == ("diff-tree", "--no-commit-id", "--name-only", "-r", "abc123"):
            return GitCommandResult(0, "dev/scripts/devctl.py\n", "")
        return GitCommandResult(1, "", "not found")

    def fail_write(*_args, **_kwargs) -> str:
        raise OSError("feature proof store unavailable")

    monkeypatch.setattr(
        "dev.scripts.devctl.commands.raw_git.write_feature_proof_receipt_artifact",
        fail_write,
    )
    args = Namespace(
        raw_git_action="commit",
        git_args=["--no-verify", "-m", "slice"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=["packet:rev_pkt_4022"],
        feature_id="MP-NEW-P207-S4",
        test_command=[real_test_ref],
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guard=["check_feature_has_proof_receipt"],
        connectivity_guards_passed="true",
        dogfood_evidence_ref=real_test_ref,
        review_fleet_role=["FeatureLifecycleProof"],
        review_fleet_actor="claude",
        real_life_test_status="proven_passed",
        not_tested_rationale="",
        evidence_artifact=["dev/state/raw_git_bypass_receipts.jsonl"],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 1
    assert report["ok"] is False
    assert report["reason"] == "feature_proof_receipt_write_failed"
    assert "feature proof store unavailable" in str(report["error"])
    receipts = read_raw_git_bypass_receipts(
        tmp_path / "dev/state/raw_git_bypass_receipts.jsonl"
    )
    assert len(receipts) == 1
    assert receipts[0].commit_sha == "abc123"
    assert not (tmp_path / feature_proof_receipt_artifact_relpath("abc123")).exists()


def test_raw_git_push_wrapper_records_push_range(tmp_path: Path) -> None:
    state = {"pushed": False}
    real_test_ref = _real_test_ref(tmp_path, "test_raw_git_push_wrapper_records_push_range")

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        if args == ("rev-parse", "HEAD"):
            return GitCommandResult(0, "head\n", "")
        if args == ("rev-parse", "--verify", "@{u}"):
            return GitCommandResult(0, "base\n", "")
        if args == ("rev-list", "--reverse", "@{u}..HEAD"):
            return GitCommandResult(0, "" if state["pushed"] else "head\n", "")
        if args == ("push", "--no-verify"):
            state["pushed"] = True
            return GitCommandResult(0, "pushed\n", "")
        if args == ("diff", "--name-only", "base..head"):
            return GitCommandResult(0, "dev/state/plan_index.jsonl\n", "")
        return GitCommandResult(1, "", "not found")

    args = Namespace(
        raw_git_action="push",
        git_args=["--no-verify"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=["packet:rev_pkt_4021", "packet:rev_pkt_4022"],
        feature_id="MP-NEW-P207-FEATURE-PROOF-RECEIPT-EMISSION-S2",
        test_command=[real_test_ref],
        tests_passed_count=1,
        tests_failed_count=None,
        connectivity_guard=["check_non_trivial_output_proof"],
        connectivity_guards_passed="true",
        dogfood_evidence_ref=real_test_ref,
        review_fleet_role=[],
        review_fleet_actor="raw-git-wrapper",
        real_life_test_status="",
        not_tested_rationale="",
        evidence_artifact=[],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 0
    assert report["ok"] is True
    receipts = read_raw_git_bypass_receipts(
        tmp_path / "dev/state/raw_git_bypass_receipts.jsonl"
    )
    assert receipts[0].push_range == ("base", "head")
    assert receipts[0].skipped_pre_hooks == ("pre-push",)
    assert receipts[0].affected_paths == ("dev/state/plan_index.jsonl",)
    assert receipts[0].operator_quote_evidence_ref == "packet:rev_pkt_4022"
    proof_path = tmp_path / feature_proof_receipt_artifact_relpath("head")
    proof = feature_proof_receipt_from_mapping(
        json.loads(proof_path.read_text(encoding="utf-8"))
    )
    assert proof.commit_sha == "head"
    assert f"raw_git_bypass_receipt:{receipts[0].receipt_id}" in proof.bypass_audit_trail_refs


def test_raw_git_wrapper_does_not_emit_receipt_when_git_fails(tmp_path: Path) -> None:
    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        if args == ("commit", "--no-verify", "-m", "slice"):
            return GitCommandResult(1, "", "commit failed")
        return GitCommandResult(1, "", "not found")

    args = Namespace(
        raw_git_action="commit",
        git_args=["--no-verify", "-m", "slice"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=[],
        feature_id="",
        test_command=[],
        tests_passed_count=None,
        tests_failed_count=None,
        connectivity_guard=[],
        connectivity_guards_passed="true",
        dogfood_evidence_ref="",
        review_fleet_role=[],
        review_fleet_actor="raw-git-wrapper",
        real_life_test_status="",
        not_tested_rationale="",
        evidence_artifact=[],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 1
    assert report["ok"] is False
    assert not (tmp_path / "dev/state/raw_git_bypass_receipts.jsonl").exists()


def test_raw_git_wrapper_does_not_emit_receipt_for_help_noop(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_git(args: tuple[str, ...], capture: bool) -> GitCommandResult:
        calls.append(args)
        return GitCommandResult(0, "help\n", "")

    args = Namespace(
        raw_git_action="commit",
        git_args=["--help"],
        actor="codex",
        authority="operator_witnessed",
        bypass_lifecycle_id="",
        operator_quote_evidence_ref=[],
        feature_id="",
        test_command=[],
        tests_passed_count=None,
        tests_failed_count=None,
        connectivity_guard=[],
        connectivity_guards_passed="true",
        dogfood_evidence_ref="",
        review_fleet_role=[],
        review_fleet_actor="raw-git-wrapper",
        real_life_test_status="",
        not_tested_rationale="",
        evidence_artifact=[],
        store_path="dev/state/raw_git_bypass_receipts.jsonl",
        bypass_lifecycle_store_path="dev/state/bypass_lifecycles.jsonl",
        governed_exception_store_path="dev/state/governed_exception_lifecycles.jsonl",
    )

    report, rc = run_raw_git_action(args, repo_root=tmp_path, git_runner=fake_git)

    assert rc == 0
    assert report["reason"] == "git_help_noop"
    assert calls == []
    assert not (tmp_path / "dev/state/raw_git_bypass_receipts.jsonl").exists()
