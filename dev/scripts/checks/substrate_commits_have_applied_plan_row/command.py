#!/usr/bin/env python3
"""Require substrate commits to be covered by applied typed PlanRows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.governance.repo_policy import (
    load_repo_governance_section,
)
from dev.scripts.devctl.runtime.commit_to_plan_row_reducer import (
    DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL,
)
from dev.scripts.devctl.runtime.repo_portability import resolve_guard_mandate
from dev.scripts.devctl.runtime.value_coercion import coerce_string_items
from dev.scripts.checks.substrate_commits_have_applied_plan_row.coverage import (
    covered_commit_shas,
    successful_closure_commit_shas,
)
from dev.scripts.checks.substrate_commits_have_applied_plan_row.enforcement import (
    commit_is_enforced,
)
from dev.scripts.checks.substrate_commits_have_applied_plan_row.matching import (
    commit_covered,
)
from dev.scripts.checks.substrate_commits_have_applied_plan_row.jsonl_rows import (
    read_jsonl_rows,
    read_plan_rows,
)
from dev.scripts.checks.substrate_commits_have_applied_plan_row.path_policy import (
    path_is_substrate,
)
from dev.scripts.checks.substrate_commits_have_applied_plan_row.report import (
    render_markdown,
)
try:
    from dev.scripts.checks.git_support.range import git_commit_range
except ModuleNotFoundError:  # pragma: no cover - direct script fallback
    from git_support.range import git_commit_range

COMMAND = "check_substrate_commits_have_applied_plan_row"
CONTRACT_ID = "SubstrateCommitAppliedPlanRowGuard"
DEFAULT_BASE_REF = "@{u}"
DEFAULT_HEAD_REF = "HEAD"
DEFAULT_PLAN_INDEX_REL = Path("dev/state/plan_index.jsonl")
DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_REL = Path(
    DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_STORE_REL
)
DEFAULT_SUBSTRATE_PATHS = (
    "dev/scripts/checks/",
    "dev/scripts/devctl/",
    "dev/config/",
    "dev/guides/",
    "dev/state/contract_registry.jsonl",
    "AGENTS.md",
    "CLAUDE.md",
)
DEFAULT_IGNORE_PATHS = (
    "dev/scripts/devctl/tests/",
    "dev/test_data/",
    "dev/reports/",
    "dev/audits/",
    "bridge.md",
)
@dataclass(frozen=True, slots=True)
class SubstrateCommitPlanRowViolation:
    commit_sha: str
    reason: str
    scope: str
    changed_paths: tuple[str, ...] = ()
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SubstrateCommitAppliedPlanRowGuard:
    ok: bool
    scanned_commit_count: int
    substrate_commit_count: int
    covered_commit_count: int
    violation_count: int
    legacy_gap_count: int
    base_ref: str = DEFAULT_BASE_REF
    head_ref: str = DEFAULT_HEAD_REF
    plan_index_path: str = DEFAULT_PLAN_INDEX_REL.as_posix()
    policy_path: str = ""
    mandate_packet_id: str = ""
    mandate_observed_at_utc: str = ""
    substrate_paths: tuple[str, ...] = DEFAULT_SUBSTRATE_PATHS
    ignore_paths: tuple[str, ...] = DEFAULT_IGNORE_PATHS
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    legacy_gaps: tuple[dict[str, object], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = CONTRACT_ID
    command: str = COMMAND


def evaluate_substrate_commits_have_applied_plan_row(
    *,
    repo_root: Path = REPO_ROOT,
    base_ref: str = DEFAULT_BASE_REF,
    head_ref: str = DEFAULT_HEAD_REF,
    plan_index_path: Path | None = None,
    commit_shas: tuple[str, ...] | None = None,
    changed_paths_by_commit: dict[str, tuple[str, ...]] | None = None,
    committed_at_by_commit: dict[str, str] | None = None,
    policy_path: str | Path | None = None,
) -> SubstrateCommitAppliedPlanRowGuard:
    warnings: list[str] = []
    if commit_shas is None:
        commit_shas, range_warnings = git_commit_range(
            repo_root=repo_root,
            base_ref=base_ref,
            head_ref=head_ref,
        )
        warnings.extend(range_warnings)

    mandate = resolve_guard_mandate(COMMAND, repo_root=repo_root, policy_path=policy_path)
    substrate_paths, ignore_paths, policy_warnings, resolved_policy_path = _load_path_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    warnings.extend(policy_warnings)
    rows, row_warnings = read_plan_rows(plan_index_path or repo_root / DEFAULT_PLAN_INDEX_REL)
    warnings.extend(row_warnings)
    closure_receipts, closure_warnings = read_jsonl_rows(
        repo_root / DEFAULT_PLAN_ROW_CLOSURE_RECEIPT_REL,
        missing_ok=True,
        warning_prefix="plan_row_closure_receipt",
    )
    warnings.extend(closure_warnings)
    covered_commits = covered_commit_shas(rows)
    successful_closure_commits = successful_closure_commit_shas(closure_receipts)

    substrate_commit_count = 0
    covered_commit_count = 0
    violations: list[SubstrateCommitPlanRowViolation] = []
    legacy_gaps: list[SubstrateCommitPlanRowViolation] = []
    changed_paths_by_commit = changed_paths_by_commit or {}
    committed_at_by_commit = committed_at_by_commit or {}

    for commit_sha in commit_shas:
        changed_paths = changed_paths_by_commit.get(commit_sha)
        if changed_paths is None:
            changed_paths, changed_warnings = _git_changed_paths(
                repo_root=repo_root,
                commit_sha=commit_sha,
            )
            warnings.extend(changed_warnings)
        substrate_changed_paths = tuple(
            path
            for path in changed_paths
            if path_is_substrate(
                path,
                substrate_paths=substrate_paths,
                ignore_paths=ignore_paths,
            )
        )
        if not substrate_changed_paths:
            continue
        substrate_commit_count += 1
        committed_at = committed_at_by_commit.get(commit_sha)
        if committed_at is None:
            committed_at, time_warning = _git_commit_timestamp(
                repo_root=repo_root,
                commit_sha=commit_sha,
            )
            if time_warning:
                warnings.append(time_warning)
        scope = "enforced" if commit_is_enforced(committed_at, mandate=mandate) else "legacy"
        if commit_covered(commit_sha, covered_commits):
            if scope != "enforced" or commit_covered(
                commit_sha,
                successful_closure_commits,
            ):
                covered_commit_count += 1
                continue
            gap = SubstrateCommitPlanRowViolation(
                commit_sha=commit_sha,
                reason="missing_successful_plan_row_closure_receipt",
                scope=scope,
                changed_paths=substrate_changed_paths,
                detail=(
                    "Post-mandate substrate commits with applied PlanRows must also "
                    "have a PlanRowClosureReceipt with closure_succeeded=true."
                ),
            )
            violations.append(gap)
            continue
        gap = SubstrateCommitPlanRowViolation(
            commit_sha=commit_sha,
            reason="missing_applied_plan_row",
            scope=scope,
            changed_paths=substrate_changed_paths,
            detail=(
                "Substrate commits must have an applied/completed PlanRow whose "
                "commit_anchor_ref or anchor_refs point at the commit."
            ),
        )
        if scope == "enforced":
            violations.append(gap)
        else:
            legacy_gaps.append(gap)

    return SubstrateCommitAppliedPlanRowGuard(
        ok=not violations and not row_warnings and not closure_warnings,
        scanned_commit_count=len(commit_shas),
        substrate_commit_count=substrate_commit_count,
        covered_commit_count=covered_commit_count,
        violation_count=len(violations),
        legacy_gap_count=len(legacy_gaps),
        base_ref=base_ref,
        head_ref=head_ref,
        plan_index_path=_display_path(
            plan_index_path or repo_root / DEFAULT_PLAN_INDEX_REL,
            repo_root=repo_root,
        ),
        policy_path=_display_path(resolved_policy_path, repo_root=repo_root),
        mandate_packet_id=mandate.mandate_packet_id,
        mandate_observed_at_utc=mandate.observed_at_utc,
        substrate_paths=substrate_paths,
        ignore_paths=ignore_paths,
        violations=tuple(gap.to_dict() for gap in violations),
        legacy_gaps=tuple(gap.to_dict() for gap in legacy_gaps),
        warnings=tuple(warnings),
    )


def _load_path_policy(
    *,
    repo_root: Path,
    policy_path: str | Path | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], Path]:
    section, warnings, resolved_policy_path = load_repo_governance_section(
        "substrate_commit_plan_rows",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    target_paths = coerce_string_items(section.get("target_paths")) or DEFAULT_SUBSTRATE_PATHS
    ignore_paths = coerce_string_items(section.get("ignore_paths")) or DEFAULT_IGNORE_PATHS
    return target_paths, ignore_paths, tuple(warnings), resolved_policy_path


def _git_changed_paths(
    *,
    repo_root: Path,
    commit_sha: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    result = subprocess.run(
        ("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit_sha),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        warning = result.stderr.strip() or result.stdout.strip() or "git_diff_tree_failed"
        return (), (f"{commit_sha}:{warning}",)
    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip()), ()


def _git_commit_timestamp(
    *,
    repo_root: Path,
    commit_sha: str,
) -> tuple[str, str]:
    result = subprocess.run(
        ("git", "show", "-s", "--format=%cI", commit_sha),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        warning = result.stderr.strip() or result.stdout.strip() or "git_show_failed"
        return "", f"{commit_sha}:{warning}"
    return result.stdout.strip(), ""


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", default=DEFAULT_BASE_REF)
    parser.add_argument("--head-ref", default=DEFAULT_HEAD_REF)
    parser.add_argument("--plan-index", default=DEFAULT_PLAN_INDEX_REL.as_posix())
    parser.add_argument("--policy-path")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = evaluate_substrate_commits_have_applied_plan_row(
            base_ref=args.since_ref,
            head_ref=args.head_ref,
            plan_index_path=REPO_ROOT / args.plan_index,
            policy_path=args.policy_path,
        )
    # broad-except: allow reason=guard entrypoints must emit structured reports instead of tracebacks fallback=typed runtime error
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        return emit_runtime_error(COMMAND, args.format, f"{exc.__class__.__name__}: {exc}")
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(render_markdown(report, command=COMMAND), end="")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
