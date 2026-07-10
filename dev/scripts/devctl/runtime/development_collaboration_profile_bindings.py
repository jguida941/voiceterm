"""Role binding readers for collaboration profiles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .provider_registry import is_valid_provider_id, normalize_provider_id
from .session_posture import SessionPosture


def role_bindings(
    values: Sequence[object],
    *,
    known_roles: set[str],
    review_state: Mapping[str, object],
    session_posture: SessionPosture | None,
    binding_type: Any,
) -> tuple[tuple[object, ...], tuple[str, ...]]:
    bindings: list[object] = []
    errors: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        if "=" not in raw:
            errors.append(f"role binding `{raw}` must use role=provider")
            continue
        role, target = raw.split("=", 1)
        role = role.strip()
        provider, session_id = split_provider_session(target)
        if role not in known_roles:
            errors.append(f"role binding `{raw}` uses unknown role `{role}`")
            continue
        provider = normalize_provider_id(provider)
        if not is_valid_provider_id(provider):
            errors.append(f"role binding `{raw}` uses invalid provider `{provider}`")
            continue
        bindings.append(
            binding_type(
                role=role,
                provider=provider,
                session_id=session_id
                or session_for_role(
                    review_state,
                    provider=provider,
                    role=role,
                    session_posture=session_posture,
                ),
            )
        )
    return tuple(bindings), tuple(errors)


def session_for_role(
    review_state: Mapping[str, object],
    *,
    provider: str,
    role: str,
    session_posture: SessionPosture | None,
) -> str:
    actors = session_posture.actors if session_posture is not None else ()
    for actor in actors:
        actor_provider = normalize_provider_id(actor.provider or actor.actor_id)
        if actor_provider == provider and actor.role == role:
            return actor.actor_id or actor.provider
    for row in rows(mapping(review_state.get("agent_work_board")).get("rows")):
        if (
            normalize_provider_id(row.get("provider") or row.get("actor_id")) == provider
            and str(row.get("role") or "").strip() == role
        ):
            return str(row.get("session_id") or "").strip()
    for row in rows(review_state.get("agent_loop_decisions")):
        if (
            normalize_provider_id(row.get("actor_id")) == provider
            and str(row.get("actor_role") or "").strip() == role
        ):
            return str(row.get("session_id") or "").strip()
    return ""


def split_provider_session(value: str) -> tuple[str, str]:
    target = value.strip()
    if ":" not in target:
        return target, ""
    provider, session_id = target.split(":", 1)
    return provider.strip(), session_id.strip()


def rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
