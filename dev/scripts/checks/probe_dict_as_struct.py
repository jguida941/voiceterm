#!/usr/bin/env python3
"""Review probe: detect functions returning dicts that should be dataclasses.

AI coding assistants frequently return plain dicts with 5+ keys instead of
defining typed models. This defeats type checking, IDE navigation, and makes
the "shape" of data invisible to readers and tooling.

This probe always exits 0.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from check_bootstrap import (
    REPO_ROOT,
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
    REPO_ROOT,
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
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")

guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds: flag functions with return-dicts of N+ keys.
DICT_KEY_MEDIUM = 5
DICT_KEY_HIGH = 8

# Regex: return dict literal — `return {` possibly with content.
RETURN_DICT_RE = re.compile(r"^\s*return\s*\{", re.MULTILINE)

# Regex: quoted dict key in a literal — "key": or 'key':
DICT_KEY_RE = re.compile(r"""(?:"|')(\w+)(?:"|')\s*:""")

# Regex: incremental dict building — result["key"] = or result['key'] =
DICT_ASSIGN_RE = re.compile(r"""(\w+)\s*\[(?:"|')(\w+)(?:"|')\]\s*=""")

# Functions where returning large dicts is expected (serializers, test fixtures).
_ALLOWLIST_PREFIXES = frozenset(
    {
        "to_dict",
        "as_dict",
        "serialize",
        "to_json",
        "asdict",
        "fixture",
        "mock_",
        "fake_",
        "sample_",
        "default_",
    }
)

AI_INSTRUCTIONS = {
    "medium": (
        "This function returns a dict with many keys — the data shape is "
        "invisible to type checkers and IDE tooling. Define a dataclass or "
        "TypedDict to make the structure explicit, discoverable, and "
        "refactorable."
    ),
    "high": (
        "This function returns a dict with 8+ keys — a strong signal that "
        "this data represents a domain concept deserving its own type. "
        "Define a @dataclass with typed fields. Callers will get "
        "autocomplete, type checking, and documentation for free."
    ),
}

def _count_return_dict_keys(body: str) -> int:
    """Count the max key count from any dict literal in a return statement."""
    max_keys = 0
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if not RETURN_DICT_RE.search(line):
            continue

        # Collect lines from the return { ... } block.
        brace_depth = 0
        dict_text = ""
        for j in range(i, min(i + 40, len(lines))):
            dict_text += lines[j] + "\n"
            brace_depth += lines[j].count("{") - lines[j].count("}")
            if brace_depth <= 0:
                break

        keys = set(DICT_KEY_RE.findall(dict_text))
        max_keys = max(max_keys, len(keys))

    return max_keys

def _count_incremental_dict_keys(body: str) -> tuple[str | None, int]:
    """Count distinct keys assigned to a single dict variable via d['key'] = ...

    Returns (variable_name, key_count) for the variable with the most keys.
    """
    var_keys: dict[str, set[str]] = {}
    for match in DICT_ASSIGN_RE.finditer(body):
        var_name = match.group(1)
        key_name = match.group(2)
        var_keys.setdefault(var_name, set()).add(key_name)

    if not var_keys:
        return None, 0

    best_var = max(var_keys, key=lambda v: len(var_keys[v]))
    return best_var, len(var_keys[best_var])

def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    """Detect functions returning large dicts in one Python file."""
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]

        # Skip allowlisted function name prefixes.
        if any(func_name.startswith(p) for p in _ALLOWLIST_PREFIXES):
            continue

        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start + 1 : end])

        # Check dict literal returns.
        literal_keys = _count_return_dict_keys(body)

        # Check incremental dict building.
        _var, incremental_keys = _count_incremental_dict_keys(body)

        key_count = max(literal_keys, incremental_keys)
        if key_count < DICT_KEY_MEDIUM:
            continue

        severity = "high" if key_count >= DICT_KEY_HIGH else "medium"
        method = "dict literal" if literal_keys >= incremental_keys else "incremental build"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="design_smell",
                severity=severity,
                signals=[f"returns dict with {key_count} keys ({method}) — " f"define a @dataclass or TypedDict"],
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints

def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_dict_as_struct")

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
        if path.suffix != ".py":
            continue
        if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=PYTHON_ROOTS):
            continue
        if is_review_probe_test_path(path):
            continue

        report.files_scanned += 1
        text = guard.read_text_from_ref(path, args.head_ref) if args.since_ref else guard.read_text_from_worktree(path)
        if text is None:
            continue

        hints = _scan_python_file(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)

if __name__ == "__main__":
    sys.exit(main())
