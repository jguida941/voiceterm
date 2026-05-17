"""Agent-presence and report-state helpers for the sync guard."""

from __future__ import annotations

from .markdown_tables import _normalize, _sorted_agents, _sorted_signers
from .models import (
    AGENT_NAME_PATTERN,
    ALLOWED_LEDGER_STATUSES,
    AgentBundle,
)


def _validate_agent_presence(
    *,
    agents: AgentBundle,
    errors: list[str],
) -> None:
    if not agents.master_agents:
        errors.append("MASTER_PLAN board must include at least one agent row.")
    if not agents.runbook_agents:
        errors.append("review_channel board must include at least one agent row.")
    missing_runbook = agents.required_agents - agents.runbook_agents
    unexpected_runbook = agents.runbook_agents - agents.required_agents
    if missing_runbook:
        errors.append(
            "review_channel missing agent rows: "
            + ", ".join(_sorted_agents(missing_runbook))
        )
    if unexpected_runbook:
        errors.append(
            "review_channel has unexpected agent rows: "
            + ", ".join(_sorted_agents(unexpected_runbook))
        )
    missing_signers = agents.expected_signers - agents.signoff_signers
    unexpected_signers = agents.signoff_signers - agents.expected_signers
    if missing_signers:
        errors.append(
            "review_channel signoff table missing signers: "
            + ", ".join(_sorted_signers(missing_signers))
        )
    if unexpected_signers:
        errors.append(
            "review_channel signoff table has unexpected signers: "
            + ", ".join(_sorted_signers(unexpected_signers))
        )


def _validate_agent_names(
    *,
    agents: AgentBundle,
    errors: list[str],
) -> None:
    for table_name, agent_ids in (
        ("MASTER_PLAN", agents.master_agents),
        ("review_channel", agents.runbook_agents),
    ):
        invalid_agents = sorted(
            agent for agent in agent_ids if not AGENT_NAME_PATTERN.fullmatch(agent)
        )
        if invalid_agents:
            errors.append(
                f"{table_name} contains invalid agent names (expected AGENT-<number>): "
                + ", ".join(invalid_agents)
            )


def _validate_lane_alignment(
    *,
    agents: AgentBundle,
    errors: list[str],
) -> None:
    shared_agents = _sorted_agents(agents.required_agents & agents.runbook_agents)
    for agent in shared_agents:
        master_row = agents.master_by_agent[agent]
        runbook_row = agents.runbook_by_agent[agent]
        for master_field, runbook_field in (
            ("Lane", "Lane"),
            ("MP scope (authoritative)", "MP scope"),
            ("Worktree", "Worktree"),
            ("Branch", "Branch"),
        ):
            master_value = _normalize(str(master_row.get(master_field, "")))
            runbook_value = _normalize(str(runbook_row.get(runbook_field, "")))
            if master_value != runbook_value:
                errors.append(
                    f"{agent} mismatch for {master_field!r}: "
                    f"MASTER_PLAN={master_value!r}, review_channel={runbook_value!r}"
                )


def _warn_unknown_ledger_statuses(ledger_rows: list[dict], warnings: list[str]) -> None:
    for row in ledger_rows:
        status = _normalize(str(row.get("Status", ""))).lower()
        if status and status not in ALLOWED_LEDGER_STATUSES:
            warnings.append(
                f"Shared Ledger row has unrecognized Status {status!r}; expected one of "
                + ", ".join(sorted(ALLOWED_LEDGER_STATUSES))
            )


def _extend_runtime_truth_errors(
    *,
    runtime_truth: dict[str, object],
    errors: list[str],
) -> None:
    for entry in runtime_truth.get("errors", []):
        text = str(entry).strip()
        if text:
            errors.append(text)


def _cycle_complete_for_signoff(
    *,
    master_by_agent: dict[str, dict],
    required_agents: set[str],
) -> bool:
    return bool(required_agents) and all(
        _normalize(str(master_by_agent.get(agent, {}).get("Status", ""))).lower()
        == "merged"
        for agent in required_agents
    )
