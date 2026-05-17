import json
from pathlib import Path

from dev.scripts.checks.check_publication_scope_integrity import (
    evaluate_publication_scope_integrity,
    render_markdown,
)


def _write_deferral(tmp_path: Path, paths: list[str]) -> Path:
    path = tmp_path / "dev/state/dirty_deferral.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract_id": "DirtyWorktreeDeferralReceipt",
                "deferred_paths": paths,
                "not_part_of_publication_candidate": True,
                "import_graph_checked": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def test_clean_candidate_passes() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=("dev/scripts/checks/check_new.py",),
        unstaged_paths=(),
        untracked_paths=(),
    )

    assert report.ok is True
    assert report.staged_path_count == 1
    assert report.violation_count == 0


def test_unstaged_path_without_deferral_fails() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=("dev/scripts/checks/check_new.py",),
        unstaged_paths=("dev/state/plan_index.jsonl",),
        untracked_paths=(),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "unstaged_path_not_classified"
    assert report.violations[0]["classification"] == "typed_state_or_receipt"


def test_untracked_python_path_gets_specific_reason() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=(),
        untracked_paths=("dev/scripts/checks/new_guard.py",),
    )

    assert report.ok is False
    assert report.violations[0]["reason"] == "untracked_importable_python_path"


def test_valid_deferral_receipt_covers_dirty_paths(tmp_path: Path) -> None:
    receipt = _write_deferral(
        tmp_path,
        ["dev/state/plan_index.jsonl", "dev/scripts/checks/new_guard.py"],
    )

    report = evaluate_publication_scope_integrity(
        staged_paths=("dev/scripts/checks/check_new.py",),
        unstaged_paths=("dev/state/plan_index.jsonl",),
        untracked_paths=("dev/scripts/checks/new_guard.py",),
        deferral_receipt_path=receipt,
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
    )

    assert report.ok is False
    assert "dirty_deferral_receipt_missing_candidate_exclusion" in report.warnings[0]


def test_markdown_reports_violation() -> None:
    report = evaluate_publication_scope_integrity(
        staged_paths=(),
        unstaged_paths=("bridge.md",),
        untracked_paths=(),
    )

    rendered = render_markdown(report)

    assert "# check_publication_scope_integrity" in rendered
    assert "bridge.md" in rendered
    assert "generated_or_projection_surface" in rendered
