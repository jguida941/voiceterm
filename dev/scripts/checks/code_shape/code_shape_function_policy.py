"""Function-shape helpers for check_code_shape."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

try:
    from code_shape_shared import FunctionShapeException, FunctionShapePolicy
    from code_shape.python_function_scan import scan_python_functions
except (
    ModuleNotFoundError
):  # pragma: no cover - import fallback for package-style test loading
    try:
        from checks.code_shape.code_shape_shared import (
            FunctionShapeException,
            FunctionShapePolicy,
        )
        from checks.code_shape.python_function_scan import scan_python_functions
    except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
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


def _parse_exception_expiry(raw_value: str) -> date | None:
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def evaluate_function_shape(
    *,
    path: Path,
    policy: FunctionShapePolicy,
    policy_source: str,
    text: str | None,
    today: date,
    function_policy_exceptions: dict[str, FunctionShapeException],
    best_practice_docs: dict[str, tuple[str, ...]],
    scanner=None,
    exception_key_builder=None,
) -> tuple[list[dict], int]:
    if text is None:
        return [], 0

    if scanner is None:
        scanner = scan_rust_functions
    if exception_key_builder is None:
        exception_key_builder = lambda candidate_path, function_name: (
            f"{candidate_path.as_posix()}::{function_name}"
        )

    violations: list[dict] = []
    exceptions_used = 0
    for function in scanner(text):
        line_count = int(function["line_count"])
        if line_count <= policy.max_lines:
            continue

        function_name = str(function["name"])
        exception_key = exception_key_builder(path, function_name)
        exception = function_policy_exceptions.get(exception_key)
        if exception is None:
            violations.append(
                {
                    "path": path.as_posix(),
                    "reason": "function_exceeds_max_lines",
                    "guidance": (
                        f"Function `{function_name}` is {line_count} lines "
                        f"({function['start_line']}-{function['end_line']}); "
                        f"max allowed is {policy.max_lines}. Split dispatch/pipeline logic "
                        "before merge."
                    ),
                    "best_practice_refs": list(best_practice_docs.get(path.suffix, ())),
                    "base_lines": None,
                    "current_lines": line_count,
                    "growth": None,
                    "policy": {
                        "max_function_lines": policy.max_lines,
                    },
                    "policy_source": policy_source,
                    "function_name": function_name,
                    "function_start_line": function["start_line"],
                    "function_end_line": function["end_line"],
                }
            )
            continue

        exceptions_used += 1
        expiry = _parse_exception_expiry(exception.expires_on)
        if expiry is None:
            violations.append(
                {
                    "path": path.as_posix(),
                    "reason": "function_exception_invalid_expiry",
                    "guidance": (
                        f"Function exception for `{function_name}` has invalid `expires_on` "
                        f"value `{exception.expires_on}`. Use ISO date (YYYY-MM-DD)."
                    ),
                    "best_practice_refs": list(best_practice_docs.get(path.suffix, ())),
                    "base_lines": None,
                    "current_lines": line_count,
                    "growth": None,
                    "policy": {
                        "max_function_lines": policy.max_lines,
                        "exception_max_lines": exception.max_lines,
                        "exception_owner": exception.owner,
                        "exception_expires_on": exception.expires_on,
                        "exception_follow_up_mp": exception.follow_up_mp,
                    },
                    "policy_source": policy_source,
                    "function_name": function_name,
                    "function_start_line": function["start_line"],
                    "function_end_line": function["end_line"],
                }
            )
            continue

        if line_count <= exception.max_lines and today <= expiry:
            continue

        if today > expiry:
            reason = "function_exception_expired"
            guidance = (
                f"Temporary exception for `{function_name}` expired on {exception.expires_on}. "
                f"Owner: {exception.owner}. Follow-up: {exception.follow_up_mp}. "
                "Renew with justification or split the function."
            )
        else:
            reason = "function_exceeds_exception_limit"
            guidance = (
                f"Function `{function_name}` is {line_count} lines "
                f"({function['start_line']}-{function['end_line']}); exception limit is "
                f"{exception.max_lines} lines (owner: {exception.owner}, "
                f"expires: {exception.expires_on}, follow-up: {exception.follow_up_mp}). "
                "Split before merge."
            )

        violations.append(
            {
                "path": path.as_posix(),
                "reason": reason,
                "guidance": guidance,
                "best_practice_refs": list(best_practice_docs.get(path.suffix, ())),
                "base_lines": None,
                "current_lines": line_count,
                "growth": None,
                "policy": {
                    "max_function_lines": policy.max_lines,
                    "exception_max_lines": exception.max_lines,
                    "exception_owner": exception.owner,
                    "exception_expires_on": exception.expires_on,
                    "exception_follow_up_mp": exception.follow_up_mp,
                    "exception_reason": exception.reason,
                },
                "policy_source": policy_source,
                "function_name": function_name,
                "function_start_line": function["start_line"],
                "function_end_line": function["end_line"],
            }
        )

    return violations, exceptions_used
