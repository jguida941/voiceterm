"""Function-shape helpers for check_code_shape."""

from __future__ import annotations

import re

try:
    from code_shape.code_shape_function_evaluator import evaluate_function_shape
    from code_shape_shared import FunctionShapeException, FunctionShapePolicy
    from python_function_scan import scan_python_functions
except (
    ModuleNotFoundError
):  # pragma: no cover - import fallback for package-style test loading
    try:
        from checks.code_shape.code_shape_function_evaluator import (
            evaluate_function_shape,
        )
        from checks.code_shape.code_shape_shared import (
            FunctionShapeException,
            FunctionShapePolicy,
        )
        from checks.code_shape.python_function_scan import scan_python_functions
    except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
        from dev.scripts.checks.code_shape.code_shape_function_evaluator import (
            evaluate_function_shape,
        )
        from dev.scripts.checks.code_shape.code_shape_shared import (
            FunctionShapeException,
            FunctionShapePolicy,
        )
        from dev.scripts.checks.code_shape.python_function_scan import (
            scan_python_functions,
        )

RUST_FN_PATTERN = re.compile(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\b")


def _strip_inline_comment(raw_line: str) -> str:
    return raw_line.split("//", 1)[0]


def scan_rust_functions(text: str | None) -> list[dict]:
    if not text:
        return []

    functions: list[dict] = []
    current: dict | None = None
    lines = text.splitlines()
    for lineno, raw_line in enumerate(lines, start=1):
        line = _strip_inline_comment(raw_line)
        if current is None:
            match = RUST_FN_PATTERN.search(line)
            if not match:
                continue
            current = {
                "name": match.group(1),
                "start_line": lineno,
                "opened": False,
                "brace_depth": 0,
            }

        open_count = line.count("{")
        close_count = line.count("}")

        if not current["opened"] and open_count == 0:
            # Signature-only trait declarations (`fn foo(...);`) have no body.
            if ";" in line:
                current = None
            continue

        if open_count > 0:
            current["opened"] = True

        if not current["opened"]:
            continue

        current["brace_depth"] += open_count - close_count
        if current["brace_depth"] <= 0:
            end_line = lineno
            start_line = int(current["start_line"])
            functions.append(
                {
                    "name": str(current["name"]),
                    "start_line": start_line,
                    "end_line": end_line,
                    "line_count": end_line - start_line + 1,
                }
            )
            current = None

    if current is not None and current["opened"]:
        end_line = len(lines)
        start_line = int(current["start_line"])
        functions.append(
            {
                "name": str(current["name"]),
                "start_line": start_line,
                "end_line": end_line,
                "line_count": end_line - start_line + 1,
            }
        )

    return functions
