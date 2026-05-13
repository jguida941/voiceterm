"""Role-count request parsing for collaboration profiles."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .development_collaboration_modes import DevelopCollaborationModeSpec


def role_count_requests(
    values: Sequence[object],
    *,
    architecture_agent_count: int,
    review_agent_count: int,
    max_workers: int,
    selected_mode: DevelopCollaborationModeSpec | None,
    **options: object,
) -> tuple[tuple[object, ...], tuple[str, ...]]:
    selected_mode_id = str(options.get("selected_mode_id") or "")
    known_role_values = options.get("known_roles")
    if not isinstance(known_role_values, Iterable) or isinstance(
        known_role_values, (str, bytes)
    ):
        known_roles: set[str] = set()
    else:
        known_roles = {str(role) for role in known_role_values}
    request_type = options["request_type"]
    requests: list[object] = []
    errors: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        if "=" not in raw:
            errors.append(f"role count `{raw}` must use role=n")
            continue
        role, count_text = raw.split("=", 1)
        role = role.strip()
        if role not in known_roles:
            errors.append(f"role count `{raw}` uses unknown role `{role}`")
            continue
        count = parse_count(count_text)
        if count is None:
            errors.append(f"role count `{raw}` must use a non-negative integer")
            continue
        requests.append(request_type(role=role, requested_count=count, source="request"))
    requests.extend(
        shortcut_role_count_requests(
            architecture_agent_count=architecture_agent_count,
            review_agent_count=review_agent_count,
            max_workers=max_workers,
            selected_mode=selected_mode,
            selected_mode_id=selected_mode_id,
            request_type=request_type,
        )
    )
    return merge_role_count_requests(tuple(requests), request_type), tuple(errors)


def shortcut_role_count_requests(
    *,
    architecture_agent_count: int,
    review_agent_count: int,
    max_workers: int,
    selected_mode: DevelopCollaborationModeSpec | None,
    selected_mode_id: str,
    request_type: Any,
) -> tuple[object, ...]:
    requests: list[object] = []
    if architecture_agent_count > 0:
        requests.append(
            request_type(
                role="architect",
                requested_count=architecture_agent_count,
                source="architecture_agents",
            )
        )
    if review_agent_count > 0:
        requests.append(
            request_type(
                role="reviewer",
                requested_count=review_agent_count,
                source="review_agents",
            )
        )
    if (
        max_workers > 0
        and selected_mode is not None
        and selected_mode.audit_role
        and selected_mode_id == "agent_sync"
    ):
        requests.append(
            request_type(
                role=selected_mode.audit_role,
                requested_count=max_workers,
                source="max_workers",
            )
        )
    return tuple(requests)


def merge_role_count_requests(
    requests: tuple[object, ...],
    request_type: Any,
) -> tuple[object, ...]:
    merged: dict[str, object] = {}
    for request in requests:
        previous = merged.get(request.role)
        if previous is None or request.requested_count >= previous.requested_count:
            source = request.source
            if previous is not None and previous.source != request.source:
                source = f"{previous.source}+{request.source}"
            merged[request.role] = request_type(
                role=request.role,
                requested_count=request.requested_count,
                source=source,
            )
    return tuple(merged.values())


def parse_count(value: object) -> int | None:
    text = str(value or "").strip()
    if not text.isdigit():
        return None
    return int(text)
