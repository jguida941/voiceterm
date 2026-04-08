"""Tests for the ReviewSnapshot typed projection builder."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from devctl.runtime.review_snapshot import build_review_snapshot
from devctl.runtime.review_snapshot_git import (
    extract_checkpoint_markers,
    extract_mp_refs,
    first_body_excerpt,
)
from devctl.runtime.review_snapshot_render import render_review_snapshot_markdown
from devctl.runtime.review_snapshot_hints import (
    build_suggested_commands,
    classify_bundle_lane,
    detect_authority_surfaces,
    detect_contract_mutations,
    detect_risk_addons,
)
from devctl.runtime.review_snapshot_models import (
    REVIEW_SNAPSHOT_CONTRACT_ID,
    ReviewSnapshot,
)


def test_build_review_snapshot_returns_typed_contract() -> None:
    snap = build_review_snapshot(
        startup_payload={},
        governance_payload={},
        probe_payload={},
        context_graph_payload={},
    )
    assert isinstance(snap, ReviewSnapshot)
    assert snap.contract_id == REVIEW_SNAPSHOT_CONTRACT_ID
    assert snap.schema_version == 1
    assert snap.identity.generation_stamp.startswith("snap-")


def test_build_review_snapshot_to_dict_is_json_serialisable() -> None:
    snap = build_review_snapshot(
        startup_payload={},
        governance_payload={},
        probe_payload={},
        context_graph_payload={},
    )
    payload = snap.to_dict()
    # Round-tripping through json proves every nested field is a basic type.
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["contract_id"] == REVIEW_SNAPSHOT_CONTRACT_ID
    assert "identity" in decoded
    assert "delta" in decoded
    assert "reviewer_hints" in decoded


def test_build_review_snapshot_reads_governance_inputs() -> None:
    startup_payload = {
        "advisory_action": "checkpoint_required",
        "advisory_reason": "worktree_dirty",
        "push_decision": {
            "action": "await_checkpoint",
            "reason": "dirty_worktree",
            "push_eligible_now": False,
            "next_step_command": "python3 dev/scripts/devctl.py push --execute",
            "worktree_clean": False,
            "publication_backlog": {"backlog_state": "ahead"},
        },
        "reviewer_gate": {
            "effective_reviewer_mode": "active_dual_agent",
            "operator_interaction_mode": "local_terminal",
            "review_gate_allows_push": True,
            "required_checks_status": "fresh",
        },
        "remote_commit_pipeline": {
            "state": "commit_pending",
            "blocked_reason": "awaiting_reviewer",
            "approval_state": "not_requested",
            "push_report_path": "dev/reports/review_channel/latest/push.json",
            "push_authorization": {
                "authorization_id": "push-auth-123",
                "authorized_head_sha": "deadbeef1234",
                "approved_target_identity": "tree-123:gen-9",
            },
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": True,
                "latest_push_report_path": "dev/reports/push/latest.json",
                "latest_push_report_status": "published_remote",
                "latest_push_report_reason": "post_push_pending",
                "latest_push_report_published_remote": True,
                "latest_push_report_post_push_green": False,
                "current_push_authorization_id": "push-auth-123",
                "current_push_authorization_valid": True,
                "current_push_authorization_head_commit": "deadbeef1234",
                "current_push_authorization_approved_target_identity": "tree-123:gen-9",
            },
            "repo_identity": {
                "repo_name": "test-repo",
                "default_branch": "main",
                "remote_url": "https://example.com/test.git",
            },
        },
        "work_intake": {
            "continuity": {
                "source_plan_title": "Test plan",
                "source_plan_path": "dev/active/test_plan.md",
                "source_scope": ["MP-999"],
            },
        },
        "contract_ownership_map": {
            "StartupContext": {
                "owner_layer": "governance_runtime",
                "runtime_model": "dev.scripts.devctl.runtime.startup_context:StartupContext",
                "startup_surface_tokens": ["push_eligible", "advisory_action"],
            },
        },
        "product_thesis": "Portable AI governance platform",
        "rejected_rule_traces": [],
    }
    governance_summary = {
        "ok": True,
        "stats": {
            "total_findings": 120,
            "open_finding_count": 30,
            "fixed_count": 80,
            "false_positive_count": 10,
        },
        "recent_findings": [
            {
                "finding_id": "f1",
                "check_id": "code_shape",
                "file_path": "dev/scripts/x.py",
                "symbol": "do_thing",
                "severity": "medium",
                "signal_type": "guard",
                "verdict": "open",
                "notes": "function too long",
            },
        ],
    }
    probe_summary = {
        "generated_at": "2026-04-08T00:00:00Z",
        "mode": "working-tree",
        "warnings": ["probe warning"],
        "errors": [],
        "artifact_paths": {
            "summary_json": "dev/reports/probe_report/latest/summary.json",
            "summary_md": "dev/reports/probe_report/latest/summary.md",
        },
        "summary": {
            "files_scanned": 441,
            "risk_hints": 23,
            "hints_by_severity": {"high": 8, "medium": 14, "low": 1},
        },
        "enriched_hints": [
            {
                "probe": "unwrap_chains",
                "review_lens": "correctness",
                "severity": "high",
                "file": "rust/src/parser/ansi.rs",
                "line": 42,
                "rule_id": "unwrap_chains/too_long",
                "message": "chain of 5 unwraps",
            },
        ],
    }
    snap = build_review_snapshot(
        startup_payload=startup_payload,
        governance_payload=governance_summary,
        probe_payload=probe_summary,
        context_graph_payload={},
    )
    assert snap.governance_state.push_action == "await_checkpoint"
    assert snap.governance_state.latest_push_report_path == "dev/reports/push/latest.json"
    assert snap.governance_state.pipeline_push_report_path == "dev/reports/review_channel/latest/push.json"
    assert snap.governance_state.current_push_authorization_id == "push-auth-123"
    assert snap.governance_state.current_push_authorization_valid is True
    assert snap.governance_state.reviewer_mode == "active_dual_agent"
    assert snap.governance_state.interaction_mode == "local_terminal"
    assert snap.governance_state.pipeline_state == "commit_pending"
    assert snap.governance_state.active_plan_title == "Test plan"
    assert snap.governance_state.active_mp_scope == ("MP-999",)
    assert snap.identity.repo_name == "test-repo"
    assert snap.identity.product_thesis == "Portable AI governance platform"
    assert snap.quality.governance_total_findings == 120
    assert snap.quality.governance_open_findings == 30
    assert snap.quality.probe_run_state == "ok"
    assert snap.quality.probe_run_mode == "working-tree"
    assert snap.quality.probe_warning_count == 1
    assert (
        snap.quality.probe_summary_json_path
        == "dev/reports/probe_report/latest/summary.json"
    )
    assert snap.quality.probe_hints_total == 23
    assert snap.quality.probe_hints_by_severity == {"high": 8, "medium": 14, "low": 1}
    assert len(snap.architecture.contract_ownership_map) == 1
    assert snap.architecture.contract_ownership_map[0].contract_id == "StartupContext"
    # Blocker advisory surfaces in known_gaps
    assert snap.known_gaps.startup_action_advisories == (
        "checkpoint_required: worktree_dirty",
    )


def test_render_review_snapshot_surfaces_probe_run_and_push_receipts() -> None:
    snap = build_review_snapshot(
        startup_payload={
            "push_decision": {
                "action": "run_devctl_push",
                "reason": "ready",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
                "push_eligible_now": True,
                "worktree_clean": True,
                "publication_backlog": {"backlog_state": "none"},
            },
            "reviewer_gate": {
                "effective_reviewer_mode": "single_agent",
                "operator_interaction_mode": "local_terminal",
                "required_checks_status": "fresh",
                "review_gate_allows_push": True,
            },
            "remote_commit_pipeline": {
                "state": "push_ready",
                "approval_state": "approved",
                "push_report_path": "dev/reports/review_channel/latest/push.json",
            },
            "governance": {
                "push_enforcement": {
                    "latest_push_report_path": "dev/reports/push/latest.json",
                    "latest_push_report_status": "published_remote",
                    "latest_push_report_reason": "post_push_pending",
                    "current_push_authorization_id": "push-auth-123",
                    "current_push_authorization_valid": True,
                }
            },
        },
        governance_payload={},
        probe_payload={
            "generated_at": "2026-04-08T00:00:00Z",
            "mode": "working-tree",
            "warnings": [],
            "errors": [],
            "artifact_paths": {
                "summary_json": "dev/reports/probe_report/latest/summary.json",
                "summary_md": "dev/reports/probe_report/latest/summary.md",
            },
            "summary": {"files_scanned": 0, "risk_hints": 0, "hints_by_severity": {}},
        },
        context_graph_payload={},
    )

    rendered = render_review_snapshot_markdown(snap)

    assert "- latest_push_report: `dev/reports/push/latest.json`" in rendered
    assert "- pipeline_push_report: `dev/reports/review_channel/latest/push.json`" in rendered
    assert "- current_push_authorization: `push-auth-123` (valid=True)" in rendered
    assert "- run_state: `ok`" in rendered
    assert "- summary_json: `dev/reports/probe_report/latest/summary.json`" in rendered


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def test_classify_bundle_lane_buckets_paths_correctly() -> None:
    assert classify_bundle_lane("rust/src/parser/ansi.rs") == "runtime"
    assert classify_bundle_lane("dev/scripts/devctl/commands/check/router.py") == "tooling"
    assert classify_bundle_lane("guides/CLI_FLAGS.md") == "docs"
    assert classify_bundle_lane("README.md") == "docs"
    assert classify_bundle_lane("dev/active/MASTER_PLAN.md") == "tooling"
    assert classify_bundle_lane("") == "unknown"


def test_detect_risk_addons_triggers_on_parser_path() -> None:
    triggered = detect_risk_addons(("rust/src/parser/ansi.rs",))
    assert "Parser / ANSI boundary" in triggered


def test_detect_risk_addons_triggers_multiple_for_pty_session() -> None:
    triggered = detect_risk_addons(("rust/src/pty_session.rs",))
    assert "Unsafe / FFI lifecycle" in triggered
    assert "Threading / lifecycle / memory" in triggered


def test_detect_authority_surfaces_flags_startup_context() -> None:
    matches = detect_authority_surfaces(
        ("dev/scripts/devctl/runtime/startup_context.py", "guides/README.md")
    )
    assert matches == ("dev/scripts/devctl/runtime/startup_context.py",)


def test_detect_contract_mutations_flags_contract_rows() -> None:
    matches = detect_contract_mutations(
        (
            "dev/scripts/devctl/runtime/remote_commit_pipeline_models.py",
            "dev/scripts/devctl/platform/runtime_state_contract_rows.py",
            "rust/src/main.rs",
        )
    )
    assert len(matches) == 2
    assert "remote_commit_pipeline_models.py" in matches[0]


def test_build_suggested_commands_dedupes_and_always_includes_check_router() -> None:
    commands = build_suggested_commands(
        bundle_classes_touched=("runtime", "docs"),
        risk_addons_triggered=("Parser / ANSI boundary",),
        authority_surfaces_touched=("dev/scripts/devctl/runtime/startup_context.py",),
    )
    assert "python3 dev/scripts/devctl.py check --profile ci" in commands
    assert any("check-router" in cmd for cmd in commands)
    # Dedupe preserves order
    assert len(commands) == len(set(commands))


# ---------------------------------------------------------------------------
# Git plumbing helpers (regex / text only, no subprocess)
# ---------------------------------------------------------------------------


def test_extract_mp_refs_returns_distinct_ordered_ids() -> None:
    text = "Land MP-382 + MP-387 launch-authority closure; references MP-382 again"
    assert extract_mp_refs(text) == ("MP-382", "MP-387")


def test_extract_checkpoint_markers_returns_distinct_ordered_markers() -> None:
    text = "Land MP-382 + MP-387 launch-authority closure (F21/F21a/F23/F24)"
    markers = extract_checkpoint_markers(text)
    assert "F21" in markers
    assert "F21a" in markers
    assert len(markers) == len(set(markers))


def test_first_body_excerpt_bounded_to_six_lines() -> None:
    body = "\n".join(f"line {n}" for n in range(1, 12))
    excerpt = first_body_excerpt(body, max_lines=4)
    assert excerpt.count("\n") == 3
    assert excerpt.startswith("line 1")
    assert excerpt.endswith("line 4")


# ---------------------------------------------------------------------------
# Refresh-helper skip behaviour (prevents untracked-file regressions)
# ---------------------------------------------------------------------------


def test_refresh_skips_when_target_file_does_not_exist(tmp_path) -> None:
    from devctl.runtime.review_snapshot_refresh import refresh_review_snapshot_file

    # tmp_path has no dev/audits/REVIEW_SNAPSHOT.md — refresh should no-op.
    warnings = refresh_review_snapshot_file(repo_root=tmp_path)
    assert warnings == []
    assert not (tmp_path / "dev/audits/REVIEW_SNAPSHOT.md").exists()


def test_governed_commit_includes_review_snapshot_in_committed_tree(tmp_path) -> None:
    """The publish-semantics regression test the external reviewer asked for.

    Proves that when the governed executor commits, the refreshed
    REVIEW_SNAPSHOT.md actually lives inside the committed tree (not just in
    the worktree). Without this proof the whole external-review surface
    could silently fail to publish on push even though it looked updated
    locally.
    """
    from devctl.commands.vcs.governed_executor import (
        build_commit_action,
        build_stage_action,
    )
    from devctl.tests.vcs.test_governed_executor import (
        _executor,
        _init_repo,
        _passing_guard_result,
    )
    from devctl.tests.runtime.test_remote_commit_pipeline_phases34 import (
        _approve_pipeline,
    )

    repo_root = _init_repo(tmp_path / "repo")
    # Pre-initialize the snapshot file so the refresh helper actually writes
    # it — this matches the production invariant that adopter repos must
    # explicitly opt in via a first manual `devctl review-snapshot --write`.
    snapshot_dir = repo_root / "dev/audits"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / "REVIEW_SNAPSHOT.md"
    snapshot_path.write_text("# Placeholder\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "dev/audits/REVIEW_SNAPSHOT.md"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init review snapshot placeholder"],
        cwd=repo_root,
        check=True,
    )

    (repo_root / "tracked.txt").write_text("publish-test\n", encoding="utf-8")
    executor = _executor(repo_root)
    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: publish semantics proof",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-XYZ",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    _approve_pipeline(repo_root=repo_root, pipeline=pipeline)

    commit_result = executor.execute(
        build_commit_action(
            repo_pack_id="test-pack",
            pipeline_id=pipeline.pipeline_id,
        )
    )
    assert commit_result.ok is True

    # The canonical proof: the committed tree at HEAD must contain a
    # dev/audits/REVIEW_SNAPSHOT.md blob. If the refresh hook ran
    # post-commit, this ls-tree lookup would miss the entry for tracked.txt's
    # commit (only the placeholder would still be there).
    result = subprocess.run(
        ["git", "ls-tree", "-r", "HEAD", "dev/audits/REVIEW_SNAPSHOT.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "dev/audits/REVIEW_SNAPSHOT.md" in result.stdout, (
        "Expected dev/audits/REVIEW_SNAPSHOT.md to be tracked in the committed "
        f"tree at HEAD, but ls-tree returned: {result.stdout!r}"
    )

    # Also verify the committed content differs from the placeholder we
    # started with — otherwise the refresh happened but wrote the same file
    # and the proof is vacuous.
    show = subprocess.run(
        ["git", "show", "HEAD:dev/audits/REVIEW_SNAPSHOT.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    committed_content = show.stdout
    assert committed_content != "# Placeholder\n", (
        "The committed snapshot content matches the placeholder — the "
        "refresh hook did not regenerate the file before commit."
    )
    # Sanity check: the committed content looks like a ReviewSnapshot.
    assert "Review Snapshot" in committed_content
    assert "Generation stamp" in committed_content

    # And the worktree must now be clean — otherwise the push path would
    # fail validation again. This is the regression that the earlier
    # post-commit hook introduced and this test guards against.
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert status.stdout.strip() == "", (
        f"Expected clean worktree after governed commit, got: {status.stdout!r}"
    )


def test_receipt_commit_commits_only_review_snapshot(tmp_path) -> None:
    from devctl.commands.governance.review_snapshot import _commit_snapshot_receipt

    repo_root = _init_receipt_repo(tmp_path / "repo")
    snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("# Review Snapshot\n\nreceipt\n", encoding="utf-8")

    result = _commit_snapshot_receipt(
        repo_root=repo_root,
        target_rel="dev/audits/REVIEW_SNAPSHOT.md",
    )

    assert result["ok"] is True
    assert result["reason"] == "receipt_committed"
    changed = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert changed.stdout.strip() == "dev/audits/REVIEW_SNAPSHOT.md"


def test_receipt_commit_preflight_rejects_non_snapshot_dirty_paths(tmp_path) -> None:
    from devctl.commands.governance.review_snapshot import _preflight_receipt_commit

    repo_root = _init_receipt_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    result = _preflight_receipt_commit(
        repo_root=repo_root,
        target_rel="dev/audits/REVIEW_SNAPSHOT.md",
    )

    assert result["ok"] is False
    assert result["reason"] == "non_snapshot_paths_dirty"
    assert result["dirty_paths"] == ["tracked.txt"]


def test_refresh_skips_when_content_already_matches(tmp_path, monkeypatch) -> None:
    from devctl.runtime import review_snapshot_refresh as refresh_module
    from devctl.runtime.review_snapshot_models import ReviewSnapshot

    target = tmp_path / "dev/audits/REVIEW_SNAPSHOT.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture-content\n", encoding="utf-8")

    # Stub the builder and renderer so we don't depend on a real repo.
    def _fake_build(**_kwargs):
        return ReviewSnapshot()

    def _fake_render(_snap):
        return "fixture-content\n"

    def _fake_scan(_root):
        return None

    monkeypatch.setattr(
        "devctl.runtime.review_snapshot.build_review_snapshot",
        _fake_build,
    )
    monkeypatch.setattr(
        "devctl.runtime.review_snapshot_render.render_review_snapshot_markdown",
        _fake_render,
    )
    monkeypatch.setattr(
        "devctl.runtime.governance_scan.scan_repo_governance_safely",
        _fake_scan,
    )

    mtime_before = target.stat().st_mtime_ns
    warnings = refresh_module.refresh_review_snapshot_file(repo_root=tmp_path)
    assert warnings == []
    # Same content → no write → mtime preserved.
    assert target.stat().st_mtime_ns == mtime_before
    assert target.read_text(encoding="utf-8") == "fixture-content\n"


def _init_receipt_repo(repo_root: Path) -> Path:
    repo_root.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "tests@example.com"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "ReviewSnapshot Tests"],
        cwd=repo_root,
        check=True,
    )
    (repo_root / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return repo_root
