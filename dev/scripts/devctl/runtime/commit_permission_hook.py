"""Shared raw-git commit authority gate for pre-commit hook entrypoints."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

DEFAULT_STARTUP_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
MANAGED_PROJECTION_RECEIPT_COMMIT_ENV = "DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT"


def evaluate_raw_git_commit_permission(
    repo_root: Path,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether a raw ``git commit`` is allowed plus any stderr lines."""
    try:
        from .commit_permission import build_commit_permission_decision
        from .startup_context import build_startup_context
    except Exception as exc:  # broad-except: allow reason=hook_fail_closed_import_boundary fallback=blocking_message
        return False, _load_error_lines(str(exc))

    try:
        startup_context = build_startup_context(repo_root=repo_root)
    except Exception as exc:  # broad-except: allow reason=hook_fail_closed_startup_boundary fallback=blocking_message
        return False, _load_error_lines(str(exc))

    decision = build_commit_permission_decision(startup_context)
    if decision.commit_permission != "blocked":
        return True, ()
    if completed_handoff_allows_managed_projection_commit(
        repo_root=repo_root,
        environ=os.environ,
    ):
        return True, ()

    return False, _blocked_lines(decision)


def completed_handoff_allows_managed_projection_commit(
    *,
    repo_root: Path,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Return True for hook-time managed projection receipts with handoff proof."""
    if not _env_flag_enabled(environ, MANAGED_PROJECTION_RECEIPT_COMMIT_ENV):
        return False
    if not _staged_paths_are_managed_projection_receipts(repo_root=repo_root):
        return False
    try:
        from .completed_handoff_authority import current_completed_handoff_outcome
    except Exception:  # broad-except: allow reason=hook handoff import must fail closed when runtime authority helpers are unavailable fallback=return False
        return False
    return current_completed_handoff_outcome(repo_root=repo_root) is not None


def _staged_paths_are_managed_projection_receipts(*, repo_root: Path) -> bool:
    """Return True when the staged commit only touches managed projection paths."""
    try:
        from .governance_scan import scan_repo_governance_safely
        from .review_snapshot_refresh import managed_receipt_relpaths
    except Exception:  # broad-except: allow reason=managed projection allowlist imports are optional at hook boundary fallback=return False
        return False
    try:
        governance = scan_repo_governance_safely(repo_root)
    except (OSError, ValueError):
        governance = None
    allowlist = set(managed_receipt_relpaths(repo_root=repo_root, governance=governance))
    staged_paths = _staged_paths(repo_root)
    return bool(allowlist and staged_paths) and all(
        path in allowlist for path in staged_paths
    )


def _staged_paths(repo_root: Path) -> tuple[str, ...]:
    try:
        from .vcs import run_git_capture
    except Exception:  # broad-except: allow reason=git helper import failure must block hook-time bypass fallback=return empty staged paths
        return ()
    code, stdout, _ = run_git_capture(
        ["diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        repo_root=repo_root,
    )
    if code != 0:
        return ()
    return tuple(line.strip() for line in stdout.splitlines() if line.strip())


def _env_flag_enabled(environ: Mapping[str, str] | None, name: str) -> bool:
    source = environ if environ is not None else os.environ
    return str(source.get(name, "") or "").strip() == "1"


def _load_error_lines(detail: str) -> tuple[str, ...]:
    text = detail.strip() or "unknown startup-context error"
    return (
        "[pre-commit hook] Unable to evaluate commit_permission; failing closed.",
        f"[pre-commit hook] error: {text}",
        f"[pre-commit hook] Next typed step: {DEFAULT_STARTUP_STATUS_COMMAND}",
    )


def _blocked_lines(decision) -> tuple[str, ...]:
    blockers = ", ".join(str(item).strip() for item in decision.blockers if str(item).strip())
    lines = [
        "[pre-commit hook] Raw git commit is blocked in this repo.",
        f"[pre-commit hook] Blockers: {blockers or 'unknown'}",
    ]
    if decision.recovery_action:
        lines.append(f"[pre-commit hook] Recovery: {decision.recovery_action}")
    if decision.escalation_action:
        lines.append(f"[pre-commit hook] Escalation: {decision.escalation_action}")
    lines.append(
        "[pre-commit hook] Next typed step: "
        f"{decision.next_command or DEFAULT_STARTUP_STATUS_COMMAND}"
    )
    return tuple(lines)


def main(argv: list[str] | None = None) -> int:
    """Evaluate the commit gate for the supplied repo root (or CWD)."""
    args = argv if argv is not None else sys.argv
    repo_root = Path(args[1]).resolve() if len(args) > 1 else Path.cwd().resolve()
    allowed, lines = evaluate_raw_git_commit_permission(repo_root)
    if allowed:
        return 0
    for line in lines:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover - exercised by shell hooks
    raise SystemExit(main())
