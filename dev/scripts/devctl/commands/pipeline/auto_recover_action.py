"""Auto-recover action for ``devctl pipeline --action auto-recover``.

Closes ADR-007 by classifying a stale commit/push pipeline and dispatching the
safe explicit recovery sub-action while emitting one composite audit receipt.
The classifier is pure; the runner owns IO and dispatch only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...runtime.pipeline_auto_recovery_contracts import (
    CHOSEN_ACTION_ABANDON,
    CHOSEN_ACTION_BAILED,
    CHOSEN_ACTION_NONE,
    CHOSEN_ACTION_RECOVER,
    CHOSEN_ACTION_REFRESH_AUTHORIZATION,
    CLASSIFICATION_ALREADY_CLEAN,
    CLASSIFICATION_AMBIGUOUS,
    CLASSIFICATION_NEEDS_ABANDON,
    CLASSIFICATION_NEEDS_RECOVER,
    CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
    PipelineAutoRecoveryClassification,
)
from .abandon_action import MIN_REASON_LENGTH, _apply_abandon
from .auto_recover_result import (
    AUTO_RECOVERY_RECEIPT_FILENAME,
    AutoRecoveryContext,
    AutoRecoverySubAction,
    finalize_bailed,
    finalize_noop,
    finalize_sub_action,
    render_markdown,
)
from .recover_action import _apply_recover
from .refresh_authorization_action import _apply_refresh
from .support import (
    PipelinePaths,
    RECOVERABLE_STATES,
    REFRESHABLE_STATES,
    TERMINAL_STATES,
    authorization_is_expired,
    authorization_of,
    head_has_moved,
    load_pipeline_payload,
    pipeline_id_of,
    pipeline_state_of,
    resolve_current_head,
    resolve_pipeline_paths,
)

# States that count as "live, healthy in-flight" — if HEAD still
# matches the authorized sha and the authorization window has not
# expired, the pipeline is already progressing normally and the
# operator does not need to intervene.
_HEALTHY_LIVE_STATES: frozenset[str] = frozenset({
    "commit_recorded",
    "awaiting_push",
    "push_pending",
})


def run_auto_recover(args) -> int:
    """Entry point for ``devctl pipeline --action auto-recover``."""
    paths = resolve_pipeline_paths(
        repo_root=getattr(args, "repo_root_override", None),
        pipeline_root_override=_maybe_path(
            getattr(args, "pipeline_root_override", None)
        ),
        receipts_root_override=_maybe_path(
            getattr(args, "receipts_root_override", None)
        ),
    )
    reason_override = str(getattr(args, "reason", "") or "").strip()
    operator_actor = str(
        getattr(args, "operator_actor", None) or "operator"
    )
    result = apply_auto_recover(
        paths=paths,
        operator_actor=operator_actor,
        reason_override=reason_override,
    )
    fmt = str(getattr(args, "format", "md") or "md")
    if fmt == "json":
        print(json.dumps(result, indent=2))
    else:
        print(render_markdown(result))
    return 0 if result.get("ok") else 1


def classify_pipeline(
    payload: dict[str, Any],
    *,
    current_head: str,
    now: datetime | None = None,
) -> PipelineAutoRecoveryClassification:
    """Pure classifier — no IO, no side effects, safe to unit test.

    ``current_head`` is passed in so tests can simulate any HEAD state
    without subprocess or environment fiddling.
    """
    reference_now = now or datetime.now(timezone.utc)

    if not payload:
        return PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_ALREADY_CLEAN,
            reason="no_pipeline_artifact",
            pipeline_state="",
            head_has_moved=False,
            authorization_expired=False,
        )

    state = pipeline_state_of(payload)
    moved = head_has_moved(payload, current_head=current_head)
    expired = authorization_is_expired(payload, now=reference_now)

    if state in TERMINAL_STATES:
        return PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_ALREADY_CLEAN,
            reason=f"pipeline_state_terminal:{state}",
            pipeline_state=state,
            head_has_moved=moved,
            authorization_expired=expired,
        )

    # HEAD moved off the authorized sha — rebind if we can, otherwise
    # abandon the wedge. Recover only works on the RECOVERABLE states.
    if moved:
        if state in RECOVERABLE_STATES:
            return PipelineAutoRecoveryClassification(
                classification=CLASSIFICATION_NEEDS_RECOVER,
                reason="head_drifted_on_recoverable_state",
                pipeline_state=state,
                head_has_moved=True,
                authorization_expired=expired,
            )
        return PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_NEEDS_ABANDON,
            reason=f"head_drifted_on_non_recoverable_state:{state}",
            pipeline_state=state,
            head_has_moved=True,
            authorization_expired=expired,
        )

    # Any ``push_blocked`` pipeline with no HEAD drift is a wedge —
    # the governed executor has already decided the run can't
    # complete. Abandon is the only safe forward move.
    if state == "push_blocked":
        return PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_NEEDS_ABANDON,
            reason="pipeline_state_push_blocked",
            pipeline_state=state,
            head_has_moved=False,
            authorization_expired=expired,
        )

    # HEAD still matches, not push_blocked. If the window has just
    # aged out we can hand-wave a fresh one without rebinding the
    # commit.
    if expired:
        if state in REFRESHABLE_STATES:
            return PipelineAutoRecoveryClassification(
                classification=CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION,
                reason="authorization_expired_head_matches",
                pipeline_state=state,
                head_has_moved=False,
                authorization_expired=True,
            )
        return PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_AMBIGUOUS,
            reason=(
                f"authorization_expired_but_state_not_refreshable:{state}"
            ),
            pipeline_state=state,
            head_has_moved=False,
            authorization_expired=True,
        )

    # Healthy, live, in-flight pipeline — no recovery needed.
    if state in _HEALTHY_LIVE_STATES and authorization_of(payload):
        return PipelineAutoRecoveryClassification(
            classification=CLASSIFICATION_ALREADY_CLEAN,
            reason=f"pipeline_state_healthy_live:{state}",
            pipeline_state=state,
            head_has_moved=False,
            authorization_expired=False,
        )

    # Nothing above fired — refuse to guess. The operator still has
    # the manual sub-actions if they want to force a path.
    return PipelineAutoRecoveryClassification(
        classification=CLASSIFICATION_AMBIGUOUS,
        reason=f"no_classification_rule_matched:{state or 'unknown'}",
        pipeline_state=state,
        head_has_moved=moved,
        authorization_expired=expired,
    )


def apply_auto_recover(
    *,
    paths: PipelinePaths,
    operator_actor: str = "operator",
    reason_override: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run classification + the chosen sub-action, emit composite receipt.

    Returns a JSON-ready dict. ``ok`` is ``True`` when either no action
    was required (already_clean) or the chosen sub-action succeeded;
    ``False`` when classification was ``ambiguous`` or the sub-action
    refused.
    """
    payload = load_pipeline_payload(paths)
    current_head = resolve_current_head(repo_root=paths.repo_root)
    classification = classify_pipeline(
        payload,
        current_head=current_head,
        now=now,
    )
    pipeline_id = pipeline_id_of(payload)
    previous_state = pipeline_state_of(payload)
    context = AutoRecoveryContext(
        paths=paths,
        classification=classification,
        pipeline_id=pipeline_id,
        previous_state=previous_state,
        operator_actor=operator_actor,
    )

    if classification.classification == CLASSIFICATION_ALREADY_CLEAN:
        return finalize_noop(context)

    if classification.classification == CLASSIFICATION_AMBIGUOUS:
        return finalize_bailed(context)

    if classification.classification == CLASSIFICATION_NEEDS_RECOVER:
        sub_reason = reason_override or (
            "auto-recover: rebind authorization to current HEAD"
        )
        sub = _apply_recover(
            paths=paths,
            reason=sub_reason,
            operator_actor=operator_actor,
        )
        return finalize_sub_action(
            context,
            AutoRecoverySubAction(
                chosen_action=CHOSEN_ACTION_RECOVER,
                result=sub,
                receipt_key="receipt_path",
                reason=reason_override,
            ),
        )

    if classification.classification == CLASSIFICATION_NEEDS_REFRESH_AUTHORIZATION:
        sub_reason = reason_override or (
            "auto-recover: reissue fresh authorization window"
        )
        sub = _apply_refresh(
            paths=paths,
            reason=sub_reason,
            operator_actor=operator_actor,
        )
        return finalize_sub_action(
            context,
            AutoRecoverySubAction(
                chosen_action=CHOSEN_ACTION_REFRESH_AUTHORIZATION,
                result=sub,
                receipt_key="receipt_path",
                reason=reason_override,
            ),
        )

    if classification.classification == CLASSIFICATION_NEEDS_ABANDON:
        # ``abandon`` requires a reason of MIN_REASON_LENGTH chars or
        # more; we synthesize one from the classifier's typed reason
        # so the resulting pipeline_abandoned_receipt captures the
        # automatic decision clearly.
        sub_reason = reason_override or (
            f"auto-recover: {classification.reason}"
        )
        if len(sub_reason) < MIN_REASON_LENGTH:
            # Defensive: classifier.reason tokens are always longer
            # than MIN_REASON_LENGTH today, but keep a safe fallback.
            sub_reason = (
                f"auto-recover forced abandon: {classification.reason}"
            )
        sub = _apply_abandon(
            paths=paths,
            reason=sub_reason,
            operator_actor=operator_actor,
        )
        return finalize_sub_action(
            context,
            AutoRecoverySubAction(
                chosen_action=CHOSEN_ACTION_ABANDON,
                result=sub,
                receipt_key="receipt_path",
                reason=sub_reason,
            ),
        )

    # Unreachable given the classifier invariants, but keep a typed
    # failure path in case the vocabulary grows without a dispatch
    # update here.
    return finalize_bailed(
        context,
        override_reason=(
            f"unhandled_classification:{classification.classification}"
        ),
    )


def _maybe_path(value: Any) -> Path | None:
    if value is None:
        return None
    return Path(value)
