"""Plan-target selection helpers for startup work-intake."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from .project_governance import PlanRegistryEntry, ProjectGovernance
from .review_state_locator import load_review_state as load_typed_review_state
from .review_state_models import ReviewState
from .work_intake_models import PlanTargetRef

_SESSION_RESUME_TARGET_KIND = "session_resume"
_SESSION_RESUME_ANCHOR = "session_resume:session-resume"
_PLAN_DOC_TARGET_KIND = "plan_doc"
_PLAN_DOC_ANCHOR = "section:root"


def load_review_state(
    repo_root: Path,
    governance: ProjectGovernance | None = None,
) -> ReviewState | None:
    """Load the typed review-state projection when it exists."""
    return load_typed_review_state(repo_root, governance=governance)


def select_active_plan_entry(
    governance: ProjectGovernance,
    review_state: ReviewState | None,
) -> PlanRegistryEntry | None:
    """Select the best startup plan target from review scope and plan registry."""
    entries = governance.plan_registry.entries
    if not entries:
        return None

    matched_entry = _best_scoped_entry(entries, review_state)
    if matched_entry is not None:
        return matched_entry

    tracker_entry = _entry_by_path(entries, governance.plan_registry.tracker_path)
    if tracker_entry is not None:
        return tracker_entry

    resume_entry = next(
        (
            entry
            for entry in entries
            if entry.session_resume is not None and entry.role != "tracker"
        ),
        None,
    )
    return resume_entry or entries[0]


def build_target_ref(
    repo_root: Path,
    entry: PlanRegistryEntry | None,
) -> PlanTargetRef | None:
    """Build the canonical startup plan target reference."""
    if entry is None:
        return None
    target_kind, anchor_ref, expected_revision = _target_parts(repo_root, entry)
    target_digest = sha256(
        f"{entry.path}|{target_kind}|{anchor_ref}".encode("utf-8")
    ).hexdigest()[:16]
    return PlanTargetRef(
        target_id=f"plan_target:{target_digest}",
        plan_path=entry.path,
        plan_title=entry.title,
        plan_scope=entry.scope,
        target_kind=target_kind,
        anchor_ref=anchor_ref,
        expected_revision=expected_revision,
    )


def _best_scoped_entry(
    entries: tuple[PlanRegistryEntry, ...],
    review_state: ReviewState | None,
) -> PlanRegistryEntry | None:
    best_entry: PlanRegistryEntry | None = None
    best_score = -1
    for token in _selection_tokens(review_state):
        for entry in entries:
            score = _entry_match_score(entry, token)
            if score > best_score:
                best_entry = entry
                best_score = score
    return best_entry


def _selection_tokens(review_state: ReviewState | None) -> tuple[str, ...]:
    if review_state is None:
        return ()
    values = (
        review_state.current_session.last_reviewed_scope,
        review_state.review.plan_id,
        review_state.current_session.current_instruction,
    )
    return tuple(value for value in values if value)


def _entry_match_score(entry: PlanRegistryEntry, token: str) -> int:
    needle = token.strip().casefold()
    if not needle:
        return 0

    exact_fields = (entry.path.casefold(), entry.title.casefold(), entry.scope.casefold())
    partial_fields = exact_fields
    score = 0
    if needle == exact_fields[0]:
        score = 100
    elif needle == exact_fields[1]:
        score = 95
    elif needle == exact_fields[2]:
        score = 90
    elif needle in partial_fields[0]:
        score = 70
    elif needle in partial_fields[1]:
        score = 65
    elif needle in partial_fields[2]:
        score = 60
    if score and entry.role != "tracker":
        score += 5
    if score and entry.session_resume is not None:
        score += 5
    return score


def _entry_by_path(
    entries: tuple[PlanRegistryEntry, ...],
    target_path: str,
) -> PlanRegistryEntry | None:
    return next((entry for entry in entries if entry.path == target_path), None)


def _target_parts(repo_root: Path, entry: PlanRegistryEntry) -> tuple[str, str, str]:
    if entry.session_resume is not None:
        return (
            _SESSION_RESUME_TARGET_KIND,
            _SESSION_RESUME_ANCHOR,
            entry.session_resume.section_hash,
        )
    return (
        _PLAN_DOC_TARGET_KIND,
        _PLAN_DOC_ANCHOR,
        _file_revision(repo_root, entry.path),
    )


def _file_revision(repo_root: Path, relative_path: str) -> str:
    path = repo_root / relative_path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return sha256(text.encode("utf-8")).hexdigest()[:16]


__all__ = ["build_target_ref", "load_review_state", "select_active_plan_entry"]
