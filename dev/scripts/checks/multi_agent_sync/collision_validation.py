"""MP-scope collision and handoff-token validations for the sync guard."""

from __future__ import annotations

from .markdown_tables import _normalize, _sorted_agents
from .models import HANDOFF_TOKEN_PATTERN, MP_RANGE_PATTERN, MP_SINGLE_PATTERN


def _validate_mp_collisions(
    *,
    agents,
    errors: list[str],
) -> None:
    shared_agents = _sorted_agents(agents.required_agents)
    scopes = {
        agent: _expand_mp_scope_ids(
            _normalize(
                str(agents.master_by_agent.get(agent, {}).get("MP scope (authoritative)", ""))
            )
        )
        for agent in shared_agents
    }
    for idx, agent in enumerate(shared_agents):
        for other in shared_agents[idx + 1 :]:
            overlap = scopes[agent] & scopes[other]
            if overlap:
                _validate_handoff_tokens(
                    agents=agents,
                    agent=agent,
                    other=other,
                    overlap=overlap,
                    errors=errors,
                )


def _validate_handoff_tokens(
    *,
    agents,
    agent: str,
    other: str,
    overlap: set[str],
    errors: list[str],
) -> None:
    left_notes = _normalize(str(agents.master_by_agent[agent].get("Notes", "")))
    right_notes = _normalize(str(agents.master_by_agent[other].get("Notes", "")))
    left_token = _handoff_token(left_notes)
    right_token = _handoff_token(right_notes)
    if left_token and left_token == right_token:
        return
    errors.append(
        f"MP collision requires handoff token for {agent} and {other}: "
        + ", ".join(sorted(overlap))
    )


def _expand_mp_scope_ids(value: str) -> set[str]:
    text = _normalize(value)
    ids = {f"MP-{num}" for num in MP_SINGLE_PATTERN.findall(text)}
    for start_s, end_s in MP_RANGE_PATTERN.findall(text):
        start = int(start_s)
        end = int(end_s)
        if start > end:
            start, end = end, start
        for number in range(start, end + 1):
            ids.add(f"MP-{number:03d}")
    return ids


def _handoff_token(value: str) -> str | None:
    match = HANDOFF_TOKEN_PATTERN.search(value)
    if not match:
        return None
    return match.group(1).strip().lower() or None

