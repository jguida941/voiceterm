"""Actor-authority helpers for governed VCS target selection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from ...runtime.conductor_capability import build_conductor_capability_state
from ...runtime.review_state_collaboration_models import (
    ActorAuthorityState,
    actor_authority_for_capability,
)
from ...runtime.review_state_models import ReviewState


def _collaboration_mapping(review_state: ReviewState) -> Mapping[str, object] | None:
    """v4.55.3 (rev_pkt_4778/4781): extract the typed CollaborationSessionState
    as a plain mapping so authority helpers (live_reviewer_present /
    live_implementer_present) can read `role_assignments` directly.

    Handles three collaboration shapes:
      - Mapping (dict-like): returned as-is.
      - dataclass: serialized via asdict().
      - Attribute-shaped object (SimpleNamespace, custom classes with
        `role_assignments` / `participants` attributes): build a mapping
        from the attribute namespace. This closes the rev_pkt_4781 leak
        where attribute-shaped fixtures fell through to the legacy bridge
        path because they're neither Mapping nor dataclass.

    Returns None only when the review_state has no usable collaboration
    block at all (e.g. attribute access raises or no `role_assignments`
    field present).
    """
    collaboration = getattr(review_state, "collaboration", None)
    if collaboration is None:
        return None
    if isinstance(collaboration, Mapping):
        return collaboration
    if is_dataclass(collaboration):
        try:
            return asdict(collaboration)
        except TypeError:
            return None
    # Attribute-shaped fallback: any object exposing role_assignments
    # or participants is typed-collaboration-enough for authority gating.
    role_assignments = getattr(collaboration, "role_assignments", None)
    participants = getattr(collaboration, "participants", None)
    if role_assignments is None and participants is None:
        return None
    extracted: dict[str, object] = {}
    if role_assignments is not None:
        extracted["role_assignments"] = _coerce_assignment_rows(role_assignments)
    if participants is not None:
        extracted["participants"] = _coerce_assignment_rows(participants)
    return extracted


def _coerce_assignment_rows(rows: object) -> list[Mapping[str, object]]:
    """Coerce role_assignments/participants from attribute-shaped or
    iterable forms into a list of plain mappings so the typed-facts
    helpers can iterate uniformly.
    """
    if rows is None:
        return []
    if isinstance(rows, (list, tuple)):
        normalized: list[Mapping[str, object]] = []
        for row in rows:
            if isinstance(row, Mapping):
                normalized.append(row)
                continue
            if is_dataclass(row):
                try:
                    normalized.append(asdict(row))
                except TypeError:
                    continue
                continue
            # Attribute-shaped row: pull the fields v4.55.3 cares about.
            row_map: dict[str, object] = {}
            for key in (
                "agent_id",
                "provider",
                "role_id",
                "live",
                "role",
                "actor_id",
            ):
                if hasattr(row, key):
                    row_map[key] = getattr(row, key)
            if row_map:
                normalized.append(row_map)
        return normalized
    return []


def commit_authority_target(review_state: ReviewState) -> str:
    """Return the live mutation owner when repo.commit is explicitly granted."""
    collaboration = getattr(review_state, "collaboration", None)
    mutation_owner = str(getattr(collaboration, "mutation_owner", "") or "").strip()
    authority = target_authority(
        review_state,
        capability="repo.commit",
        provider=mutation_owner,
    )
    if authority is None:
        return ""
    if not authority_has_live_role(
        review_state,
        authority=authority,
        expected_role="implementer",
    ):
        return ""
    return str(authority.provider or authority.actor_id).strip().lower()


def coding_agent_can_receive_stage_handoff(
    review_state: ReviewState,
    *,
    provider: str,
) -> bool:
    """Verify the coding-agent reroute target is live and writable."""
    authority = target_authority(
        review_state,
        capability="repo.stage",
        provider=provider,
        alternate_capabilities=("repo.stage_handoff",),
    )
    if authority is not None and authority_has_live_role(
        review_state,
        authority=authority,
        expected_role="implementer",
    ):
        return True
    reviewer_mode = (
        review_state.bridge.effective_reviewer_mode
        or review_state.collaboration.reviewer_mode
        or review_state.bridge.reviewer_mode
        or "single_agent"
    )
    # v4.55.3 (rev_pkt_4778): governed executor mutation authority must
    # NOT come from legacy reviewer_mode strings alone. Pass the typed
    # CollaborationSessionState so build_conductor_capability_state can
    # gate `may_edit_repo` on the typed `role_assignments` (a live
    # `coding_agent` assignment), not just on `active_dual_agent`.
    typed_collaboration = _collaboration_mapping(review_state)
    capability = build_conductor_capability_state(
        provider=provider,
        reviewer_mode=reviewer_mode,
        role="implementer",
        collaboration=typed_collaboration,
    )
    if capability is None or not getattr(capability, "may_edit_repo", False):
        return False
    return provider_has_live_role(
        review_state,
        provider=provider,
        role="implementer",
    )


def target_authority(
    review_state: ReviewState,
    *,
    capability: str,
    provider: str,
    alternate_capabilities: tuple[str, ...] = (),
) -> ActorAuthorityState | None:
    collaboration = getattr(review_state, "collaboration", None)
    authorities = tuple(getattr(collaboration, "actor_authorities", ()) or ())
    if not authorities:
        return None
    return actor_authority_for_capability(
        authorities,
        capability,
        preferred_actor=provider,
        alternate_capabilities=alternate_capabilities,
    )


def authority_has_live_role(
    review_state: ReviewState,
    *,
    authority: ActorAuthorityState,
    expected_role: str,
) -> bool:
    role = str(authority.role or "").strip().lower()
    if role not in {"implementer", "reviewer"}:
        return False
    normalized_expected = str(expected_role or "").strip().lower()
    if normalized_expected == "implementer" and role != "implementer":
        return False
    provider = str(authority.provider or authority.actor_id or "").strip().lower()
    if not provider:
        return False
    return provider_has_live_role(
        review_state,
        provider=provider,
        role=role,
    )


def provider_has_live_role(
    review_state: ReviewState,
    *,
    provider: str,
    role: str,
) -> bool:
    normalized_provider = str(provider or "").strip().lower()
    normalized_role = str(role or "").strip().lower()
    if not normalized_provider or normalized_role not in {"implementer", "reviewer"}:
        return False
    collaboration = getattr(review_state, "collaboration", None)
    participants = tuple(getattr(collaboration, "participants", ()) or ())
    saw_live_provider_participant = False
    for participant in participants:
        participant_provider = (
            str(
                getattr(participant, "provider", "")
                or getattr(participant, "agent_id", "")
                or ""
            )
            .strip()
            .lower()
        )
        if participant_provider != normalized_provider or not bool(
            getattr(participant, "live", False)
        ):
            continue
        saw_live_provider_participant = True
        participant_role = str(getattr(participant, "role", "") or "").strip().lower()
        if participant_role == normalized_role:
            return True
    if saw_live_provider_participant:
        return False
    assignment_status = _provider_live_role_assignment_status(
        collaboration,
        provider=normalized_provider,
        role=normalized_role,
    )
    if assignment_status == "matching":
        return True
    if assignment_status == "other":
        return False
    # Fail closed when no live participant or live role-assignment proves
    # the lane is reachable.
    return False


def _provider_live_role_assignment_status(
    collaboration: object,
    *,
    provider: str,
    role: str,
) -> str:
    role_ids = (
        ("coding_agent",) if role == "implementer" else ("review_agent", "lead_agent")
    )
    saw_live_provider_assignment = False
    for assignment in tuple(getattr(collaboration, "role_assignments", ()) or ()):
        assignment_provider = (
            str(
                getattr(assignment, "provider", "")
                or getattr(assignment, "agent_id", "")
                or ""
            )
            .strip()
            .lower()
        )
        if assignment_provider != provider or not bool(
            getattr(assignment, "live", False)
        ):
            continue
        saw_live_provider_assignment = True
        if str(getattr(assignment, "role_id", "") or "").strip().lower() in role_ids:
            return "matching"
    if saw_live_provider_assignment:
        return "other"
    return "unknown"
