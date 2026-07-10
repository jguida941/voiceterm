"""Startup projections for actor authority and grants."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .review_state_collaboration_models import ActorAuthorityState, CapabilityGrantState


def startup_actor_authority_dict(row: ActorAuthorityState) -> dict[str, object]:
    payload = _select(asdict(row), _ACTOR_AUTHORITY_FIELDS)
    payload["grants"] = [
        startup_capability_grant_dict(grant) for grant in row.grants
    ]
    return payload


def startup_actor_authority_summary_dict(
    row: ActorAuthorityState,
) -> dict[str, object]:
    payload = _select(asdict(row), _ACTOR_AUTHORITY_SUMMARY_FIELDS)
    payload["grant_capabilities"] = [
        grant.capability for grant in row.grants if grant.granted
    ]
    return payload


def startup_actor_authority_summary_from_mapping(
    row: Mapping[str, object],
) -> dict[str, object]:
    payload = _select(row, _ACTOR_AUTHORITY_SUMMARY_FIELDS)
    payload["live"] = bool(row.get("live", False))
    payload["grant_capabilities"] = [
        str(grant.get("capability") or "")
        for grant in row.get("grants", ())
        if isinstance(grant, dict) and bool(grant.get("granted", False))
    ]
    return payload


def startup_capability_grant_dict(row: CapabilityGrantState) -> dict[str, object]:
    return asdict(row)


def _select(
    row: Mapping[str, object],
    fields: tuple[str, ...],
) -> dict[str, object]:
    return {field: row.get(field, "") for field in fields}


_ACTOR_AUTHORITY_FIELDS = (
    "actor_id",
    "provider",
    "role",
    "live",
    "status",
    "source",
    "source_contract",
    "source_identity",
    "snapshot_id",
    "zref",
    "generation_id",
    "worktree_identity",
    "packet_id",
    "approval_ref",
    "issued_at_utc",
    "expires_at_utc",
)

_ACTOR_AUTHORITY_SUMMARY_FIELDS = (
    "actor_id",
    "provider",
    "role",
    "live",
)


__all__ = [
    "startup_actor_authority_dict",
    "startup_actor_authority_summary_dict",
    "startup_actor_authority_summary_from_mapping",
    "startup_capability_grant_dict",
]
