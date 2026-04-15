"""Bounded projection helpers for the typed StartupContext surface.

Isolates the contract-ownership, surface-token, and coordination
projection helpers so the main ``startup_context`` module can stay
focused on reviewer-gate detection and the top-level builder.  Each
helper returns a small, serializable dict suitable for the startup
packet bootstrap surface.
"""

from __future__ import annotations

from ..platform.contract_definitions import shared_contracts
from ..platform.coordination_snapshot_models import CoordinationSnapshot


def build_contract_ownership_map() -> dict[str, dict[str, object]]:
    """Return the full contract-ownership map used by ``build_startup_context``."""
    ownership: dict[str, dict[str, object]] = {}
    for spec in sorted(shared_contracts(), key=lambda row: row.contract_id):
        if not spec.startup_surface_tokens:
            continue
        ownership[spec.contract_id] = {
            "owner_layer": spec.owner_layer,
            "runtime_model": spec.runtime_model,
            "startup_surface_token_count": len(spec.startup_surface_tokens),
            "startup_surface_tokens": list(spec.startup_surface_tokens),
        }
    return ownership


def bounded_contract_ownership_map(
    ownership: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Serialize a slim startup-facing contract ownership projection."""
    bounded: dict[str, dict[str, object]] = {}
    for contract_id, payload in ownership.items():
        row: dict[str, object] = {}
        owner_layer = str(payload.get("owner_layer") or "").strip()
        if owner_layer:
            row["owner_layer"] = owner_layer
        runtime_model = str(payload.get("runtime_model") or "").strip()
        if contract_id in {
            "ReviewState",
            "RemoteCommitPipelineContract",
            "WorkIntakePacket",
            "CollaborationSession",
        } and runtime_model:
            row["runtime_model"] = runtime_model
        token_count = int(payload.get("startup_surface_token_count") or 0)
        if token_count > 0:
            row["startup_surface_token_count"] = token_count
        tokens = _bounded_contract_tokens(payload.get("startup_surface_tokens"))
        if tokens:
            row["startup_surface_tokens"] = tokens
        bounded[contract_id] = row
    return bounded


def _bounded_contract_tokens(value: object) -> list[str]:
    """Return a capped, prioritized list of surface tokens."""
    seen: list[str] = []
    raw_tokens = [str(item).strip() for item in (value or ()) if str(item).strip()]
    for token in ("snapshot_id", "implementer_state_hash", "push_eligible_now"):
        if token in raw_tokens and token not in seen:
            seen.append(token)
    for token in raw_tokens:
        if token not in seen:
            seen.append(token)
        if len(seen) >= 2:
            break
    return seen

def startup_coordination_dict(coordination: CoordinationSnapshot) -> dict[str, object]:
    """Bounded coordination projection for the startup packet surface.

    Startup bootstrap is one of the proof surfaces for the F1/MP-384
    parity contract, so every ownership-posture field the underlying
    ``CoordinationSnapshot`` carries must reach the serialized dict —
    dropping ``ownership_status`` silently is what caused the scoped
    parity claim to be vacuous.
    """
    payload: dict[str, object] = {
        "declared_topology": coordination.declared_topology,
        "observed_topology": coordination.observed_topology,
        "recommended_topology": coordination.recommended_topology,
        "fanout_posture": coordination.fanout_posture,
        "safe_to_fanout": coordination.safe_to_fanout,
        "worktree_strategy": coordination.worktree_strategy,
        "resync_required": coordination.resync_required,
    }
    ownership_status = str(
        getattr(coordination, "ownership_status", "") or ""
    ).strip()
    if ownership_status:
        payload["ownership_status"] = ownership_status
    authority_mode = str(getattr(coordination, "authority_mode", "") or "").strip()
    if authority_mode:
        payload["authority_mode"] = authority_mode
    work_ownership_mode = str(
        getattr(coordination, "work_ownership_mode", "") or ""
    ).strip()
    if work_ownership_mode:
        payload["work_ownership_mode"] = work_ownership_mode
    sync_cadence_mode = str(
        getattr(coordination, "sync_cadence_mode", "") or ""
    ).strip()
    if sync_cadence_mode:
        payload["sync_cadence_mode"] = sync_cadence_mode
    if coordination.active_target is not None:
        payload["active_target"] = coordination.active_target.to_dict()
    if coordination.current_slice:
        payload["current_slice"] = coordination.current_slice
    if coordination.scope_paths:
        payload["scope_paths"] = list(coordination.scope_paths)
    if coordination.resync_reasons:
        payload["resync_reasons"] = list(coordination.resync_reasons)
    if coordination.duplicate_worktrees:
        payload["duplicate_worktrees"] = list(coordination.duplicate_worktrees)
    if coordination.actors:
        payload["actors"] = [
            {
                "actor_id": actor.actor_id,
                "provider": actor.provider,
                "role": actor.role,
                "presence": actor.presence,
            }
            for actor in coordination.actors[:4]
        ]
    return payload


__all__ = [
    "build_contract_ownership_map",
    "bounded_contract_ownership_map",
    "startup_coordination_dict",
]
