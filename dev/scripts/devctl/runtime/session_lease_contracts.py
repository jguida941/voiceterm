"""Session lease typed contract models."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .value_coercion import coerce_int, coerce_mapping, coerce_string


@dataclass(frozen=True, slots=True)
class SessionLease:
    """Lease for one runtime session, separate from SessionCachePacket."""

    lease_id: str
    session_id: str
    agent_role: str
    interaction_mode: str
    started_at_utc: str
    heartbeat_at_utc: str
    pid: int
    rollout_path: str
    declared_scope: str
    baseline_head_sha: str
    baseline_snapshot_id: str
    schema_version: int = 1
    contract_id: str = "SessionLease"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def session_lease_from_mapping(value: object) -> SessionLease | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    lease_id = coerce_string(payload.get("lease_id"))
    session_id = coerce_string(payload.get("session_id"))
    if not lease_id or not session_id:
        return None

    return SessionLease(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "SessionLease",
        lease_id=lease_id,
        session_id=session_id,
        agent_role=coerce_string(payload.get("agent_role")),
        interaction_mode=coerce_string(payload.get("interaction_mode")),
        started_at_utc=coerce_string(payload.get("started_at_utc")),
        heartbeat_at_utc=coerce_string(payload.get("heartbeat_at_utc")),
        pid=coerce_int(payload.get("pid")),
        rollout_path=coerce_string(payload.get("rollout_path")),
        declared_scope=coerce_string(payload.get("declared_scope")),
        baseline_head_sha=coerce_string(payload.get("baseline_head_sha")),
        baseline_snapshot_id=coerce_string(payload.get("baseline_snapshot_id")),
    )


__all__ = ["SessionLease", "session_lease_from_mapping"]
