"""Shared helpers for `devctl check`."""

from __future__ import annotations

import subprocess
from pathlib import Path

AI_GUARD_CHECKS = (
    ("code-shape-guard", "code_shape"),
    ("rust-lint-debt-guard", "rust_lint_debt"),
    ("rust-best-practices-guard", "rust_best_practices"),
    ("rust-audit-patterns-guard", "rust_audit_patterns"),
    ("rust-security-footguns-guard", "rust_security_footguns"),
)

AI_GUARD_STEP_NAMES = {name for name, _script_id in AI_GUARD_CHECKS}


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
