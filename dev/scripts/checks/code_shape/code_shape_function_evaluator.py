"""Function-shape evaluation helpers for check_code_shape."""

from __future__ import annotations

from datetime import date
from pathlib import Path

try:
    from code_shape_shared import FunctionShapeException, FunctionShapePolicy
except (
    ModuleNotFoundError
):  # pragma: no cover - import fallback for package-style test loading
    try:
        from checks.code_shape.code_shape_shared import (
            FunctionShapeException,
            FunctionShapePolicy,
        )
    except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
        from dev.scripts.checks.code_shape.code_shape_shared import (
            FunctionShapeException,
            FunctionShapePolicy,
        )


def _parse_exception_expiry(raw_value: str) -> date | None:
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _default_scanner():
    try:
        from code_shape.code_shape_function_policy import scan_rust_functions
    except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
        try:
            from checks.code_shape.code_shape_function_policy import scan_rust_functions
        except ModuleNotFoundError:  # pragma: no cover - repo-package fallback
            from dev.scripts.checks.code_shape.code_shape_function_policy import (
                scan_rust_functions,
            )
    return scan_rust_functions


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
        scanner = _default_scanner()
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
