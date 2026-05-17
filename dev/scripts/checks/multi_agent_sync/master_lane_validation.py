"""MASTER_PLAN row and freshness validations for the sync guard."""

from __future__ import annotations

from .markdown_tables import _normalize, _sorted_agents
from .models import ALLOWED_MASTER_STATUSES, UTC_Z_PATTERN


def _validate_master_lane_rows(
    *,
    agents,
    ledger_rows: list[dict],
    errors: list[str],
) -> None:
    for agent in _sorted_agents(agents.required_agents):
        row = agents.master_by_agent.get(agent)
        if not row:
            continue
        status = _normalize(str(row.get("Status", ""))).lower()
        if status not in ALLOWED_MASTER_STATUSES:
            errors.append(
                f"{agent} MASTER_PLAN status {status!r} is invalid; expected one of "
                + ", ".join(sorted(ALLOWED_MASTER_STATUSES))
            )
        _validate_last_update(agent=agent, row=row, errors=errors)
        if status == "merged" and not any(
            _ledger_row_matches_agent(
                ledger_row,
                agent,
                _normalize(str(row.get("Branch", ""))),
            )
            for ledger_row in ledger_rows
        ):
            errors.append(
                f"{agent} is merged in MASTER_PLAN but no matching Shared Ledger entry was found."
            )


def _validate_last_update(
    *,
    agent: str,
    row: dict,
    errors: list[str],
) -> None:
    timestamp = _normalize(str(row.get("Last update (UTC)", "")))
    if not timestamp or not UTC_Z_PATTERN.match(timestamp):
        errors.append(
            f"{agent} Last update (UTC) must be populated with full UTC timestamp."
        )


def _ledger_row_matches_agent(row: dict, agent: str, branch: str) -> bool:
    area = _normalize(str(row.get("Area", ""))).upper()
    actor = _normalize(str(row.get("Actor", ""))).upper()
    ledger_branch = _normalize(str(row.get("Branch", "")))
    if area == agent or actor == agent:
        return True
    return bool(branch and ledger_branch == branch)
