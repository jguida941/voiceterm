"""Runtime helpers for governed commit attention and handoff behavior."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.event_reducer import load_or_refresh_event_bundle
from ...review_channel.events import post_packet, resolve_artifact_paths
from ...runtime.conductor_capability import build_conductor_capability_state
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_state_models import ReviewState
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.startup_receipt import load_startup_receipt
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


def _held_lease_active(held_lease: str) -> bool:
    """Return true when the caller is holding a non-empty attention lease."""
    return bool(str(held_lease or "").strip())


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


def _has_actionable_packet_attention(record: object) -> bool:
    pending_actionable = getattr(record, "pending_actionable_packet_ids", ()) or ()
    if pending_actionable:
        return True
    wake_reason = str(getattr(record, "wake_reason", "") or "").strip()
    return wake_reason == "finding_pending"


def _target_agent_has_actionable_packet_attention(
    *,
    packet_inbox: object,
    target_agent: str,
) -> bool:
    agent_records = tuple(getattr(packet_inbox, "agents", ()) or ())
    if target_agent:
        normalized_target = target_agent.strip().lower()
        for record in agent_records:
            if str(getattr(record, "agent", "") or "").strip().lower() != normalized_target:
                continue
            return _has_actionable_packet_attention(record)
        return False
    return any(_has_actionable_packet_attention(record) for record in agent_records)


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
    if not target_agent or review_channel_path is None:
        return "", "", ""
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
    if reviewer_provider and reviewer_capability and reviewer_capability.may_edit_repo:
        return reviewer_provider
    return ""


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
