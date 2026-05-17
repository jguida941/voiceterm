"""Report assembly and rendering for runtime-spine closure."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

from .support import (
    build_runtime_spine_report,
    load_owner_texts,
)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    system_map_path: Path | None = None,
    owner_paths: Sequence[Path] | None = None,
    registered_check_ids: Sequence[str] | None = None,
) -> dict[str, object]:
    """Build the runtime-spine closure report for the current repo."""
    system_map = system_map_path or repo_root / "dev/guides/SYSTEM_MAP.md"
    system_map_text = system_map.read_text(encoding="utf-8")
    check_ids = tuple(registered_check_ids or _registered_check_ids(repo_root))
    report = build_runtime_spine_report(
        system_map_text=system_map_text,
        owner_texts=load_owner_texts(repo_root, owner_paths=owner_paths),
        registered_check_ids=check_ids,
    )
    report["command"] = "check_runtime_spine_closure"
    report["timestamp"] = utc_timestamp()
    report["system_map_path"] = system_map.relative_to(repo_root).as_posix()
    return report


def render_md(report: Mapping[str, object]) -> str:
    """Render a compact Markdown report."""
    lines = ["# check_runtime_spine_closure", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- section_present: {report.get('section_present', False)}")
    lines.append(f"- closure_rule_present: {report.get('closure_rule_present', False)}")
    lines.append(f"- registered_guard_present: {report.get('registered_guard_present', False)}")
    lines.append(f"- risky_item_count: {report.get('risky_item_count', 0)}")
    lines.append(f"- closure_matrix_present: {report.get('closure_matrix_present', False)}")
    lines.append(f"- closure_matrix_rows: {report.get('closure_matrix_row_count', 0)}")
    violations = _rows(report.get("violations"))
    lines.append(f"- violations: {len(violations)}")
    items = _rows(report.get("items"))
    if items:
        lines.extend(("", "## Runtime Spine Owners", ""))
        for item in items:
            owner_refs = item.get("owner_refs")
            owner_text = ", ".join(owner_refs) if isinstance(owner_refs, list) else ""
            lines.append(
                "- "
                + str(item.get("name") or "unknown")
                + " "
                + str(item.get("status") or "unknown")
                + ": "
                + (owner_text or "unowned")
            )
    matrix_rows = _rows(report.get("closure_matrix"))
    if matrix_rows:
        lines.extend(("", "## Closure Matrix", ""))
        for row in matrix_rows:
            lines.append(
                "- "
                + str(row.get("runtime_object") or "unknown")
                + ": owner="
                + str(row.get("active_owner") or "")
                + "; proof="
                + str(row.get("regression_proof") or "")
                + "; priority="
                + str(row.get("priority") or "")
            )
    if violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            lines.append(
                "- "
                + str(violation.get("check") or "unknown")
                + ": "
                + str(violation.get("detail") or "")
            )
    return "\n".join(lines)


def _registered_check_ids(repo_root: Path) -> tuple[str, ...]:
    from dev.scripts.devctl.governance.script_catalog_registry import (
        CHECK_SCRIPT_RELATIVE_PATHS,
    )

    return tuple(CHECK_SCRIPT_RELATIVE_PATHS)


def _rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]
