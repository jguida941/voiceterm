#!/usr/bin/env python3
"""Guard against non-regressive Rust best-practice drift in changed files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from check_bootstrap import emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import emit_runtime_error, import_attr, utc_timestamp

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

ALLOW_ATTR_RE = re.compile(r"#\s*\[\s*allow\s*\((?P<body>[^\]]*)\)\s*\]", re.DOTALL)
ALLOW_REASON_RE = re.compile(r"\breason\s*=")
UNSAFE_BLOCK_RE = re.compile(r"\bunsafe\s*\{")
UNSAFE_FN_RE = re.compile(r"\bunsafe\s+fn\b")
PUB_UNSAFE_FN_RE = re.compile(r"\bpub(?:\s*\([^\)]*\))?\s+unsafe\s+fn\b")
UNSAFE_IMPL_RE = re.compile(r"\bunsafe\s+impl\b")
MEM_FORGET_RE = re.compile(r"\b(?:std::mem::forget|mem::forget)\s*\(")
RESULT_STRING_RE = re.compile(r"Result\s*<[^>]*,\s*String\s*>")
EXPECT_JOIN_RECV_RE = re.compile(
    r"\.\s*(?:join|recv|recv_timeout)\s*\([^)]*\)\s*\.\s*expect\s*\("
)
UNWRAP_JOIN_RECV_RE = re.compile(
    r"\.\s*(?:join|recv|recv_timeout)\s*\([^)]*\)\s*\.\s*unwrap\s*\("
)
DROPPED_SEND_RESULT_RE = re.compile(
    r"(?:let\s+_|\b_\s*=)\s*[^;\n]*\.\s*(?:send|send_timeout|try_send|blocking_send)\s*\("
)
DROPPED_EMIT_RESULT_RE = re.compile(
    r"(?:let\s+_|\b_\s*=)\s*[^;\n]*\.\s*emit\s*\("
)
THREAD_SPAWN_RE = re.compile(r"\b(?:std::thread::spawn|thread::spawn)\s*\(")
DETACHED_THREAD_ALLOW_RE = re.compile(
    r"detached-thread:\s*allow\s+reason\s*=",
    re.IGNORECASE,
)
ENV_MUTATION_RE = re.compile(r"\b(?:std::)?env::(?:set_var|remove_var)\s*\(")
OPEN_OPTIONS_NEW_RE = re.compile(r"\b(?:std::fs::|fs::)?OpenOptions::new\s*\(\)")
OPEN_OPTIONS_OPEN_RE = re.compile(r"\.\s*open\s*\(")
CREATE_TRUE_RE = re.compile(r"\.\s*create\s*\(\s*true\s*\)")
CREATE_NEW_TRUE_RE = re.compile(r"\.\s*create_new\s*\(\s*true\s*\)")
APPEND_TRUE_RE = re.compile(r"\.\s*append\s*\(\s*true\s*\)")
TRUNCATE_EXPLICIT_RE = re.compile(r"\.\s*truncate\s*\(\s*(?:true|false)\s*\)")
WRITE_TRUE_RE = re.compile(r"\.\s*write\s*\(\s*true\s*\)")
FLOAT_LITERAL_COMPARISON_RE = re.compile(
    r"(?:==|!=)\s*-?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?(?:_f(?:32|64)|f(?:32|64))?\b|"
    r"\b-?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?(?:_f(?:32|64)|f(?:32|64))?\s*(?:==|!=)"
)
STRING_LITERAL_RE = re.compile(r'"(?:\\.|[^"\\])*"')
DIRECT_FS_WRITE_RE = re.compile(
    r"\b(?:std::fs::|fs::)?write\s*\(\s*(?P<path_expr>[^,\n]+?)\s*,",
    re.DOTALL,
)
FILE_CREATE_RE = re.compile(
    r"\b(?:std::fs::|fs::)?File::create\s*\(\s*(?P<path_expr>[^)\n]+?)\s*\)"
)
OPEN_CALL_RE = re.compile(r"\.\s*open\s*\(\s*(?P<path_expr>[^)\n]+?)\s*\)")
PERSISTENT_TOML_SCOPE_PATHS = {
    "rust/src/bin/voiceterm/persistent_config.rs",
    "rust/src/bin/voiceterm/onboarding.rs",
    "rust/src/bin/voiceterm/theme_studio/export_page.rs",
}
CUSTOM_TOML_PARSER_SCOPE_PATHS = {
    "rust/src/bin/voiceterm/persistent_config.rs",
    "rust/src/bin/voiceterm/onboarding.rs",
}
PARSER_FUNCTION_RE = re.compile(r"\bfn\s+(?P<name>parse_[A-Za-z0-9_]+)\s*\(")
MANUAL_TOML_SPLIT_RE = re.compile(
    r"split_once\(\s*'='\s*\)|split\(\s*'='\s*\)\.nth\(\s*\d+\s*\)"
)
MANUAL_TOML_VALUE_RE = re.compile(r"trim_matches\(\s*'\"'\s*\)|strip_prefix\(")
FUNCTION_SIGNATURE_RE = re.compile(r"\bfn\s+[A-Za-z0-9_]+\s*\(")
JOIN_HANDLE_RETURN_RE = re.compile(r"->\s*(?:std::thread::|thread::)?JoinHandle\s*<")
METRIC_KEYS = (
    "allow_without_reason",
    "undocumented_unsafe_blocks",
    "pub_unsafe_fn_missing_safety_docs",
    "unsafe_impl_missing_safety_comment",
    "mem_forget_calls",
    "result_string_types",
    "expect_on_join_recv",
    "unwrap_on_join_recv",
    "dropped_send_results",
    "dropped_emit_results",
    "detached_thread_spawns",
    "env_mutation_calls",
    "suspicious_open_options",
    "float_literal_comparisons",
    "nonatomic_persistent_toml_writes",
    "custom_persistent_toml_parsers",
)


def _count_allow_without_reason(text: str | None) -> int:
    if text is None:
        return 0
    count = 0
    for match in ALLOW_ATTR_RE.finditer(text):
        body = match.group("body")
        if not ALLOW_REASON_RE.search(body):
            count += 1
    return count


def _has_nearby_safety_comment(lines: list[str], index: int, lookback: int = 5) -> bool:
    min_index = max(0, index - lookback)
    for probe in range(index - 1, min_index - 1, -1):
        raw = lines[probe].strip()
        if not raw:
            continue
        if "SAFETY:" in raw or "# Safety" in raw:
            return True
        if raw.startswith(("//", "/*", "*", "///", "//!", "#[")):
            continue
        break
    return False


def _count_undocumented_unsafe_blocks(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not UNSAFE_BLOCK_RE.search(line):
            continue
        if UNSAFE_FN_RE.search(line):
            # `unsafe fn ... {` is tracked by the missing safety-docs metric below.
            continue
        if not _has_nearby_safety_comment(lines, index):
            count += 1
    return count


def _public_unsafe_fn_missing_safety_docs(lines: list[str], index: int) -> bool:
    saw_doc = False
    saw_safety_heading = False
    probe = index - 1
    while probe >= 0:
        raw = lines[probe].strip()
        if not raw:
            if saw_doc:
                break
            probe -= 1
            continue
        if raw.startswith("#["):
            probe -= 1
            continue
        if raw.startswith("///"):
            saw_doc = True
            if "# Safety" in raw:
                saw_safety_heading = True
            probe -= 1
            continue
        break
    return not (saw_doc and saw_safety_heading)


def _count_pub_unsafe_fn_missing_safety_docs(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not PUB_UNSAFE_FN_RE.search(line):
            continue
        if _public_unsafe_fn_missing_safety_docs(lines, index):
            count += 1
    return count


def _count_unsafe_impl_missing_safety_comment(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not UNSAFE_IMPL_RE.search(line):
            continue
        if not _has_nearby_safety_comment(lines, index):
            count += 1
    return count


def _count_mem_forget_calls(text: str | None) -> int:
    if text is None:
        return 0
    return len(MEM_FORGET_RE.findall(text))


def _count_result_string(text: str | None) -> int:
    if text is None:
        return 0
    return len(RESULT_STRING_RE.findall(text))


def _count_expect_on_join_recv(text: str | None) -> int:
    if text is None:
        return 0
    return len(EXPECT_JOIN_RECV_RE.findall(text))


def _count_unwrap_on_join_recv(text: str | None) -> int:
    if text is None:
        return 0
    return len(UNWRAP_JOIN_RECV_RE.findall(text))


def _count_dropped_send_results(text: str | None) -> int:
    if text is None:
        return 0
    return len(DROPPED_SEND_RESULT_RE.findall(text))


def _count_dropped_emit_results(text: str | None) -> int:
    if text is None:
        return 0
    return len(DROPPED_EMIT_RESULT_RE.findall(text))


def _enclosing_function_returns_join_handle(
    lines: list[str],
    index: int,
    lookahead: int = 12,
) -> bool:
    for probe in range(index, -1, -1):
        if FUNCTION_SIGNATURE_RE.search(lines[probe]) is None:
            continue
        window = " ".join(
            line.strip() for line in lines[probe : min(len(lines), probe + lookahead)]
        )
        return JOIN_HANDLE_RETURN_RE.search(window) is not None
    return False


def _has_detached_thread_allow(lines: list[str], index: int, lookback: int = 2) -> bool:
    min_index = max(0, index - lookback)
    for probe in range(index, min_index - 1, -1):
        if DETACHED_THREAD_ALLOW_RE.search(lines[probe]):
            return True
    return False


def _collect_spawn_statement(
    lines: list[str],
    *,
    start_index: int,
    start_column: int,
    max_lines: int = 40,
) -> str:
    statement_parts: list[str] = []
    depth = 0
    for probe in range(start_index, min(len(lines), start_index + max_lines)):
        code = lines[probe].split("//", 1)[0]
        segment = code[start_column:] if probe == start_index else code
        segment = STRING_LITERAL_RE.sub('""', segment)
        statement_parts.append(segment)
        top_level_semicolon = False
        for char in segment:
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth = max(0, depth - 1)
            elif char == ";" and depth == 0:
                top_level_semicolon = True
                break
        if top_level_semicolon:
            return "\n".join(statement_parts)
        if depth == 0 and segment.strip().endswith((")", "})")):
            return "\n".join(statement_parts)
    return "\n".join(statement_parts)


def _count_detached_thread_spawns(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    findings = 0
    for index, raw_line in enumerate(lines):
        code = raw_line.split("//", 1)[0]
        match = THREAD_SPAWN_RE.search(code)
        if match is None:
            continue
        if code[: match.start()].strip():
            continue
        if _enclosing_function_returns_join_handle(lines, index):
            continue
        if _has_detached_thread_allow(lines, index):
            continue
        statement = _collect_spawn_statement(
            lines,
            start_index=index,
            start_column=match.start(),
        ).strip()
        if statement.endswith(";"):
            findings += 1
    return findings


def _count_env_mutation_calls(text: str | None) -> int:
    if text is None:
        return 0
    return len(ENV_MUTATION_RE.findall(text))


def _open_options_window(text: str, start_index: int, max_lines: int = 12) -> str:
    lines: list[str] = []
    for raw in text[start_index:].splitlines():
        stripped = raw.strip()
        if not stripped and lines:
            break
        lines.append(raw)
        window = "\n".join(lines)
        if OPEN_OPTIONS_OPEN_RE.search(window):
            break
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def _count_suspicious_open_options(text: str | None) -> int:
    if text is None:
        return 0
    findings = 0
    for match in OPEN_OPTIONS_NEW_RE.finditer(text):
        window = _open_options_window(text, match.start())
        if not OPEN_OPTIONS_OPEN_RE.search(window):
            continue
        if not CREATE_TRUE_RE.search(window):
            continue
        if CREATE_NEW_TRUE_RE.search(window):
            continue
        if APPEND_TRUE_RE.search(window):
            continue
        if TRUNCATE_EXPLICIT_RE.search(window):
            continue
        findings += 1
    return findings


def _count_float_literal_comparisons(text: str | None) -> int:
    if text is None:
        return 0
    findings = 0
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(("//", "///", "//!")):
            continue
        code = raw_line.split("//", 1)[0]
        code = STRING_LITERAL_RE.sub('""', code)
        findings += len(FLOAT_LITERAL_COMPARISON_RE.findall(code))
    return findings


def _is_persistent_toml_scope(text: str | None, *, path: Path | None) -> bool:
    relative_path = path.as_posix() if path is not None else ""
    if relative_path in PERSISTENT_TOML_SCOPE_PATHS:
        return True
    if text is None:
        return False
    lowered = text.lower()
    return ".toml" in lowered and (
        "save_" in text
        or "config_file_path" in text
        or "onboarding_state_path" in text
        or "ensure_theme_dir" in text
        or "export_theme_file" in text
        or "persistent config" in lowered
    )


def _looks_temp_path_expr(path_expr: str) -> bool:
    lowered = path_expr.lower()
    return "temp" in lowered or "tmp" in lowered


def _count_nonatomic_persistent_toml_writes(
    text: str | None,
    *,
    path: Path | None,
) -> int:
    if text is None or not _is_persistent_toml_scope(text, path=path):
        return 0

    findings = 0
    for match in DIRECT_FS_WRITE_RE.finditer(text):
        if _looks_temp_path_expr(match.group("path_expr")):
            continue
        findings += 1

    for match in FILE_CREATE_RE.finditer(text):
        if _looks_temp_path_expr(match.group("path_expr")):
            continue
        findings += 1

    for match in OPEN_OPTIONS_NEW_RE.finditer(text):
        window = _open_options_window(text, match.start(), max_lines=16)
        if not OPEN_OPTIONS_OPEN_RE.search(window):
            continue
        if not WRITE_TRUE_RE.search(window):
            continue
        if not TRUNCATE_EXPLICIT_RE.search(window):
            continue
        open_match = OPEN_CALL_RE.search(window)
        if open_match is not None and _looks_temp_path_expr(open_match.group("path_expr")):
            continue
        findings += 1

    return findings


def _function_window(text: str, start_index: int, max_lines: int = 40) -> str:
    return "\n".join(text[start_index:].splitlines()[:max_lines])


def _is_custom_toml_parser_scope(text: str | None, *, path: Path | None) -> bool:
    relative_path = path.as_posix() if path is not None else ""
    if relative_path in CUSTOM_TOML_PARSER_SCOPE_PATHS:
        return True
    if text is None:
        return False
    lowered = text.lower()
    return ".toml" in lowered and "read_to_string" in text and "parse_" in text


def _looks_like_custom_toml_parser(window: str) -> bool:
    if "toml::from_str" in window:
        return False
    if MANUAL_TOML_SPLIT_RE.search(window):
        return True
    return "lines()" in window and (
        MANUAL_TOML_VALUE_RE.search(window) is not None
        or "parse_toml_value(" in window
    )


def _count_custom_persistent_toml_parsers(
    text: str | None,
    *,
    path: Path | None,
) -> int:
    if text is None or not _is_custom_toml_parser_scope(text, path=path):
        return 0
    findings = 0
    for match in PARSER_FUNCTION_RE.finditer(text):
        window = _function_window(text, match.start())
        if _looks_like_custom_toml_parser(window):
            findings += 1
    return findings


def _count_metrics(text: str | None, *, path: Path | None = None) -> dict[str, int]:
    if text is not None:
        text = strip_cfg_test_blocks(text)
    return {
        "allow_without_reason": _count_allow_without_reason(text),
        "undocumented_unsafe_blocks": _count_undocumented_unsafe_blocks(text),
        "pub_unsafe_fn_missing_safety_docs": _count_pub_unsafe_fn_missing_safety_docs(
            text
        ),
        "unsafe_impl_missing_safety_comment": _count_unsafe_impl_missing_safety_comment(
            text
        ),
        "mem_forget_calls": _count_mem_forget_calls(text),
        "result_string_types": _count_result_string(text),
        "expect_on_join_recv": _count_expect_on_join_recv(text),
        "unwrap_on_join_recv": _count_unwrap_on_join_recv(text),
        "dropped_send_results": _count_dropped_send_results(text),
        "dropped_emit_results": _count_dropped_emit_results(text),
        "detached_thread_spawns": _count_detached_thread_spawns(text),
        "env_mutation_calls": _count_env_mutation_calls(text),
        "suspicious_open_options": _count_suspicious_open_options(text),
        "float_literal_comparisons": _count_float_literal_comparisons(text),
        "nonatomic_persistent_toml_writes": _count_nonatomic_persistent_toml_writes(
            text,
            path=path,
        ),
        "custom_persistent_toml_parsers": _count_custom_persistent_toml_parsers(
            text,
            path=path,
        ),
    }


def _list_all_rust_paths() -> list[Path]:
    paths: set[Path] = set()
    tracked = guard.run_git(["git", "ls-files"]).stdout.splitlines()
    untracked = guard.run_git(
        ["git", "ls-files", "--others", "--exclude-standard"]
    ).stdout.splitlines()
    for raw in [*tracked, *untracked]:
        if not raw.strip():
            continue
        path = Path(raw.strip())
        if path.suffix != ".rs" or _is_test_path(path):
            continue
        paths.add(path)
    return sorted(paths)


def _resolve_scan_targets(
    args: argparse.Namespace,
) -> tuple[list[Path], dict[Path, Path], str]:
    if args.absolute and args.since_ref:
        raise RuntimeError("--absolute cannot be combined with --since-ref/--head-ref")

    if args.absolute:
        return _list_all_rust_paths(), {}, "absolute"

    if args.since_ref:
        guard.validate_ref(args.since_ref)
        guard.validate_ref(args.head_ref)

    changed_paths, base_map = list_changed_paths_with_base_map(
        guard.run_git,
        args.since_ref,
        args.head_ref,
    )
    mode = "commit-range" if args.since_ref else "working-tree"
    return changed_paths, base_map, mode


def _read_path_pair(
    *,
    path: Path,
    base_map: dict[Path, Path],
    absolute: bool,
    since_ref: str | None,
    head_ref: str,
) -> tuple[str | None, str | None]:
    if absolute:
        return None, guard.read_text_from_worktree(path)

    base_path = base_map.get(path, path)
    if since_ref:
        return (
            guard.read_text_from_ref(base_path, since_ref),
            guard.read_text_from_ref(path, head_ref),
        )
    return (
        guard.read_text_from_ref(base_path, "HEAD"),
        guard.read_text_from_worktree(path),
    )


def _growth_from_metrics(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {metric: current[metric] - base[metric] for metric in METRIC_KEYS}


def _empty_growth_totals() -> dict[str, int]:
    return {f"{metric}_growth": 0 for metric in METRIC_KEYS}


def _accumulate_growth_totals(totals: dict[str, int], growth: dict[str, int]) -> None:
    for metric, value in growth.items():
        totals[f"{metric}_growth"] += value


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _scan_paths(
    *,
    changed_paths: list[Path],
    base_map: dict[Path, Path],
    absolute: bool,
    since_ref: str | None,
    head_ref: str,
) -> dict:
    files_considered = 0
    files_skipped_non_rust = 0
    files_skipped_tests = 0
    totals = _empty_growth_totals()
    violations: list[dict] = []

    for path in changed_paths:
        if path.suffix != ".rs":
            files_skipped_non_rust += 1
            continue
        if _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1
        base_path = base_map.get(path, path)
        base_text, current_text = _read_path_pair(
            path=path,
            base_map=base_map,
            absolute=absolute,
            since_ref=since_ref,
            head_ref=head_ref,
        )
        base = _count_metrics(base_text, path=base_path)
        current = _count_metrics(current_text, path=path)
        growth = _growth_from_metrics(base, current)
        _accumulate_growth_totals(totals, growth)

        if _has_positive_growth(growth):
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    return {
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_rust": files_skipped_non_rust,
        "files_skipped_tests": files_skipped_tests,
        "totals": totals,
        "violations": violations,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_rust_best_practices", ""]
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
        f"allow_without_reason {totals['allow_without_reason_growth']:+d}, "
        f"undocumented_unsafe_blocks {totals['undocumented_unsafe_blocks_growth']:+d}, "
        "pub_unsafe_fn_missing_safety_docs "
        f"{totals['pub_unsafe_fn_missing_safety_docs_growth']:+d}, "
        "unsafe_impl_missing_safety_comment "
        f"{totals['unsafe_impl_missing_safety_comment_growth']:+d}, "
        f"mem_forget_calls {totals['mem_forget_calls_growth']:+d}, "
        f"result_string_types {totals['result_string_types_growth']:+d}, "
        f"expect_on_join_recv {totals['expect_on_join_recv_growth']:+d}, "
        f"unwrap_on_join_recv {totals['unwrap_on_join_recv_growth']:+d}, "
        f"dropped_send_results {totals['dropped_send_results_growth']:+d}, "
        f"dropped_emit_results {totals['dropped_emit_results_growth']:+d}, "
        f"detached_thread_spawns {totals['detached_thread_spawns_growth']:+d}, "
        f"env_mutation_calls {totals['env_mutation_calls_growth']:+d}, "
        f"suspicious_open_options {totals['suspicious_open_options_growth']:+d}, "
        "float_literal_comparisons "
        f"{totals['float_literal_comparisons_growth']:+d}, "
        "nonatomic_persistent_toml_writes "
        f"{totals['nonatomic_persistent_toml_writes_growth']:+d}, "
        "custom_persistent_toml_parsers "
        f"{totals['custom_persistent_toml_parsers_growth']:+d}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for item in report["violations"]:
            growth = item["growth"]
            lines.append(
                f"- `{item['path']}`: allow_without_reason "
                f"{item['base']['allow_without_reason']} -> "
                f"{item['current']['allow_without_reason']} "
                f"({growth['allow_without_reason']:+d}), "
                "undocumented_unsafe_blocks "
                f"{item['base']['undocumented_unsafe_blocks']} -> "
                f"{item['current']['undocumented_unsafe_blocks']} "
                f"({growth['undocumented_unsafe_blocks']:+d}), "
                "pub_unsafe_fn_missing_safety_docs "
                f"{item['base']['pub_unsafe_fn_missing_safety_docs']} -> "
                f"{item['current']['pub_unsafe_fn_missing_safety_docs']} "
                f"({growth['pub_unsafe_fn_missing_safety_docs']:+d}), "
                "unsafe_impl_missing_safety_comment "
                f"{item['base']['unsafe_impl_missing_safety_comment']} -> "
                f"{item['current']['unsafe_impl_missing_safety_comment']} "
                f"({growth['unsafe_impl_missing_safety_comment']:+d}), "
                f"mem_forget_calls {item['base']['mem_forget_calls']} -> "
                f"{item['current']['mem_forget_calls']} "
                f"({growth['mem_forget_calls']:+d}), "
                f"result_string_types {item['base']['result_string_types']} -> "
                f"{item['current']['result_string_types']} "
                f"({growth['result_string_types']:+d}), "
                f"expect_on_join_recv {item['base']['expect_on_join_recv']} -> "
                f"{item['current']['expect_on_join_recv']} "
                f"({growth['expect_on_join_recv']:+d}), "
                f"unwrap_on_join_recv {item['base']['unwrap_on_join_recv']} -> "
                f"{item['current']['unwrap_on_join_recv']} "
                f"({growth['unwrap_on_join_recv']:+d}), "
                f"dropped_send_results {item['base']['dropped_send_results']} -> "
                f"{item['current']['dropped_send_results']} "
                f"({growth['dropped_send_results']:+d}), "
                f"dropped_emit_results {item['base']['dropped_emit_results']} -> "
                f"{item['current']['dropped_emit_results']} "
                f"({growth['dropped_emit_results']:+d}), "
                "detached_thread_spawns "
                f"{item['base']['detached_thread_spawns']} -> "
                f"{item['current']['detached_thread_spawns']} "
                f"({growth['detached_thread_spawns']:+d}), "
                f"env_mutation_calls {item['base']['env_mutation_calls']} -> "
                f"{item['current']['env_mutation_calls']} "
                f"({growth['env_mutation_calls']:+d}), "
                "suspicious_open_options "
                f"{item['base']['suspicious_open_options']} -> "
                f"{item['current']['suspicious_open_options']} "
                f"({growth['suspicious_open_options']:+d}), "
                "float_literal_comparisons "
                f"{item['base']['float_literal_comparisons']} -> "
                f"{item['current']['float_literal_comparisons']} "
                f"({growth['float_literal_comparisons']:+d}), "
                "nonatomic_persistent_toml_writes "
                f"{item['base']['nonatomic_persistent_toml_writes']} -> "
                f"{item['current']['nonatomic_persistent_toml_writes']} "
                f"({growth['nonatomic_persistent_toml_writes']:+d}), "
                "custom_persistent_toml_parsers "
                f"{item['base']['custom_persistent_toml_parsers']} -> "
                f"{item['current']['custom_persistent_toml_parsers']} "
                f"({growth['custom_persistent_toml_parsers']:+d})"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Scan all tracked/untracked non-test Rust files instead of changed paths.",
    )
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        changed_paths, base_map, mode = _resolve_scan_targets(args)
        scan_report = _scan_paths(
            changed_paths=changed_paths,
            base_map=base_map,
            absolute=args.absolute,
            since_ref=args.since_ref,
            head_ref=args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error("check_rust_best_practices", args.format, str(exc))

    report = {
        "command": "check_rust_best_practices",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(scan_report["violations"]) == 0,
        **scan_report,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
