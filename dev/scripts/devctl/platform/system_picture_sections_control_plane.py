"""Control-plane section builder for the system-picture snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..common_io import display_path
from .system_picture_sections import _build_section

if TYPE_CHECKING:
    from ..runtime.control_plane_read_model import ControlPlaneReadModel

_CONTROL_PLANE_COMMAND = "python3 dev/scripts/devctl.py dashboard --format json"


@dataclass(frozen=True, slots=True)
class ControlPlaneSectionSummary:
    """Typed system-picture projection for organized control-plane facts."""

    resolved_phase: str
    top_blocker: str
    next_action: str
    next_command: str
    push_eligible: bool
    implementation_blocked: bool
    operator_interaction_mode: str
    reviewer_mode: str
    reviewer_freshness: str
    review_accepted: bool
    attention_status: str
    attention_summary: str
    pending_action_requests: int
    last_guard_ok: bool
    check_detail_count: int
    reviewer_observation_status: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if not self.reviewer_observation_status:
            payload.pop("reviewer_observation_status", None)
        return payload


def build_control_plane_section(
    *,
    repo_root: Path,
    control_plane: "ControlPlaneReadModel | None",
    review_state_path: Path | None,
) -> object:
    """Build the organized control-plane summary for operators and AI."""
    if control_plane is None:
        return _build_section(
            section_id="control_plane",
            title="Control Plane",
            status="missing",
            summary={},
            source_path="",
            source_command=_CONTROL_PLANE_COMMAND,
            generated_at_utc="",
            notes=(
                "No ControlPlaneReadModel could be built for this proof tick; "
                "refresh startup/review artifacts before relying on operator guidance.",
            ),
        )

    reviewer_observation_status = ""
    if control_plane.reviewer_observation is not None:
        reviewer_observation_status = control_plane.reviewer_observation.status

    notes: list[str] = []
    if control_plane.next_command:
        notes.append(f"Next governed command: {control_plane.next_command}")
    if control_plane.top_blocker and control_plane.top_blocker != "none":
        notes.append(f"Current blocker: {control_plane.top_blocker}")

    summary = ControlPlaneSectionSummary(
        resolved_phase=control_plane.resolved_phase,
        top_blocker=control_plane.top_blocker,
        next_action=control_plane.next_action,
        next_command=control_plane.next_command,
        push_eligible=control_plane.push_eligible,
        implementation_blocked=control_plane.implementation_blocked,
        operator_interaction_mode=control_plane.operator_interaction_mode,
        reviewer_mode=control_plane.reviewer_mode,
        reviewer_freshness=control_plane.reviewer_freshness,
        review_accepted=control_plane.review_accepted,
        attention_status=control_plane.attention_status,
        attention_summary=control_plane.attention_summary,
        pending_action_requests=control_plane.pending_action_requests,
        last_guard_ok=control_plane.last_guard_ok,
        check_detail_count=len(control_plane.check_details),
        reviewer_observation_status=reviewer_observation_status,
    ).to_dict()

    return _build_section(
        section_id="control_plane",
        title="Control Plane",
        status="current",
        summary=summary,
        source_path=(
            display_path(review_state_path, repo_root=repo_root)
            if review_state_path is not None
            else ""
        ),
        source_command=_CONTROL_PLANE_COMMAND,
        generated_at_utc=control_plane.timestamp,
        notes=tuple(notes[:2]),
    )


__all__ = ["build_control_plane_section"]
