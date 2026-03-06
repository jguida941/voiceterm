"""Shared helpers for `devctl check`."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import REPO_ROOT
from ..script_catalog import check_script_cmd

AI_GUARD_CHECKS = (
    ("code-shape-guard", "code_shape", ()),
    ("duplicate-types-guard", "duplicate_types", ()),
    ("structural-complexity-guard", "structural_complexity", ()),
    ("rust-test-shape-guard", "rust_test_shape", ()),
    (
        "ide-provider-isolation-guard",
        "ide_provider_isolation",
        ("--fail-on-violations",),
    ),
    ("compat-matrix-guard", "compat_matrix", ()),
    ("compat-matrix-smoke-guard", "compat_matrix_smoke", ()),
    ("naming-consistency-guard", "naming_consistency", ()),
    (
        "rust-lint-debt-guard",
        "rust_lint_debt",
        ("--report-dead-code", "--dead-code-report-limit", "120"),
    ),
    ("rust-best-practices-guard", "rust_best_practices", ()),
    ("rust-runtime-panic-policy-guard", "rust_runtime_panic_policy", ()),
    ("rust-audit-patterns-guard", "rust_audit_patterns", ()),
    ("rust-security-footguns-guard", "rust_security_footguns", ()),
)

AI_GUARD_STEP_NAMES = {name for name, _script_id, _extra_args in AI_GUARD_CHECKS}
AI_GUARD_COMMIT_RANGE_SCRIPT_IDS = frozenset(
    {
        "code_shape",
        "duplicate_types",
        "structural_complexity",
        "rust_test_shape",
        "rust_lint_debt",
        "rust_best_practices",
        "rust_runtime_panic_policy",
        "rust_audit_patterns",
        "rust_security_footguns",
    }
)

CLIPPY_HIGH_SIGNAL_LINTS_PATH = REPO_ROOT / "dev/reports/check/clippy-lints.json"


def build_ai_guard_cmd(
    script_id: str,
    *,
    since_ref: str | None,
    head_ref: str,
    extra_args: tuple[str, ...] = (),
) -> list[str]:
    """Build one AI-guard command with optional commit-range refs."""
    cmd = check_script_cmd(script_id, *extra_args)
    if since_ref and script_id in AI_GUARD_COMMIT_RANGE_SCRIPT_IDS:
        cmd.extend(["--since-ref", since_ref, "--head-ref", head_ref])
    return cmd


def resolve_perf_log_path() -> str:
    """Return the expected perf log file path used by the verifier script."""
    try:
        return subprocess.check_output(
            [
                "python3",
                "-c",
                "import os, tempfile; print(os.path.join(tempfile.gettempdir(), 'voiceterm_tui.log'))",
            ],
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"failed to resolve perf log path ({exc})") from exc


def build_clippy_high_signal_collect_cmd() -> list[str]:
    """Build the strict clippy lint-histogram collection command."""
    return [
        "python3",
        "dev/scripts/collect_clippy_warnings.py",
        "--working-directory",
        "rust",
        "--output-lints-json",
        str(CLIPPY_HIGH_SIGNAL_LINTS_PATH),
        "--deny-warnings",
        "--quiet-json-stream",
        "--propagate-exit-code",
    ]


def build_clippy_high_signal_guard_cmd() -> list[str]:
    """Build the high-signal lint baseline guard command."""
    return check_script_cmd(
        "clippy_high_signal",
        "--input-lints-json",
        str(CLIPPY_HIGH_SIGNAL_LINTS_PATH),
        "--format",
        "md",
    )


def maybe_emit_ai_guard_scaffold(
    *,
    with_ai_guard: bool,
    already_emitted: bool,
    failed_results: list[dict],
    run_cmd_fn,
    repo_root: Path,
    dry_run: bool,
) -> tuple[bool, dict | None]:
    """Create an audit scaffold when AI-guard checks fail."""
    if not with_ai_guard or already_emitted:
        return already_emitted, None

    failed_guard_steps = [
        result["name"] for result in failed_results if result["name"] in AI_GUARD_STEP_NAMES
    ]
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
        cwd=repo_root,
        dry_run=dry_run,
    )
    return True, scaffold_result
