#!/usr/bin/env python3
"""Guard against non-regressive Rust security footguns in changed files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TODO_MACRO_RE = re.compile(r"\btodo!\s*\(")
UNIMPLEMENTED_MACRO_RE = re.compile(r"\bunimplemented!\s*\(")
DBG_MACRO_RE = re.compile(r"\bdbg!\s*\(")
SHELL_SPAWN_RE = re.compile(
    r"""\bCommand::new\s*\(\s*"(?:sh|bash|zsh|cmd|powershell|pwsh)"\s*\)""",
    re.IGNORECASE,
)
SHELL_CONTROL_FLAG_RE = re.compile(r"""\.arg\s*\(\s*"(?:-c|/C)"\s*\)""")
PERMISSIVE_MODE_RE = re.compile(r"\b0o(?:777|666)\b")
WEAK_CRYPTO_RE = re.compile(r"\b(?:md5|sha1)\b", re.IGNORECASE)
CHILD_ID_SIGNED_CAST_RE = re.compile(r"\bchild\.id\s*\(\s*\)\s*as\s+i(?:16|32|64)\b")
GETPID_SIGNED_CAST_RE = re.compile(r"\blibc::getpid\s*\(\s*\)\s*as\s+i(?:16|32|64)\b")
GETPID_BLOCK_SIGNED_CAST_RE = re.compile(
    r"unsafe\s*\{\s*libc::getpid\s*\(\s*\)\s*\}\s*as\s+i(?:16|32|64)\b"
)
SYSCALL_ASSIGN_RE = re.compile(
    r"let\s+(?:mut\s+)?(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=;]+)?=\s*[^;]*?"
    r"libc::(?:read|write|recv|send|pread|pwrite)\s*\([^;]*?;",
    re.DOTALL,
)
UNSIGNED_CAST_RE_TEMPLATE = r"\b{var}\s+as\s+(?:u(?:8|16|32|64|128)|usize)\b"
SIGN_GUARD_RE_TEMPLATE = (
    r"(?:if|while|assert!)\s*[!(]*\s*{var}\s*(?:[<>!=]=?)\s*0\b"
)


def _window_after_statement(text: str, start_index: int) -> str:
    remaining = text[start_index:]
    blank_line_index = remaining.find("\n\n")
    if blank_line_index >= 0:
        remaining = remaining[:blank_line_index]
    lines = remaining.splitlines()
    return "\n".join(lines[:20])


def _count_sign_unsafe_syscall_casts(text: str) -> int:
    findings = 0
    for match in SYSCALL_ASSIGN_RE.finditer(text):
        variable = match.group("var")
        window = _window_after_statement(text, match.end())
        cast_match = re.search(
            UNSIGNED_CAST_RE_TEMPLATE.format(var=re.escape(variable)),
            window,
        )
        if cast_match is None:
            continue
        prefix = window[: cast_match.start()]
        if re.search(
            SIGN_GUARD_RE_TEMPLATE.format(var=re.escape(variable)),
            prefix,
        ):
            continue
        findings += 1
    return findings


def _count_pid_signed_wrap_casts(text: str) -> int:
    return (
        len(CHILD_ID_SIGNED_CAST_RE.findall(text))
        + len(GETPID_SIGNED_CAST_RE.findall(text))
        + len(GETPID_BLOCK_SIGNED_CAST_RE.findall(text))
    )


def _count_metrics(text: str | None) -> dict[str, int]:
    if text is None:
        return {
            "todo_macro_calls": 0,
            "unimplemented_macro_calls": 0,
            "dbg_macro_calls": 0,
            "shell_spawn_calls": 0,
            "shell_control_flag_calls": 0,
            "permissive_mode_literals": 0,
            "weak_crypto_refs": 0,
            "pid_signed_wrap_casts": 0,
            "sign_unsafe_syscall_casts": 0,
        }
    text = strip_cfg_test_blocks(text)
    return {
        "todo_macro_calls": len(TODO_MACRO_RE.findall(text)),
        "unimplemented_macro_calls": len(UNIMPLEMENTED_MACRO_RE.findall(text)),
        "dbg_macro_calls": len(DBG_MACRO_RE.findall(text)),
        "shell_spawn_calls": len(SHELL_SPAWN_RE.findall(text)),
        "shell_control_flag_calls": len(SHELL_CONTROL_FLAG_RE.findall(text)),
        "permissive_mode_literals": len(PERMISSIVE_MODE_RE.findall(text)),
        "weak_crypto_refs": len(WEAK_CRYPTO_RE.findall(text)),
        "pid_signed_wrap_casts": _count_pid_signed_wrap_casts(text),
        "sign_unsafe_syscall_casts": _count_sign_unsafe_syscall_casts(text),
    }


def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _render_md(report: dict) -> str:
    lines = ["# check_rust_security_footguns", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_rust: {report['files_skipped_non_rust']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    totals = report["totals"]
    lines.append(
        "- aggregate_growth: "
        f"todo_macro_calls {totals['todo_macro_calls_growth']:+d}, "
        f"unimplemented_macro_calls {totals['unimplemented_macro_calls_growth']:+d}, "
        f"dbg_macro_calls {totals['dbg_macro_calls_growth']:+d}, "
        f"shell_spawn_calls {totals['shell_spawn_calls_growth']:+d}, "
        f"shell_control_flag_calls {totals['shell_control_flag_calls_growth']:+d}, "
        f"permissive_mode_literals {totals['permissive_mode_literals_growth']:+d}, "
        f"weak_crypto_refs {totals['weak_crypto_refs_growth']:+d}, "
        f"pid_signed_wrap_casts {totals['pid_signed_wrap_casts_growth']:+d}, "
        f"sign_unsafe_syscall_casts {totals['sign_unsafe_syscall_casts_growth']:+d}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: reduce risky patterns in changed files (prefer typed error paths, "
            "avoid shell `-c` execution paths, avoid permissive modes like `0o777`/`0o666`, "
            "avoid weak hashes such as MD5/SHA1, prefer checked/typed PID conversions over "
            "`as i32`, and guard signed syscall return values before any cast to unsigned "
            "types like `usize`)."
        )
        for item in report["violations"]:
            growth_bits = [
                f"{key} {value:+d}"
                for key, value in item["growth"].items()
                if value > 0
            ]
            lines.append(f"- `{item['path']}`: {', '.join(growth_bits)}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    return build_since_ref_format_parser(__doc__ or "")


def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error(
            "check_rust_security_footguns", args.format, str(exc)
        )

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {
        "todo_macro_calls_growth": 0,
        "unimplemented_macro_calls_growth": 0,
        "dbg_macro_calls_growth": 0,
        "shell_spawn_calls_growth": 0,
        "shell_control_flag_calls_growth": 0,
        "permissive_mode_literals_growth": 0,
        "weak_crypto_refs_growth": 0,
        "pid_signed_wrap_casts_growth": 0,
        "sign_unsafe_syscall_casts_growth": 0,
    }

    for path in changed_paths:
        if path.suffix != ".rs":
            files_skipped_non_rust += 1
            continue
        if _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1

        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)

        base = _count_metrics(base_text)
        current = _count_metrics(current_text)
        growth = _growth(base, current)

        totals["todo_macro_calls_growth"] += growth["todo_macro_calls"]
        totals["unimplemented_macro_calls_growth"] += growth[
            "unimplemented_macro_calls"
        ]
        totals["dbg_macro_calls_growth"] += growth["dbg_macro_calls"]
        totals["shell_spawn_calls_growth"] += growth["shell_spawn_calls"]
        totals["shell_control_flag_calls_growth"] += growth["shell_control_flag_calls"]
        totals["permissive_mode_literals_growth"] += growth["permissive_mode_literals"]
        totals["weak_crypto_refs_growth"] += growth["weak_crypto_refs"]
        totals["pid_signed_wrap_casts_growth"] += growth["pid_signed_wrap_casts"]
        totals["sign_unsafe_syscall_casts_growth"] += growth[
            "sign_unsafe_syscall_casts"
        ]

        if _has_positive_growth(growth):
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    report = {
        "command": "check_rust_security_footguns",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_rust": files_skipped_non_rust,
        "files_skipped_tests": files_skipped_tests,
        "totals": totals,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
