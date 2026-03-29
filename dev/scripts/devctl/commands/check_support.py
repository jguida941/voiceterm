"""Shared helpers for `devctl check`."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ..config import REPO_ROOT, get_repo_root, resolve_src_dir
from ..quality_policy import (
    DEFAULT_AI_GUARD_CHECKS,
    DEFAULT_REVIEW_PROBE_CHECKS,
    ai_guard_supports_commit_range,
    review_probe_supports_commit_range,
)
from ..script_catalog import check_script_cmd, probe_script_cmd

AI_GUARD_CHECKS = DEFAULT_AI_GUARD_CHECKS
REVIEW_PROBE_CHECKS = DEFAULT_REVIEW_PROBE_CHECKS


def _repo_check_reports_root() -> Path:
    return get_repo_root() / "dev" / "reports" / "check"


def _clippy_high_signal_lints_path() -> Path:
    return _repo_check_reports_root() / "clippy-lints.json"


def _clippy_pedantic_summary_path() -> Path:
    return _repo_check_reports_root() / "clippy-pedantic-summary.json"


def _clippy_pedantic_lints_path() -> Path:
    return _repo_check_reports_root() / "clippy-pedantic-lints.json"


def build_probe_cmd(
    script_id: str,
    *,
    since_ref: str | None,
    head_ref: str,
    adoption_scan: bool = False,
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build one review-probe command with optional commit-range refs."""
    cmd = probe_script_cmd(script_id, *extra_args)
    if adoption_scan and review_probe_supports_commit_range(script_id):
        cmd.extend(["--since-ref", since_ref or "", "--head-ref", head_ref])
    elif since_ref and review_probe_supports_commit_range(script_id):
        cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    return cmd


def build_ai_guard_cmd(
    script_id: str,
    *,
    since_ref: str | None,
    head_ref: str,
    adoption_scan: bool = False,
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build one AI-guard command with optional commit-range refs."""
    cmd = check_script_cmd(script_id, *extra_args)
    if adoption_scan and ai_guard_supports_commit_range(script_id):
        cmd.extend(["--since-ref", since_ref or "", "--head-ref", head_ref])
    elif since_ref and ai_guard_supports_commit_range(script_id):
        cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    return cmd


def resolve_perf_log_path() -> str:
    """Return the expected perf log file path used by the verifier script."""
    return str(Path(tempfile.gettempdir()) / "voiceterm_tui.log")


def build_clippy_high_signal_collect_cmd() -> list[str]:
    """Build the strict clippy lint-histogram collection command."""
    return [
        "python3",
        "dev/scripts/rust_tools/collect_clippy_warnings.py",
        "--working-directory",
        str(resolve_src_dir(get_repo_root())),
        "--output-lints-json",
        str(_clippy_high_signal_lints_path()),
        "--deny-warnings",
        "--quiet-json-stream",
        "--propagate-exit-code",
    ]


def build_clippy_high_signal_guard_cmd() -> list[str]:
    """Build the high-signal lint baseline guard command."""
    return check_script_cmd(
        "clippy_high_signal",
        "--input-lints-json",
        str(_clippy_high_signal_lints_path()),
        "--format",
        "md",
    )


def build_clippy_pedantic_collect_cmd(
    *,
    summary_path: str | Path | None = None,
    lints_path: str | Path | None = None,
) -> list[str]:
    """Build the pedantic clippy collection command."""
    resolved_summary_path = str(summary_path or _clippy_pedantic_summary_path())
    resolved_lints_path = str(lints_path or _clippy_pedantic_lints_path())
    return [
        "python3",
        "dev/scripts/rust_tools/collect_clippy_warnings.py",
        "--working-directory",
        str(resolve_src_dir(get_repo_root())),
        "--output-json",
        resolved_summary_path,
        "--output-lints-json",
        resolved_lints_path,
        "--deny-warnings",
        "--extra-clippy-arg=-W",
        "--extra-clippy-arg",
        "clippy::pedantic",
        "--quiet-json-stream",
        "--propagate-exit-code",
    ]


def maybe_emit_ai_guard_scaffold(
    *,
    with_ai_guard: bool,
    already_emitted: bool,
    failed_results: list[dict],
    run_cmd_fn,
    dry_run: bool,
    ai_guard_step_names: set[str] | frozenset[str],
) -> tuple[bool, dict | None]:
    """Create an audit scaffold when AI-guard checks fail."""
    if not with_ai_guard or already_emitted:
        return already_emitted, None

    failed_guard_steps = [result["name"] for result in failed_results if result["name"] in ai_guard_step_names]
    if not failed_guard_steps:
        return already_emitted, None

    scaffold_cmd = [
        "python3",
        "dev/scripts/devctl.py",
        "audit-scaffold",
        "--source-guards",
        "--force",
        "--yes",
        "--trigger",
        "check-ai-guard",
        "--trigger-steps",
        ",".join(failed_guard_steps),
    ]
    scaffold_result = run_cmd_fn(
        "audit-scaffold-auto",
        scaffold_cmd,
        cwd=REPO_ROOT,
        dry_run=dry_run,
    )
    return True, scaffold_result
