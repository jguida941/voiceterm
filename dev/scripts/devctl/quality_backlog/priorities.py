"""Priority scoring assembly for quality backlog reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    CODE_SHAPE_REASON_WEIGHTS,
    COMPILER_WARNING_WEIGHTS,
    FACADE_WRAPPER_WEIGHTS,
    FUNCTION_DUPLICATION_WEIGHTS,
    LINT_DEBT_WEIGHTS,
    RUST_BEST_PRACTICE_WEIGHTS,
    SECURITY_FOOTGUN_WEIGHTS,
    SERDE_COMPATIBILITY_WEIGHTS,
    STRUCTURAL_SIMILARITY_WEIGHTS,
    SUGGESTIONS_BY_SIGNAL_PREFIX,
    InventoryRow,
    PriorityRow,
)


def ensure_priority(priorities: dict[str, PriorityRow], path: str) -> PriorityRow:
    row = priorities.get(path)
    if row is not None:
        return row
    created = PriorityRow(path=path, language=Path(path).suffix)
    priorities[path] = created
    return created


def add_signal(row: PriorityRow, *, signal: str, score: int) -> None:
    row.add_signal(
        signal=signal,
        score=score,
        suggestions=SUGGESTIONS_BY_SIGNAL_PREFIX,
    )


def ingest_inventory_signals(
    priorities: dict[str, PriorityRow],
    inventory_rows: list[InventoryRow],
) -> None:
    for row in inventory_rows:
        if row.score <= 0:
            continue
        target = ensure_priority(priorities, row.path)
        if row.status == "exceeds_hard":
            add_signal(target, signal="shape:hard", score=row.score)
        elif row.status == "exceeds_soft":
            add_signal(target, signal="shape:soft", score=row.score)
        elif row.status == "near_soft":
            add_signal(target, signal="shape:near_soft", score=row.score)


def ingest_code_shape_signals(
    priorities: dict[str, PriorityRow],
    report: dict[str, Any],
) -> None:
    violations = report.get("violations", [])
    if not isinstance(violations, list):
        return
    for violation in violations:
        if not isinstance(violation, dict):
            continue
        path = str(violation.get("path") or "")
        if not path:
            continue
        reason = str(violation.get("reason") or "unknown")
        score = CODE_SHAPE_REASON_WEIGHTS.get(reason, 140)
        add_signal(
            ensure_priority(priorities, path),
            signal=f"code_shape:{reason}",
            score=score,
        )


def ingest_growth_signals(
    priorities: dict[str, PriorityRow],
    report: dict[str, Any],
    *,
    signal_prefix: str,
    category_weights: dict[str, int],
) -> None:
    violations = report.get("violations", [])
    if not isinstance(violations, list):
        return
    for violation in violations:
        if not isinstance(violation, dict):
            continue
        path = str(violation.get("path") or "")
        growth = violation.get("growth")
        if not path or not isinstance(growth, dict):
            continue
        for category, raw_count in growth.items():
            try:
                count = int(raw_count)
            except (TypeError, ValueError):
                count = 0
            if count <= 0:
                continue
            weight = category_weights.get(str(category), 120)
            add_signal(
                ensure_priority(priorities, path),
                signal=f"{signal_prefix}:{category}",
                score=weight * count,
            )


def ingest_compiler_warning_signals(
    priorities: dict[str, PriorityRow],
    report: dict[str, Any],
) -> None:
    warnings = report.get("warnings", [])
    if not isinstance(warnings, list):
        return
    for warning in warnings:
        if not isinstance(warning, dict):
            continue
        path = str(warning.get("path") or "")
        if not path:
            continue
        code = str(warning.get("code") or "unknown")
        score = COMPILER_WARNING_WEIGHTS.get(code, 50)
        add_signal(
            ensure_priority(priorities, path),
            signal=f"rust_warning:{code}",
            score=score,
        )


def build_priorities(
    *,
    inventory_rows: list[InventoryRow],
    checks: dict[str, dict[str, Any]],
    top_n: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    priorities: dict[str, PriorityRow] = {}
    ingest_inventory_signals(priorities, inventory_rows)
    ingest_code_shape_signals(priorities, checks.get("code_shape", {}).get("report", {}))
    ingest_growth_signals(
        priorities,
        checks.get("rust_lint_debt", {}).get("report", {}),
        signal_prefix="rust_lint_debt",
        category_weights=LINT_DEBT_WEIGHTS,
    )
    ingest_growth_signals(
        priorities,
        checks.get("rust_best_practices", {}).get("report", {}),
        signal_prefix="rust_best",
        category_weights=RUST_BEST_PRACTICE_WEIGHTS,
    )
    ingest_growth_signals(
        priorities,
        checks.get("rust_runtime_panic_policy", {}).get("report", {}),
        signal_prefix="rust_panic",
        category_weights={"unallowlisted_panic_calls": 320},
    )
    ingest_compiler_warning_signals(
        priorities,
        checks.get("rust_compiler_warnings", {}).get("report", {}),
    )
    ingest_growth_signals(
        priorities,
        checks.get("structural_similarity", {}).get("report", {}),
        signal_prefix="structural_similarity",
        category_weights=STRUCTURAL_SIMILARITY_WEIGHTS,
    )
    ingest_growth_signals(
        priorities,
        checks.get("facade_wrappers", {}).get("report", {}),
        signal_prefix="facade_wrappers",
        category_weights=FACADE_WRAPPER_WEIGHTS,
    )
    ingest_growth_signals(
        priorities,
        checks.get("serde_compatibility", {}).get("report", {}),
        signal_prefix="serde_compat",
        category_weights=SERDE_COMPATIBILITY_WEIGHTS,
    )
    ingest_growth_signals(
        priorities,
        checks.get("function_duplication", {}).get("report", {}),
        signal_prefix="function_dup",
        category_weights=FUNCTION_DUPLICATION_WEIGHTS,
    )
    ingest_growth_signals(
        priorities,
        checks.get("rust_security_footguns", {}).get("report", {}),
        signal_prefix="security_footgun",
        category_weights=SECURITY_FOOTGUN_WEIGHTS,
    )
    rows = list(priorities.values())
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for row in rows:
        row.finalize()
        severity_counts[row.severity] += 1
    rows.sort(key=lambda row: (-row.score, row.path))
    if top_n > 0:
        rows = rows[:top_n]
    return [row.to_dict() for row in rows], severity_counts
