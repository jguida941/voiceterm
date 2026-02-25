"""Plan-scope helpers for `devctl swarm_run`."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autonomy_run_helpers import repo_relative


def validate_plan_scope(
    *, plan_doc: Path, index_doc: Path, master_plan_doc: Path, mp_scope: str
) -> tuple[str, str, str, list[str], list[str]]:
    plan_text = plan_doc.read_text(encoding="utf-8")
    index_text = index_doc.read_text(encoding="utf-8")
    master_text = master_plan_doc.read_text(encoding="utf-8")
    plan_rel = repo_relative(plan_doc)

    warnings: list[str] = []
    errors: list[str] = []
    plan_tokens = {plan_rel, str(plan_doc), plan_doc.name}
    if not any(token and token in index_text for token in plan_tokens):
        errors.append(f"active index does not reference plan doc path: {plan_rel}")
    if mp_scope not in master_text:
        errors.append(f"MASTER_PLAN does not contain scope token: {mp_scope}")
    if mp_scope not in index_text:
        warnings.append(f"INDEX does not explicitly mention scope token: {mp_scope}")
    return plan_text, index_text, plan_rel, warnings, errors


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    for start, line in enumerate(lines):
        if line.strip() != heading:
            continue
        end = len(lines)
        for index in range(start + 1, len(lines)):
            if lines[index].startswith("## "):
                end = index
                break
        return start, end
    return None


def _append_line_to_section(
    text: str, *, heading: str, line: str, marker: str
) -> tuple[str, bool, str | None]:
    lines = text.splitlines()
    had_trailing_newline = text.endswith("\n")
    bounds = _section_bounds(lines, heading)
    if not bounds:
        return text, False, f"missing section: {heading}"
    start, end = bounds
    section = lines[start + 1 : end]
    if any(marker in row for row in section):
        return text, False, None
    lines.insert(end, line)
    updated = "\n".join(lines)
    if had_trailing_newline:
        updated += "\n"
    return updated, True, None


def update_plan_doc(
    *,
    plan_doc: Path,
    plan_rel: str,
    run_label: str,
    mp_scope: str,
    swarm_ok: bool,
    governance_ok: bool,
    run_dir: Path,
    swarm_summary: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    current = plan_doc.read_text(encoding="utf-8")
    today = str(datetime.now(timezone.utc).date())
    status_word = "done" if swarm_ok and governance_ok else "blocked"
    summary_rel = repo_relative(run_dir / "summary.md")

    progress_line = (
        f"- {today}: Ran `devctl swarm_run` (`{run_label}`, `{mp_scope}`); "
        f"selected_agents={swarm_summary.get('selected_agents')}, "
        f"worker_agents={swarm_summary.get('worker_agents')}, "
        f"reviewer_lane={swarm_summary.get('reviewer_lane')}, governance_ok={governance_ok}, "
        f"status={status_word}; artifacts: `{summary_rel}`."
    )
    audit_row = (
        f"| `python3 dev/scripts/devctl.py swarm_run --plan-doc {plan_rel} --mp-scope {mp_scope} --run-label {run_label}` "
        f"| swarm_ok={swarm_ok}, governance_ok={governance_ok}, summary=`{summary_rel}` ({today} local run) "
        f"| {status_word} |"
    )

    updated_text, _, progress_error = _append_line_to_section(
        current,
        heading="## Progress Log",
        line=progress_line,
        marker=run_label,
    )
    final_text, _, audit_error = _append_line_to_section(
        updated_text,
        heading="## Audit Evidence",
        line=audit_row,
        marker=run_label,
    )

    warnings: list[str] = []
    ok = True
    if progress_error:
        ok = False
        warnings.append(progress_error)
    if audit_error:
        ok = False
        warnings.append(audit_error)

    updated = False
    if ok and final_text != current:
        plan_doc.write_text(final_text, encoding="utf-8")
        updated = True

    return {"ok": ok, "updated": updated, "warnings": warnings}, warnings
