#!/usr/bin/env python3
"""Review probe: detect concurrency risk patterns in Rust source files.

This probe always exits 0. It emits structured risk hints for AI review
instead of blocking CI.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from dev.scripts.checks.probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_rust_test_path = import_attr("rust_guard_common", "is_test_path")
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "concurrency"

# Per-signal-type AI instructions for targeted review guidance.
AI_INSTRUCTIONS = {
    "nested_locks": (
        "Check lock acquisition order for deadlock risk. Verify that "
        "all callers acquire locks in the same order, and that no "
        "lock is held across an await point or fallible operation."
    ),
    "arc_mutex_spawn": (
        "Review shared mutable state crossing a spawn boundary. "
        "Verify the lock is not held across await points, the "
        "critical section is minimal, and contention is bounded."
    ),
    "atomic_relaxed_multi_flag": (
        "Multiple AtomicBool flags with Relaxed ordering may miss "
        "cross-flag coordination. Verify flags are truly independent "
        "and that no flag observation guards access to shared data."
    ),
    "poison_recovery": (
        "Lock poisoning recovery via into_inner() silently continues "
        "with potentially stale state. Verify the protected data is "
        "simple enough that poison recovery is safe, or add explicit "
        "error handling."
    ),
}
DEFAULT_AI_INSTRUCTION = (
    "Review for ordering issues, stale reads, unsynchronized state "
    "transitions, and deadlock risk from nested lock acquisitions."
)

# Patterns that indicate concurrency risk.
ARC_MUTEX_RE = re.compile(r"Arc\s*<\s*(Mutex|RwLock)\s*<")
LOCK_CALL_RE = re.compile(r"\.(lock|read|write)\s*\(\s*\)")
ATOMIC_RELAXED_RE = re.compile(r"Ordering::Relaxed")
ATOMIC_BOOL_RE = re.compile(r"AtomicBool")
ATOMIC_FLAG_DECL_RE = re.compile(r"Arc\s*<\s*AtomicBool\s*>")
TOKIO_SPAWN_RE = re.compile(r"tokio::(spawn|task::spawn)")
THREAD_SPAWN_RE = re.compile(r"thread::spawn")
POISONED_RECOVERY_RE = re.compile(r"poisoned.*into_inner|lock_or_recover")


def _count_lock_calls_in_scope(lines: list[str], start: int, end: int) -> int:
    """Count distinct lock/read/write calls within a line range."""
    count = 0
    for line in lines[start:end]:
        count += len(LOCK_CALL_RE.findall(line))
    return count


def _scan_file(text: str, path: Path) -> list[RiskHint]:
    """Scan one Rust file for concurrency risk patterns."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel_path = path.as_posix()

    for func in functions:
        start = func["start_line"] - 1
        end = func["end_line"]
        func_name = func["name"]
        func_text = "\n".join(lines[start:end])
        signals: list[str] = []
        signal_key: str | None = None

        # Nested lock acquisitions (deadlock risk) — HIGH severity.
        lock_count = _count_lock_calls_in_scope(lines, start, end)
        if lock_count >= 2:
            signals.append(f"{lock_count} lock/read/write calls in same function scope")
            signal_key = "nested_locks"

        # Arc<Mutex> or Arc<RwLock> with spawn — shared mutable state
        # crosses a task boundary, which is a real ownership concern.
        has_arc_mutex = bool(ARC_MUTEX_RE.search(func_text))
        has_spawn = bool(TOKIO_SPAWN_RE.search(func_text)) or bool(THREAD_SPAWN_RE.search(func_text))
        if has_arc_mutex and has_spawn:
            signals.append("Arc<Mutex/RwLock> shared with spawned task")
            signal_key = signal_key or "arc_mutex_spawn"

        # Multi-flag AtomicBool with Relaxed ordering — only flag when
        # >=2 distinct Arc<AtomicBool> parameters/bindings exist, which
        # indicates cross-flag coordination concerns. Single unidirectional
        # flags with Relaxed are idiomatic and safe.
        atomic_flag_count = len(ATOMIC_FLAG_DECL_RE.findall(func_text))
        if atomic_flag_count >= 2 and ATOMIC_RELAXED_RE.search(func_text):
            signals.append(
                f"{atomic_flag_count} Arc<AtomicBool> flags with Ordering::Relaxed " f"(verify flags are independent)"
            )
            signal_key = signal_key or "atomic_relaxed_multi_flag"

        # Lock poisoning recovery (may continue with stale state).
        if POISONED_RECOVERY_RE.search(func_text):
            signals.append("Lock poisoning recovery via into_inner()")
            signal_key = signal_key or "poison_recovery"

        if signals:
            severity = "high" if lock_count >= 2 else "medium"
            ai_instruction = AI_INSTRUCTIONS.get(signal_key or "", DEFAULT_AI_INSTRUCTION)
            hints.append(
                RiskHint(
                    file=rel_path,
                    symbol=func_name,
                    risk_type="concurrency_risk",
                    severity=severity,
                    signals=signals,
                    ai_instruction=ai_instruction,
                    review_lens=REVIEW_LENS,
                )
            )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_concurrency")

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError:
        return emit_probe_report(report, output_format=args.format)

    report.mode = "commit-range" if args.since_ref else "working-tree"
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    files_with_hints: set[str] = set()

    for path in changed_paths:
        if path.suffix != ".rs":
            continue
        if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS):
            continue
        if is_rust_test_path(path):
            continue

        report.files_scanned += 1
        if args.since_ref:
            text = guard.read_text_from_ref(path, args.head_ref)
        else:
            text = guard.read_text_from_worktree(path)

        if text is None:
            continue

        hints = _scan_file(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
