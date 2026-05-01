"""People/reviewer section builders for the DashboardSnapshot."""

from __future__ import annotations

from typing import Any

from .dashboard_utils import (
    _age_seconds,
    _format_age,
)


def _build_review_section(
    bridge: dict[str, str],
    reviewer: dict[str, Any],
    implementer: dict[str, Any],
    session: dict[str, Any],
    instruction_text: str,
    reviewer_mode: str = "",
    coordination_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reviewer_state = reviewer.get("job_state", "n/a")
    implementer_state = implementer.get("job_state", "n/a")
    current_turn = "Implementer" if implementer_state == "implementing" else "Reviewer"
    instruction_text = (instruction_text or "").strip()
    if not instruction_text:
        instruction_text = bridge.get("instruction", "n/a")
    if instruction_text and len(instruction_text) > 120:
        instruction_text = instruction_text[:120] + "..."
    section: dict[str, Any] = {}
    section["reviewer_state"] = reviewer_state
    section["reviewer_provider"] = reviewer.get("provider", "n/a")
    section["implementer_state"] = implementer_state
    section["implementer_provider"] = implementer.get("provider", "n/a")
    section["current_turn"] = current_turn
    section["instruction"] = instruction_text
    section["last_poll"] = bridge.get("last_poll", "n/a")
    section["mode"] = reviewer_mode or bridge.get("reviewer_mode", "n/a")
    # Per Codex rev_pkt_2326/2361/2367/2368: surface typed
    # coordination_topology / authority_mode / recovery_eligibility on the
    # dashboard "review" section so operators see typed authority next to
    # the legacy review-gate vocabulary. Demote section["mode"] with an
    # explicit authority marker when the typed answer is populated, so
    # consumers don't read "single_agent" as an observed-topology claim.
    coord = coordination_state or {}
    coordination_topology = str(coord.get("coordination_topology") or "").strip()
    authority_mode = str(coord.get("authority_mode") or "").strip()
    recovery_eligibility = str(coord.get("recovery_eligibility") or "").strip()
    if coordination_topology:
        section["coordination_topology"] = coordination_topology
        section["coordination_topology_authority"] = "primary"
        section["mode_authority"] = "legacy"
    if authority_mode:
        section["authority_mode"] = authority_mode
    if recovery_eligibility:
        section["recovery_eligibility"] = recovery_eligibility
    return section


def _build_workers_section(agents_data: dict[str, Any] | None) -> list[dict[str, str]]:
    """Build worker rows with scope, state, age, and last update summary."""
    if not agents_data:
        return []

    workers = []
    for idx, agent in enumerate(agents_data.get("agents", []), start=1):
        updated = agent.get("updated_at", "")
        age = _age_seconds(updated)
        row: dict[str, str] = {}
        row["id"] = f"W{idx}"
        row["agent_id"] = agent.get("agent_id", "unknown")
        row["scope"] = agent.get("lane_title", agent.get("current_job", "unknown"))
        row["provider"] = agent.get("provider", "unknown")
        row["state"] = agent.get("job_state", "unknown").upper()
        row["age"] = _format_age(age)
        row["last_update"] = agent.get("waiting_on", "")
        workers.append(row)
    return workers


def _build_reviewer_activity_section(
    bridge: dict[str, str],
    reviewer_agent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build reviewer activity from bridge.md parsed fields."""
    poll_utc = bridge.get("last_poll_utc", "")
    poll_age = _format_age(_age_seconds(poll_utc))

    verdict_raw = bridge.get("verdict", "n/a")
    verdict_first_line = _first_meaningful_line(verdict_raw)
    verdict_summary = verdict_first_line[:80] + ("..." if len(verdict_first_line) > 80 else "")

    findings_raw = bridge.get("findings_raw", "")
    finding_lines = [
        line for line in findings_raw.splitlines()
        if line.strip().startswith("- F") or line.strip().startswith("-")
    ] if findings_raw else []
    findings_posted = len(finding_lines)

    scope_raw = bridge.get("reviewed_scope_raw", "")
    scope_lines = [
        line for line in scope_raw.splitlines()
        if line.strip().startswith("- ") or line.strip().startswith("*")
    ] if scope_raw else []
    reviewed_files = len(scope_lines)

    instr_full = bridge.get("instruction_full", "n/a")
    instr_first = _first_meaningful_line(instr_full)
    instruction_summary = instr_first[:80] + ("..." if len(instr_first) > 80 else "")

    provider = (reviewer_agent or {}).get("provider", "unknown")
    section: dict[str, Any] = {}
    section["provider"] = provider
    section["last_poll_age"] = poll_age
    section["last_verdict"] = verdict_summary if verdict_summary != "n/a" else "n/a"
    section["reviewed_files"] = reviewed_files
    section["instruction_summary"] = (
        instruction_summary if instruction_summary != "n/a" else "n/a"
    )
    section["findings_posted"] = findings_posted
    return section


def _first_meaningful_line(text: str) -> str:
    """Return the first non-empty line from text, stripping leading '- '."""
    if not text or text == "n/a":
        return "n/a"
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if stripped:
            return stripped
    return "n/a"
