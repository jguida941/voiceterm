"""Startup projection for authority snapshots."""

from __future__ import annotations

from .authority_snapshot import AuthoritySnapshot
from .startup_context_actor_authority_output import (
    startup_actor_authority_summary_from_mapping,
)


def startup_authority_snapshot_dict(
    authority_snapshot: AuthoritySnapshot,
) -> dict[str, object]:
    payload = authority_snapshot.to_dict()
    payload["actor_authorities"] = [
        startup_actor_authority_summary_from_mapping(row)
        for row in payload.get("actor_authorities", ())
        if isinstance(row, dict)
    ]
    return payload


__all__ = ["startup_authority_snapshot_dict"]
