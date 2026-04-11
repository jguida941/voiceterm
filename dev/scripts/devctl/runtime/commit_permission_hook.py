"""Shared raw-git commit authority gate for pre-commit hook entrypoints."""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_STARTUP_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)


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

    return False, _blocked_lines(decision)


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
