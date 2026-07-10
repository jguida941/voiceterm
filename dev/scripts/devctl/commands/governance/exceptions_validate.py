"""Validate action for the governed exception command."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...common import resolve_repo_path
from ...runtime.governed_exception_lifecycle import GovernedExceptionLifecycle
from ...runtime.governed_exception_receipts import ExceptionReceipt
from ...runtime.governed_exception_validation import (
    validate_exception_receipt,
    validate_governed_exception_lifecycle,
)
from ...runtime.jsonl_support import parse_json_line_dict
from .exceptions_report import base_report


def validate_action(args: Any) -> tuple[dict[str, object], int]:
    """Validate governed-exception JSON or JSONL rows."""
    raw_path = str(getattr(args, "path", "") or "").strip()
    if not raw_path:
        payload = base_report("validate")
        payload["ok"] = False
        payload["errors"] = ["missing_path"]
        return payload, 2
    path = resolve_repo_path(raw_path, None)
    payload = base_report("validate", validate_path=path)
    rows, read_errors = _load_validation_rows(path)
    validation_rows: list[dict[str, object]] = []
    errors: list[str] = list(read_errors)
    current_head = str(getattr(args, "current_head", "") or "").strip()
    for index, row in enumerate(rows, start=1):
        row_errors = _validate_row(row, current_head=current_head)
        validation_rows.append({"line": index, "errors": row_errors, "payload": row})
        errors.extend(f"line {index}: {error}" for error in row_errors)
    payload["ok"] = not errors
    payload["validated_count"] = len(rows)
    payload["errors"] = errors
    payload["rows"] = validation_rows
    return payload, 0 if not errors else 1


def _load_validation_rows(path: Path) -> tuple[list[Mapping[str, object]], list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], [f"file_not_found:{path}"]
    except OSError as exc:
        return [], [f"read_failed:{exc.__class__.__name__}"]
    stripped = text.strip()
    if not stripped:
        return [], ["empty_file"]
    if stripped.startswith("{"):
        return _load_json_object(stripped)
    return _load_jsonl_rows(text, path)


def _load_json_object(text: str) -> tuple[list[Mapping[str, object]], list[str]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], [f"invalid_json:{exc.msg}"]
    if not isinstance(payload, Mapping):
        return [], ["expected_json_object"]
    return [payload], []


def _load_jsonl_rows(path_text: str, path: Path) -> tuple[list[Mapping[str, object]], list[str]]:
    rows: list[Mapping[str, object]] = []
    errors: list[str] = []
    for index, line in enumerate(path_text.splitlines(), start=1):
        payload = parse_json_line_dict(
            line,
            source=str(path),
            line_number=index,
            warning_sink=lambda message: errors.append(message),
        )
        if payload is not None:
            rows.append(payload)
    return rows, errors


def _validate_row(
    payload: Mapping[str, object],
    *,
    current_head: str,
) -> list[str]:
    contract_id = str(payload.get("contract_id") or "").strip()
    if contract_id == "GovernedExceptionLifecycle" or "lifecycle_id" in payload:
        lifecycle = GovernedExceptionLifecycle.from_mapping(payload)
        return list(
            validate_governed_exception_lifecycle(
                lifecycle,
                current_head=current_head,
            )
        )
    if contract_id == "ExceptionReceipt" or _looks_like_exception_receipt(payload):
        receipt = ExceptionReceipt.from_mapping(payload)
        return list(validate_exception_receipt(receipt, current_head=current_head))
    if contract_id:
        return [f"unsupported_contract:{contract_id}"]
    return ["unsupported_contract"]


def _looks_like_exception_receipt(payload: Mapping[str, object]) -> bool:
    return all(
        key in payload
        for key in (
            "receipt_id",
            "action_kind",
            "phase",
            "guard_id",
            "exception_class",
            "operator_reason",
            "head",
        )
    )


__all__ = ["validate_action"]
