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
    feature_proof_receipt_artifact_relpath,
    feature_proof_receipt_from_mapping,
)
from dev.scripts.devctl.runtime.raw_git_bypass_receipts import (
    read_raw_git_bypass_receipts,
)


def test_raw_git_commit_wrapper_emits_receipt(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []
    state = {"committed": False}

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
        test_command=["python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/commands/test_raw_git.py"],
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


def test_raw_git_commit_wrapper_records_raw_commit_when_hook_advances_head(
    tmp_path: Path,
) -> None:
    state = {"committed": False}

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
    assert report["ok"] is True
    receipts = read_raw_git_bypass_receipts(
        tmp_path / "dev/state/raw_git_bypass_receipts.jsonl"
    )
    assert receipts[0].commit_sha == "raw123"
    assert receipts[0].affected_paths == ("dev/state/plan_index.jsonl",)
    proof_path = tmp_path / feature_proof_receipt_artifact_relpath("raw123")
    assert proof_path.exists()


def test_raw_git_push_wrapper_records_push_range(tmp_path: Path) -> None:
    state = {"pushed": False}

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
