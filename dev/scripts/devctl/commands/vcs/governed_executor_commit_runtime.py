"""Runtime helpers for governed commit attention and handoff behavior."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.event_reducer import load_or_refresh_event_bundle
from ...review_channel.events import post_packet, resolve_artifact_paths
from ...review_channel.publication_ownership import resolve_publication_owner
from ...runtime.conductor_capability import build_conductor_capability_state
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_state_models import ReviewState
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.reviewer_runtime_models import has_active_remote_control_attachment
from ...runtime.startup_receipt import load_startup_receipt
from .governed_executor_commit_attention import (
    _held_lease_active,
    _target_agent_has_actionable_packet_attention,
)
from .governed_executor_packets import build_commit_execution_request


def attention_revision_stale(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
    held_lease: str = "",
) -> bool:
    """Return true when packet attention changed since the latest startup receipt.

    When `held_lease` is a non-empty revision string, treat it as authoritative:
    the caller (e.g., the commit-pipeline post-approval window) has pinned the
    attention revision and subsequent typed-state writes must not re-trigger the
    stale gate. This is the Q100 attention-revision-lease pattern. Callers that
    still want the pre-lease, receipt-comparison semantics pass an empty lease.
    """
    if _held_lease_active(held_lease):
        return False
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    if review_state is None:
        return False
    packet_inbox = getattr(review_state, "packet_inbox", None)
    if packet_inbox is None:
        return False
    current_attention_revision = str(
        getattr(packet_inbox, "attention_revision", "") or ""
    ).strip()
    if not current_attention_revision:
        return False
    target_agent = resolve_commit_execution_target(review_state)
    if not _target_agent_has_actionable_packet_attention(
        packet_inbox=packet_inbox,
        target_agent=target_agent,
    ):
        return False
    receipt = load_startup_receipt(repo_root=repo_root)
    if receipt is None:
        return True
    return receipt.attention_revision != current_attention_revision

def live_attention_revision(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
) -> str:
    """Return the current live packet-inbox attention revision, or empty string."""
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    if review_state is None:
        return ""
    packet_inbox = getattr(review_state, "packet_inbox", None)
    if packet_inbox is None:
        return ""
    return str(getattr(packet_inbox, "attention_revision", "") or "").strip()

def post_commit_execution_handoff(
    *,
    pipeline: RemoteCommitPipelineContract,
    repo_root: Path,
    review_channel_path: Path | None,
) -> tuple[str, str, str]:
    """Post one typed commit handoff when the local lane cannot write `.git`."""
    review_state = load_live_review_state(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
    )
    target_agent = resolve_commit_execution_target(review_state)
    if review_channel_path is None:
        return "", "", "commit_execution_request_review_channel_missing"
    if not target_agent:
        return "", "", "commit_execution_target_unavailable"
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        _, event = post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            request=build_commit_execution_request(
                pipeline,
                to_agent=target_agent,
                body=(
                    "The current lane hit `.git/index.lock` permission denial "
                    "while running the already-approved governed commit. "
                    "Resume the same runtime-bound pipeline from the writable "
                    "lane without restaging."
                ),
            ),
        )
    except (OSError, ValueError) as exc:
        return target_agent, "", f"commit_execution_request_failed: {exc}"
    return target_agent, str(event.get("packet_id") or "").strip(), ""


def load_live_review_state(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
) -> ReviewState | None:
    """Return the latest typed review state when event-backed projections exist."""
    if review_channel_path is None or not review_channel_path.exists():
        return None
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        bundle = load_or_refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except ValueError:
        return None
    return review_state_from_payload(bundle.review_state)


def resolve_commit_execution_target(review_state: ReviewState | None) -> str:
    """Pick the writable provider lane for a typed commit handoff."""
    if review_state is None:
        return ""
    reviewer_mode = (
        review_state.bridge.effective_reviewer_mode
        or review_state.collaboration.reviewer_mode
        or review_state.bridge.reviewer_mode
        or "single_agent"
    )
    implementer_provider = _provider_for_role(
        review_state,
        role_id="coding_agent",
        fallback_provider=review_state.collaboration.coding_agent,
        fallback_role="implementer",
    )
    implementer_capability = review_state.bridge.implementer_capability or (
        build_conductor_capability_state(
            provider=implementer_provider,
            reviewer_mode=reviewer_mode,
            role="implementer",
        )
        if implementer_provider
        else None
    )
    if (
        implementer_provider
        and implementer_capability
        and implementer_capability.may_edit_repo
        and _provider_has_live_role(
            review_state,
            provider=implementer_provider,
            role="implementer",
        )
    ):
        return implementer_provider

    reviewer_provider = _provider_for_role(
        review_state,
        role_id="review_agent",
        fallback_provider=review_state.collaboration.review_agent,
        fallback_role="reviewer",
    )
    reviewer_capability = review_state.bridge.reviewer_capability or (
        build_conductor_capability_state(
            provider=reviewer_provider,
            reviewer_mode=reviewer_mode,
            role="reviewer",
        )
        if reviewer_provider
        else None
    )
    if (
        reviewer_provider
        and reviewer_capability
        and reviewer_capability.may_edit_repo
        and _provider_has_live_role(
            review_state,
            provider=reviewer_provider,
            role="reviewer",
        )
    ):
        return reviewer_provider
    return _publication_owned_target(
        review_state,
        reviewer_provider=reviewer_provider,
        implementer_provider=implementer_provider,
    )


def _provider_for_role(
    review_state: ReviewState,
    *,
    role_id: str,
    fallback_provider: str,
    fallback_role: str,
) -> str:
    for assignment in review_state.collaboration.role_assignments:
        if assignment.role_id != role_id:
            continue
        provider = str(assignment.provider or assignment.agent_id).strip().lower()
        if provider:
            return provider
    provider = str(fallback_provider or "").strip().lower()
    if provider:
        return provider
    if fallback_role == "implementer":
        capability = review_state.bridge.implementer_capability
    else:
        capability = review_state.bridge.reviewer_capability
    if capability is not None:
        provider = str(capability.provider or "").strip().lower()
        if provider:
            return provider
    return ""


def _publication_owned_target(
    review_state: ReviewState,
    *,
    reviewer_provider: str,
    implementer_provider: str,
) -> str:
    interaction_mode = _commit_execution_interaction_mode(review_state)
    if interaction_mode != "remote_control":
        return ""
    collaboration = getattr(review_state, "collaboration", None)
    topology = str(getattr(collaboration, "topology_mode", "") or "").strip()
    decision = resolve_publication_owner(
        interaction_mode=interaction_mode,
        topology=topology,
        reviewer_provider=reviewer_provider,
        implementer_provider=implementer_provider,
    )
    target_provider = str(decision.owner_provider or "").strip().lower()
    if not target_provider:
        return ""
    target_role = ""
    if str(decision.owner or "").strip().lower() == "implementer":
        target_role = "implementer"
    elif str(decision.owner or "").strip().lower() == "reviewer":
        target_role = "reviewer"
    if target_role and not _provider_has_live_role(
        review_state,
        provider=target_provider,
        role=target_role,
    ):
        return ""
    return target_provider


def _provider_has_live_role(
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
        participant_provider = str(
            getattr(participant, "provider", "")
            or getattr(participant, "agent_id", "")
            or ""
        ).strip().lower()
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
    return True


def _provider_live_role_assignment_status(
    collaboration: object,
    *,
    provider: str,
    role: str,
) -> str:
    role_ids = ("coding_agent",) if role == "implementer" else ("review_agent", "lead_agent")
    saw_live_provider_assignment = False
    for assignment in tuple(getattr(collaboration, "role_assignments", ()) or ()):
        assignment_provider = str(
            getattr(assignment, "provider", "")
            or getattr(assignment, "agent_id", "")
            or ""
        ).strip().lower()
        if assignment_provider != provider or not bool(getattr(assignment, "live", False)):
            continue
        saw_live_provider_assignment = True
        if str(getattr(assignment, "role_id", "") or "").strip().lower() in role_ids:
            return "matching"
    if saw_live_provider_assignment:
        return "other"
    return "unknown"


def _commit_execution_interaction_mode(review_state: ReviewState) -> str:
    reviewer_runtime = getattr(review_state, "reviewer_runtime", None)
    attachment = getattr(reviewer_runtime, "remote_control_attachment", None)
    if has_active_remote_control_attachment(attachment):
        return "remote_control"

    collaboration = getattr(review_state, "collaboration", None)
    restart = getattr(collaboration, "restart", None)
    if str(getattr(restart, "source", "") or "").strip() == "remote_control_attachment":
        return "remote_control"

    participants = tuple(getattr(collaboration, "participants", ()) or ())
    for participant in participants:
        if str(getattr(participant, "capture_mode", "") or "").strip().lower() == "remote-control":
            return "remote_control"
    return "local_terminal"
