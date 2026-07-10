import subprocess
from pathlib import Path

from dev.scripts.checks.check_runtime_state_ignore_posture import (
    evaluate_runtime_state_ignore_posture,
)


def test_runtime_state_paths_ignored_and_untracked_pass(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write(
        tmp_path,
        ".gitignore",
        "\n".join(
            (
                "dev/state/bypass_lifecycles.jsonl",
                "dev/state/governed_exception_lifecycles.jsonl",
            )
        )
        + "\n",
    )
    _write(tmp_path, "dev/state/bypass_lifecycles.jsonl", "{}\n")
    _write(tmp_path, "dev/state/governed_exception_lifecycles.jsonl", "{}\n")

    report = evaluate_runtime_state_ignore_posture(
        repo_root=tmp_path,
        paths=(
            "dev/state/bypass_lifecycles.jsonl",
            "dev/state/governed_exception_lifecycles.jsonl",
        ),
    )

    assert report.ok is True
    assert report.checked_path_count == 2
    assert report.ignored_path_count == 2
    assert report.tracked_path_count == 0
    assert report.violation_count == 0


def test_runtime_state_tracked_path_fails_even_when_ignored(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write(tmp_path, ".gitignore", "dev/state/bypass_lifecycles.jsonl\n")
    _write(tmp_path, "dev/state/bypass_lifecycles.jsonl", "{}\n")
    _git(tmp_path, "add", "-f", "dev/state/bypass_lifecycles.jsonl")

    report = evaluate_runtime_state_ignore_posture(
        repo_root=tmp_path,
        paths=("dev/state/bypass_lifecycles.jsonl",),
    )

    assert report.ok is False
    assert report.would_fail is True
    assert report.tracked_path_count == 1
    assert report.violation_count == 1
    assert report.violations[0]["path"] == "dev/state/bypass_lifecycles.jsonl"
    assert report.violations[0]["tracked"] is True


def test_runtime_state_missing_ignore_rule_fails(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write(tmp_path, "dev/state/bypass_lifecycles.jsonl", "{}\n")

    report = evaluate_runtime_state_ignore_posture(
        repo_root=tmp_path,
        paths=("dev/state/bypass_lifecycles.jsonl",),
    )

    assert report.ok is False
    assert report.ignored_path_count == 0
    assert report.violation_count == 1
    assert report.violations[0]["ignored"] is False


def _init_repo(root: Path) -> None:
    _git(root, "init")


def _write(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
