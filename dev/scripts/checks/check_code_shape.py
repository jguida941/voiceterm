#!/usr/bin/env python3
"""Guard against source-file shape drift in Rust/Python code."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ShapePolicy:
    soft_limit: int
    hard_limit: int
    oversize_growth_limit: int
    hard_lock_growth_limit: int


LANGUAGE_POLICIES: dict[str, ShapePolicy] = {
    # Existing Rust runtime has a few legacy oversized files; this guard is
    # intentionally non-regressive and blocks new oversize growth.
    ".rs": ShapePolicy(
        soft_limit=900,
        hard_limit=1400,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    ".py": ShapePolicy(
        soft_limit=350,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
}

BEST_PRACTICE_DOCS: dict[str, tuple[str, ...]] = {
    ".rs": (
        "https://doc.rust-lang.org/book/",
        "https://rust-lang.github.io/api-guidelines/",
    ),
    ".py": (
        "https://docs.python.org/3/",
        "https://peps.python.org/pep-0008/",
    ),
}

SHAPE_AUDIT_GUIDANCE = (
    "Run a shape audit before merge: identify modularization or consolidation opportunities. "
    "Do not bypass shape limits with readability-reducing code-golf edits."
)

# Phase 3C hotspot budgets (MP-265): these files must not grow while staged
# decomposition work is active.
PATH_POLICY_OVERRIDES: dict[str, ShapePolicy] = {
    "src/src/bin/voiceterm/event_loop/input_dispatch.rs": ShapePolicy(
        soft_limit=1200,
        hard_limit=1561,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "src/src/bin/voiceterm/status_line/format.rs": ShapePolicy(
        soft_limit=1000,
        hard_limit=1200,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "src/src/bin/voiceterm/status_line/buttons.rs": ShapePolicy(
        soft_limit=1000,
        hard_limit=1200,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "src/src/bin/voiceterm/theme/rule_profile.rs": ShapePolicy(
        soft_limit=1000,
        hard_limit=1200,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "src/src/bin/voiceterm/theme/style_pack.rs": ShapePolicy(
        soft_limit=750,
        hard_limit=950,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "src/src/bin/voiceterm/transcript_history.rs": ShapePolicy(
        soft_limit=750,
        hard_limit=950,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_code_shape.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_active_plan_sync.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_multi_agent_sync.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
}


def _policy_for_path(path: Path) -> tuple[ShapePolicy | None, str | None]:
    override = PATH_POLICY_OVERRIDES.get(path.as_posix())
    if override is not None:
        return override, f"path_override:{path.as_posix()}"
    policy = LANGUAGE_POLICIES.get(path.suffix)
    if policy is None:
        return None, None
    return policy, f"language_default:{path.suffix}"


def _run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "git command failed")
    return result


def _validate_ref(ref: str) -> None:
    _run_git(["git", "rev-parse", "--verify", ref], check=True)


def _list_changed_paths(since_ref: str | None, head_ref: str) -> list[Path]:
    if since_ref:
        diff_cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", since_ref, head_ref]
    else:
        diff_cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"]

    changed = {
        Path(line.strip())
        for line in _run_git(diff_cmd).stdout.splitlines()
        if line.strip()
    }

    if since_ref is None:
        untracked = _run_git(["git", "ls-files", "--others", "--exclude-standard"])
        for line in untracked.stdout.splitlines():
            if line.strip():
                changed.add(Path(line.strip()))

    return sorted(changed)


def _is_test_path(path: Path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name

    if path.suffix == ".rs":
        return "/tests/" in normalized or name == "tests.rs" or name.endswith("_test.rs")
    if path.suffix == ".py":
        return "/tests/" in normalized or name.startswith("test_") or name.endswith("_test.py")
    return False


def _read_text_from_ref(path: Path, ref: str) -> str | None:
    spec = f"{ref}:{path.as_posix()}"
    result = _run_git(["git", "show", spec], check=False)
    if result.returncode == 0:
        return result.stdout

    stderr = result.stderr.strip()
    missing_markers = (
        "does not exist in",
        "exists on disk, but not in",
        "fatal: path",
    )
    if any(marker in stderr.lower() for marker in missing_markers):
        return None

    raise RuntimeError(stderr or f"failed to read {spec}")


def _read_text_from_worktree(path: Path) -> str | None:
    absolute_path = REPO_ROOT / path
    if not absolute_path.exists():
        return None
    return absolute_path.read_text(encoding="utf-8", errors="replace")


def _count_lines(text: str | None) -> int | None:
    if text is None:
        return None
    return len(text.splitlines())


def _violation(
    *,
    path: Path,
    reason: str,
    guidance: str,
    policy: ShapePolicy,
    policy_source: str,
    base_lines: int | None,
    current_lines: int,
) -> dict:
    growth = None if base_lines is None else current_lines - base_lines
    docs_refs = BEST_PRACTICE_DOCS.get(path.suffix, ())
    guidance_parts = [guidance]
    if reason != "current_file_missing":
        guidance_parts.append(SHAPE_AUDIT_GUIDANCE)
    if docs_refs:
        guidance_parts.append("Best-practice refs: " + ", ".join(docs_refs))
    return {
        "path": path.as_posix(),
        "reason": reason,
        "guidance": " ".join(guidance_parts),
        "best_practice_refs": list(docs_refs),
        "base_lines": base_lines,
        "current_lines": current_lines,
        "growth": growth,
        "policy": {
            "soft_limit": policy.soft_limit,
            "hard_limit": policy.hard_limit,
            "oversize_growth_limit": policy.oversize_growth_limit,
            "hard_lock_growth_limit": policy.hard_lock_growth_limit,
        },
        "policy_source": policy_source,
    }


def _evaluate_shape(
    *,
    path: Path,
    policy: ShapePolicy,
    policy_source: str,
    base_lines: int | None,
    current_lines: int | None,
) -> dict | None:
    if current_lines is None:
        return _violation(
            path=path,
            reason="current_file_missing",
            guidance="File is missing in current tree; rerun after resolving rename/delete state.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=0,
        )

    if base_lines is None:
        if current_lines > policy.soft_limit:
            return _violation(
                path=path,
                reason="new_file_exceeds_soft_limit",
                guidance="Split the new file before merge or keep it under the soft limit.",
                policy=policy,
                policy_source=policy_source,
                base_lines=base_lines,
                current_lines=current_lines,
            )
        return None

    growth = current_lines - base_lines
    if base_lines <= policy.soft_limit and current_lines > policy.soft_limit:
        return _violation(
            path=path,
            reason="crossed_soft_limit",
            guidance="Refactor into smaller modules before crossing the soft limit.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    if base_lines <= policy.hard_limit and current_lines > policy.hard_limit and growth > 0:
        return _violation(
            path=path,
            reason="crossed_hard_limit",
            guidance="Hard limit exceeded; split and reduce file size before merge.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    if base_lines > policy.hard_limit and growth > policy.hard_lock_growth_limit:
        return _violation(
            path=path,
            reason="hard_locked_file_grew",
            guidance="File is already above hard limit; do not grow it further.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    if base_lines > policy.soft_limit and growth > policy.oversize_growth_limit:
        return _violation(
            path=path,
            reason="oversize_file_growth_exceeded_budget",
            guidance=(
                "File is already above soft limit; keep growth within budget or decompose first."
            ),
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    return None


def _render_md(report: dict) -> str:
    lines = ["# check_code_shape", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_using_path_overrides: {report['files_using_path_overrides']}")
    lines.append(f"- files_skipped_non_source: {report['files_skipped_non_source']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            growth = violation["growth"]
            growth_label = "n/a" if growth is None else f"{growth:+d}"
            lines.append(
                f"- `{violation['path']}` ({violation['reason']}): "
                f"{violation['base_lines']} -> {violation['current_lines']} "
                f"(growth {growth_label}); {violation['guidance']} "
                f"[policy: {violation['policy_source']}]"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref used with --since-ref")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            _validate_ref(args.since_ref)
            _validate_ref(args.head_ref)
        changed_paths = _list_changed_paths(args.since_ref, args.head_ref)
    except RuntimeError as exc:
        error_report = {
            "command": "check_code_shape",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "error": str(exc),
        }
        if args.format == "json":
            print(json.dumps(error_report, indent=2))
        else:
            print("# check_code_shape\n")
            print(f"- ok: False\n- error: {error_report['error']}")
        return 2

    mode = "commit-range" if args.since_ref else "working-tree"
    violations: list[dict] = []
    files_skipped_non_source = 0
    files_skipped_tests = 0
    files_considered = 0
    files_using_path_overrides = 0

    for path in changed_paths:
        policy, policy_source = _policy_for_path(path)
        if policy is None:
            files_skipped_non_source += 1
            continue
        if _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1
        if policy_source and policy_source.startswith("path_override:"):
            files_using_path_overrides += 1

        if args.since_ref:
            base_lines = _count_lines(_read_text_from_ref(path, args.since_ref))
            current_lines = _count_lines(_read_text_from_ref(path, args.head_ref))
        else:
            base_lines = _count_lines(_read_text_from_ref(path, "HEAD"))
            current_lines = _count_lines(_read_text_from_worktree(path))

        violation = _evaluate_shape(
            path=path,
            policy=policy,
            policy_source=policy_source or "unknown",
            base_lines=base_lines,
            current_lines=current_lines,
        )
        if violation:
            violations.append(violation)

    report = {
        "command": "check_code_shape",
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_using_path_overrides": files_using_path_overrides,
        "files_skipped_non_source": files_skipped_non_source,
        "files_skipped_tests": files_skipped_tests,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
