import json
from pathlib import Path

from dev.scripts.checks.check_publication_scope_integrity import (
    evaluate_publication_scope_integrity,
    render_markdown,
)

CANDIDATE_TREE_SHA = "candidate-tree-123"


def _base_kwargs() -> dict[str, object]:
    return {
        "base_sha": "base123",
        "head_sha": "head123",
        "index_tree_sha": CANDIDATE_TREE_SHA,
        "staged_patch_sha256": "0" * 64,
        "ignored_paths": (),
    }


def _write_deferral(
    tmp_path: Path,
    paths: list[str],
    *,
    candidate_tree_sha: str = CANDIDATE_TREE_SHA,
) -> Path:
    path = tmp_path / "dev/state/dirty_deferral.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract_id": "DirtyWorktreeDeferralReceipt",
                "candidate_tree_sha": candidate_tree_sha,
                "deferred_paths": paths,
                "not_part_of_publication_candidate": True,
                "import_graph_checked": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_candidate_scope(
    tmp_path: Path,
    paths: list[str],
    *,
    candidate_tree_sha: str = CANDIDATE_TREE_SHA,
) -> Path:
    path = tmp_path / "dev/state/publication_candidate_scope.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract_id": "PublicationCandidateScope",
                "candidate_tree_sha": candidate_tree_sha,
                "allowed_paths": paths,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def test_clean_unstaged_candidate_passes() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=(),
        untracked_paths=(),
        **_base_kwargs(),
    )

    assert report.ok is True
    assert report.candidate_tree_sha == CANDIDATE_TREE_SHA
    assert report.staged_path_count == 0
    assert report.violation_count == 0


def test_staged_path_requires_candidate_scope_receipt() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=("dev/scripts/checks/check_new.py",),
        unstaged_paths=(),
        untracked_paths=(),
        **_base_kwargs(),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "staged_path_missing_candidate_scope"


def test_staged_path_outside_candidate_scope_fails(tmp_path: Path) -> None:
    scope = _write_candidate_scope(tmp_path, ["dev/scripts/checks/check_allowed.py"])

    report = evaluate_publication_scope_integrity(
        staged_paths=("dev/scripts/checks/check_new.py",),
        unstaged_paths=(),
        untracked_paths=(),
        candidate_scope_receipt_path=scope,
        **_base_kwargs(),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "staged_path_outside_candidate_scope"


def test_staged_path_inside_candidate_scope_passes(tmp_path: Path) -> None:
    scope = _write_candidate_scope(tmp_path, ["dev/scripts/checks/check_new.py"])

    report = evaluate_publication_scope_integrity(
        staged_paths=("dev/scripts/checks/check_new.py",),
        unstaged_paths=(),
        untracked_paths=(),
        candidate_scope_receipt_path=scope,
        **_base_kwargs(),
    )

    assert report.ok is True
    assert report.allowed_candidate_path_count == 1
    assert report.violation_count == 0


def test_unstaged_path_without_deferral_fails() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=("dev/state/plan_index.jsonl",),
        untracked_paths=(),
        **_base_kwargs(),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "unstaged_path_not_classified"
    assert report.violations[0]["classification"] == "typed_state_or_receipt"


def test_untracked_python_path_gets_specific_reason() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=(),
        untracked_paths=("dev/scripts/checks/new_guard.py",),
        **_base_kwargs(),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "untracked_importable_python_path"


def test_ignored_python_path_gets_specific_reason() -> None:
    kwargs = _base_kwargs()
    kwargs.pop("ignored_paths")
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=(),
        untracked_paths=(),
        ignored_paths=("dev/scripts/checks/ignored_guard.py",),
        **kwargs,
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "ignored_importable_python_path"


def test_ignored_rust_target_python_path_is_not_importable() -> None:
    kwargs = _base_kwargs()
    kwargs.pop("ignored_paths")
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=(),
        untracked_paths=(),
        ignored_paths=("rust/target/debug/build/generated.py",),
        **kwargs,
    )

    assert report.ok is True
    assert report.violation_count == 0


def test_valid_deferral_receipt_covers_dirty_paths(tmp_path: Path) -> None:
    receipt = _write_deferral(
        tmp_path,
        ["dev/state/plan_index.jsonl", "dev/scripts/checks/new_guard.py"],
    )

    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=("dev/state/plan_index.jsonl",),
        untracked_paths=("dev/scripts/checks/new_guard.py",),
        deferral_receipt_path=receipt,
        **_base_kwargs(),
    )

    assert report.ok is True
    assert report.deferred_path_count == 2
    assert report.violation_count == 0


def test_invalid_deferral_receipt_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "deferral.json"
    path.write_text(
        json.dumps(
            {
                "contract_id": "DirtyWorktreeDeferralReceipt",
                "deferred_paths": ["dev/state/plan_index.jsonl"],
            }
        ),
        encoding="utf-8",
    )

    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=("dev/state/plan_index.jsonl",),
        untracked_paths=(),
        deferral_receipt_path=path,
        **_base_kwargs(),
    )

    assert report.ok is False
    assert "dirty_deferral_receipt_missing_candidate_exclusion" in report.warnings[0]


def test_deferral_receipt_candidate_tree_mismatch_fails(tmp_path: Path) -> None:
    receipt = _write_deferral(
        tmp_path,
        ["dev/state/plan_index.jsonl"],
        candidate_tree_sha="other-tree",
    )

    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=("dev/state/plan_index.jsonl",),
        untracked_paths=(),
        deferral_receipt_path=receipt,
        **_base_kwargs(),
    )

    assert report.ok is False
    assert "dirty_deferral_receipt_candidate_tree_mismatch" in report.warnings[0]


def test_markdown_reports_violation() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=("bridge.md",),
        untracked_paths=(),
        **_base_kwargs(),
    )

    rendered = render_markdown(report)

    assert "# check_publication_scope_integrity" in rendered
    assert f"candidate_tree_sha: `{CANDIDATE_TREE_SHA}`" in rendered
    assert "bridge.md" in rendered
    assert "generated_or_projection_surface" in rendered
