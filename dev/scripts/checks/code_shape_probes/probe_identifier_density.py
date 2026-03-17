#!/usr/bin/env python3
"""Review probe: detect functions with excessive unique identifiers.

Functions using >20 unique identifiers force readers to track too many
names simultaneously.  Splitting into focused helpers — each with 10-15
names — keeps working-memory load manageable.

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
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)
RUST_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds for unique identifier count per function.
IDENT_MEDIUM = 20
IDENT_HIGH = 30

# Secondary signal: ratio of single-char identifiers.
SINGLE_CHAR_RATIO_THRESHOLD = 0.30
SINGLE_CHAR_MIN_IDENTS = 10

# Allowed single-char names (loop vars, coordinates, throwaway).
SINGLE_CHAR_ALLOWED = frozenset({"i", "j", "k", "_", "x", "y", "n", "m"})

# Identifier extraction pattern.
IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

PYTHON_KEYWORDS = frozenset({
    "if", "else", "elif", "for", "while", "return", "def", "class",
    "import", "from", "as", "with", "try", "except", "finally",
    "raise", "pass", "break", "continue", "and", "or", "not", "in",
    "is", "lambda", "yield", "True", "False", "None", "self", "cls",
})

PYTHON_BUILTINS = frozenset({
    "len", "print", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "range", "enumerate", "zip", "map", "filter",
    "sorted", "reversed", "any", "all", "min", "max", "sum", "abs",
    "isinstance", "issubclass", "type", "super", "object", "property",
    "staticmethod", "classmethod", "hasattr", "getattr", "setattr",
    "open", "repr", "format", "iter", "next", "id", "hash", "callable",
    "vars", "dir", "globals", "locals", "input", "round", "chr", "ord",
    "hex", "oct", "bin", "pow", "divmod", "ValueError", "TypeError",
    "KeyError", "IndexError", "AttributeError", "RuntimeError",
    "OSError", "IOError", "FileNotFoundError", "StopIteration",
    "Exception", "NotImplementedError", "AssertionError",
})

RUST_KEYWORDS = frozenset({
    "fn", "let", "mut", "if", "else", "for", "while", "loop", "match",
    "return", "pub", "use", "mod", "struct", "enum", "impl", "trait",
    "where", "const", "static", "ref", "self", "super", "crate",
    "true", "false", "Self", "as", "in", "break", "continue", "move",
    "async", "await", "dyn", "type", "unsafe",
})

RUST_BUILTINS = frozenset({
    "String", "Vec", "Option", "Result", "Some", "None", "Ok", "Err",
    "Box", "Rc", "Arc", "Cell", "RefCell", "Mutex", "HashMap",
    "HashSet", "BTreeMap", "BTreeSet", "Cow", "Pin", "PhantomData",
    "u8", "u16", "u32", "u64", "u128", "usize",
    "i8", "i16", "i32", "i64", "i128", "isize",
    "f32", "f64", "bool", "char", "str",
    "println", "eprintln", "format", "panic", "todo", "unimplemented",
    "unreachable", "assert", "assert_eq", "assert_ne", "debug_assert",
    "vec", "write", "writeln",
})

AI_INSTRUCTIONS = {
    "medium": (
        "This function uses {count} unique identifiers. Extract "
        "sub-computations into helper functions that encapsulate their "
        "own variable scope, aiming for 10-15 identifiers per function."
    ),
    "high": (
        "This function uses {count} unique identifiers — far too many "
        "to hold in working memory. Split into smaller functions, each "
        "with a focused vocabulary of 10-15 distinct names."
    ),
}

SINGLE_CHAR_INSTRUCTION = (
    "Over {pct}% of identifiers in this function are single-character "
    "names. Use descriptive names that reveal intent."
)


def _extract_function_body(lines: list[str], func: dict) -> str:
    """Extract the text of a function body from source lines."""
    start = func["start_line"] - 1
    end = func.get("end_line", len(lines))
    return "\n".join(lines[start:end])


def _count_identifiers(body: str, exclude: frozenset[str]) -> tuple[set[str], set[str]]:
    """Return (unique_identifiers, single_char_identifiers) from a function body."""
    raw_idents = set(IDENT_RE.findall(body))
    filtered = raw_idents - exclude
    # Remove purely numeric-looking tokens that slip through (e.g. _0)
    unique = {name for name in filtered if not name.startswith("__")}
    single_char = {
        name for name in unique
        if len(name) == 1 and name not in SINGLE_CHAR_ALLOWED
    }
    return unique, single_char


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()
    exclude = PYTHON_KEYWORDS | PYTHON_BUILTINS

    for func in functions:
        body = _extract_function_body(lines, func)
        unique, single_char = _count_identifiers(body, exclude)
        count = len(unique)

        func_hints = _build_hints(rel, func["name"], count, unique, single_char)
        hints.extend(func_hints)

    return hints


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()
    exclude = RUST_KEYWORDS | RUST_BUILTINS

    for func in functions:
        body = _extract_function_body(lines, func)
        unique, single_char = _count_identifiers(body, exclude)
        count = len(unique)

        func_hints = _build_hints(rel, func["name"], count, unique, single_char)
        hints.extend(func_hints)

    return hints


def _build_hints(
    rel: str,
    func_name: str,
    count: int,
    unique: set[str],
    single_char: set[str],
) -> list[RiskHint]:
    """Build RiskHint entries for a single function's identifier analysis."""
    hints: list[RiskHint] = []

    if count >= IDENT_MEDIUM:
        severity = "high" if count >= IDENT_HIGH else "medium"
        sample = sorted(unique)[:8]
        sample_str = ", ".join(sample)
        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="readability_smell",
                severity=severity,
                signals=[
                    f"{count} unique identifiers ({sample_str}, ...) — "
                    f"split into focused helpers"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity].format(count=count),
                review_lens=REVIEW_LENS,
            )
        )

    # Secondary: single-char density check.
    if (
        count >= SINGLE_CHAR_MIN_IDENTS
        and single_char
        and len(single_char) / count > SINGLE_CHAR_RATIO_THRESHOLD
    ):
        pct = int(100 * len(single_char) / count)
        char_list = ", ".join(sorted(single_char)[:6])
        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="readability_smell",
                severity="medium",
                signals=[
                    f"{pct}% single-character identifiers ({char_list}) — "
                    f"use descriptive names"
                ],
                ai_instruction=SINGLE_CHAR_INSTRUCTION.format(pct=pct),
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_identifier_density")

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
        if is_review_probe_test_path(path):
            continue

        is_python = path.suffix == ".py" and is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=PYTHON_ROOTS)
        is_rust = path.suffix == ".rs" and is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=RUST_ROOTS)
        if not is_python and not is_rust:
            continue

        report.files_scanned += 1
        text = guard.read_text_from_ref(path, args.head_ref) if args.since_ref else guard.read_text_from_worktree(path)
        if text is None:
            continue

        hints = _scan_python_file(text, path) if is_python else _scan_rust_file(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
