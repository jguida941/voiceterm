"""Lane-lock validations for the sync guard."""

from __future__ import annotations

from .markdown_tables import _normalize, _sorted_agents


def _validate_lane_locks(
    *,
    agents,
    errors: list[str],
) -> None:
    lock_labels = {
        "lane": "Lane",
        "worktree": "Worktree",
        "branch": "Branch",
    }
    for lock_type, field in lock_labels.items():
        _validate_table_lane_lock(
            agents=agents,
            field=field,
            lock_type=lock_type,
            errors=errors,
        )


def _validate_table_lane_lock(
    *,
    agents,
    field: str,
    lock_type: str,
    errors: list[str],
) -> None:
    seen: dict[str, str] = {}
    for agent in _sorted_agents(agents.required_agents):
        row = agents.master_by_agent.get(agent)
        if not row:
            continue
        value = _normalize(str(row.get(field, "")))
        if not value:
            errors.append(f"{agent} missing {field} in MASTER_PLAN.")
            continue
        previous = seen.get(value)
        if previous is not None:
            errors.append(
                f"{lock_type} collision: {previous} and {agent} both claim {field}={value!r}."
            )
            continue
        seen[value] = agent

