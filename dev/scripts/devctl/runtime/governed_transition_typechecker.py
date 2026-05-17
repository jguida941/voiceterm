"""Typestate checks for governed exception lifecycle transitions."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from .governed_transition_typechecker_helpers import (
    bypass_links_to_exception,
    bypass_still_active,
    closure_lifecycle_id,
    commit_ref,
    composed_refs,
    evidence_has_commit,
    evidence_has_ref,
    read_field,
    read_text,
)
from .governed_transition_typechecker_models import (
    GovernedTransitionCheck,
    GovernedTransitionError,
    GovernedTransitionErrorCode,
    GovernedTransitionInput,
    IllegalTransition,
    StaleProofRef,
)

COMMIT_ANCHOR_CLOSURE_EVENT = "CommitAnchorClosureProof"
BYPASS_EXPIRY_EVENT = "BypassExpiryReceipt"
ACK_TAGGED_RESOLUTION_EVENT = "AckTaggedResolution"
IDEMPOTENT_REEMIT_EVENT = "IdempotentReemit"

_LEGAL_TRANSITIONS: Mapping[tuple[str, str], frozenset[str]] = {
    ("classified", "ExceptionPolicyChecked"): frozenset({"exception_policy_checked"}),
    ("exception_policy_checked", "OperatorApproval"): frozenset({"operator_approved"}),
    ("operator_approved", COMMIT_ANCHOR_CLOSURE_EVENT): frozenset(
        {"closed", "closed_via_commit_anchor"}
    ),
    ("operator_approved", BYPASS_EXPIRY_EVENT): frozenset(
        {"closed", "closed_via_bypass_expiry"}
    ),
    ("operator_approved", ACK_TAGGED_RESOLUTION_EVENT): frozenset({"resolved"}),
    ("closed", IDEMPOTENT_REEMIT_EVENT): frozenset({"closed"}),
    ("closed_via_commit_anchor", IDEMPOTENT_REEMIT_EVENT): frozenset(
        {"closed_via_commit_anchor"}
    ),
    ("closed_via_bypass_expiry", IDEMPOTENT_REEMIT_EVENT): frozenset(
        {"closed_via_bypass_expiry"}
    ),
    ("resolved", IDEMPOTENT_REEMIT_EVENT): frozenset({"resolved"}),
}
_KNOWN_STATUSES: frozenset[str] = frozenset(
    {old for old, _ in _LEGAL_TRANSITIONS} | set().union(*_LEGAL_TRANSITIONS.values())
)
_CLOSED_STATUSES: frozenset[str] = frozenset(
    {"closed", "closed_via_commit_anchor", "closed_via_bypass_expiry", "resolved"}
)
_RESOLUTION_REQUIRED_STATUSES: frozenset[str] = _CLOSED_STATUSES
_CLOSURE_PROOF_REQUIRED_STATUSES: frozenset[str] = frozenset(
    {"closed", "closed_via_commit_anchor", "closed_via_bypass_expiry"}
)


class _TransitionState:
    __slots__ = (
        "inputs",
        "evidence",
        "now",
        "before_status",
        "after_status",
        "before_id",
        "after_id",
        "closure",
        "errors",
        "missing_refs",
        "illegal",
        "stale",
        "assertions",
    )

    def __init__(self, *, inputs: GovernedTransitionInput) -> None:
        before_id = read_text(inputs.before, "lifecycle_id")
        self.inputs = inputs
        self.evidence = inputs.evidence_index or {}
        self.now = inputs.now_utc or datetime.now(timezone.utc)
        self.before_status = read_text(inputs.before, "status")
        self.after_status = read_text(inputs.after, "status")
        self.before_id = before_id
        self.after_id = read_text(inputs.after, "lifecycle_id") or before_id
        self.closure = (
            inputs.closure_proof
            if inputs.closure_proof is not None
            else read_field(inputs.after, "closure_proof")
        )
        self.errors: list[GovernedTransitionError] = []
        self.missing_refs: list[str] = []
        self.illegal: list[IllegalTransition] = []
        self.stale: list[StaleProofRef] = []
        self.assertions = 0


def check_governed_exception_transition(
    inputs: GovernedTransitionInput,
) -> GovernedTransitionCheck:
    """Validate a governed exception lifecycle transition before accepting proof."""
    state = _state_from_inputs(inputs)
    _check_status_domain(state)
    _check_transition_legality(state)
    _check_closed_requisites(state)
    _check_closure_proof(state)
    _check_bypass_expiry(state)
    return _result(state)


def _state_from_inputs(inputs: GovernedTransitionInput) -> _TransitionState:
    return _TransitionState(inputs=inputs)


def _check_status_domain(state: _TransitionState) -> None:
    state.assertions += 1
    if state.before_status not in _KNOWN_STATUSES:
        _add_error(
            state,
            GovernedTransitionErrorCode.UNKNOWN_OLD_STATUS,
            f"old status {state.before_status!r} is not known",
            state.before_id,
        )
    state.assertions += 1
    if state.after_status not in _KNOWN_STATUSES:
        _add_error(
            state,
            GovernedTransitionErrorCode.UNKNOWN_NEW_STATUS,
            f"new status {state.after_status!r} is not known",
            state.after_id,
        )


def _check_transition_legality(state: _TransitionState) -> None:
    state.assertions += 1
    expected = _LEGAL_TRANSITIONS.get(
        (state.before_status, state.inputs.event_kind),
        frozenset(),
    )
    if state.after_status not in expected:
        transition = IllegalTransition(
            old_status=state.before_status,
            event_kind=state.inputs.event_kind,
            new_status=state.after_status,
            lifecycle_id=state.before_id,
        )
        state.illegal.append(transition)
        _add_error(
            state,
            GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
            (
                f"transition ({state.before_status!r}, "
                f"{state.inputs.event_kind!r}) -> {state.after_status!r} "
                "is not legal"
            ),
            state.before_id,
        )

    state.assertions += 1
    if _already_closed_non_idempotent(state):
        _add_error(
            state,
            GovernedTransitionErrorCode.ALREADY_CLOSED_NON_IDEMPOTENT,
            (
                f"closed lifecycle status {state.before_status!r} cannot move to "
                f"{state.after_status!r} via {state.inputs.event_kind!r}"
            ),
            state.before_id,
        )


def _check_closed_requisites(state: _TransitionState) -> None:
    if state.after_status in _RESOLUTION_REQUIRED_STATUSES:
        state.assertions += 1
        if read_field(state.inputs.after, "resolution") is None:
            _add_error(
                state,
                GovernedTransitionErrorCode.MISSING_RESOLUTION,
                f"status {state.after_status!r} requires a resolution receipt",
                state.after_id,
            )
    if state.after_status in _CLOSURE_PROOF_REQUIRED_STATUSES:
        state.assertions += 1
        if state.closure is None:
            _add_error(
                state,
                GovernedTransitionErrorCode.MISSING_CLOSURE_PROOF,
                f"status {state.after_status!r} requires a closure proof",
                state.after_id,
            )


def _check_closure_proof(state: _TransitionState) -> None:
    if state.closure is None:
        return
    state.assertions += 1
    proof_lifecycle_id = closure_lifecycle_id(state.closure)
    if proof_lifecycle_id and proof_lifecycle_id != state.before_id:
        _add_error(
            state,
            GovernedTransitionErrorCode.MISMATCHED_LIFECYCLE_ID,
            (
                f"closure proof lifecycle {proof_lifecycle_id!r} does not "
                f"match {state.before_id!r}"
            ),
            state.before_id,
        )
    _check_composed_refs(state)
    _check_commit_anchor(state)


def _check_composed_refs(state: _TransitionState) -> None:
    for ref in composed_refs(state.closure):
        state.assertions += 1
        if evidence_has_ref(state.evidence, ref):
            continue
        state.missing_refs.append(ref)
        _add_error(
            state,
            GovernedTransitionErrorCode.MISSING_COMPOSED_REF,
            f"composed ref {ref!r} is not present in evidence",
            state.after_id,
            composed_ref=ref,
        )


def _check_commit_anchor(state: _TransitionState) -> None:
    ref = commit_ref(state.closure)
    if state.inputs.event_kind != COMMIT_ANCHOR_CLOSURE_EVENT or not ref:
        return
    state.assertions += 1
    if evidence_has_commit(state.evidence, ref):
        return
    state.stale.append(
        StaleProofRef(
            proof_kind="commit_anchor",
            ref=ref,
            lifecycle_id=state.after_id,
            reason="commit anchor is absent from evidence_index",
        )
    )
    _add_error(
        state,
        GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR,
        f"commit anchor {ref!r} is not current evidence",
        state.after_id,
        composed_ref=ref,
    )


def _check_bypass_expiry(state: _TransitionState) -> None:
    if state.inputs.event_kind != BYPASS_EXPIRY_EVENT:
        return
    state.assertions += 1
    if bypass_still_active(
        bypass_lifecycle=state.inputs.bypass_lifecycle,
        bypass_expiry=state.inputs.bypass_expiry,
        now=state.now,
    ):
        _add_error(
            state,
            GovernedTransitionErrorCode.BYPASS_NOT_EXPIRED,
            "bypass lifecycle has not reached an expired terminal state",
            state.before_id,
        )
    state.assertions += 1
    if not bypass_links_to_exception(state.inputs.bypass_lifecycle, state.before_id):
        _add_error(
            state,
            GovernedTransitionErrorCode.BYPASS_NOT_LINKED_TO_EXCEPTION,
            "bypass lifecycle is not linked to the governed exception",
            state.before_id,
        )


def _result(state: _TransitionState) -> GovernedTransitionCheck:
    inputs_scanned = sum(
        1
        for value in (
            state.inputs.before,
            state.inputs.after,
            state.closure,
            state.inputs.bypass_lifecycle,
            state.inputs.bypass_expiry,
        )
        if value is not None
    )
    return GovernedTransitionCheck(
        ok=not state.errors and inputs_scanned > 0 and state.assertions > 0,
        errors=tuple(state.errors),
        missing_refs=tuple(dict.fromkeys(state.missing_refs)),
        illegal_transitions=tuple(state.illegal),
        stale_proofs=tuple(state.stale),
        inputs_scanned=inputs_scanned,
        assertions_evaluated=state.assertions,
    )


def _add_error(
    state: _TransitionState,
    code: GovernedTransitionErrorCode,
    message: str,
    lifecycle_id: str,
    *,
    composed_ref: str = "",
) -> None:
    state.errors.append(
        GovernedTransitionError(
            code=code,
            message=message,
            lifecycle_id=lifecycle_id,
            composed_ref=composed_ref,
        )
    )


def _already_closed_non_idempotent(state: _TransitionState) -> bool:
    return (
        state.before_status in _CLOSED_STATUSES
        and state.inputs.event_kind != IDEMPOTENT_REEMIT_EVENT
        and state.after_status != state.before_status
    )


__all__ = [
    "ACK_TAGGED_RESOLUTION_EVENT",
    "BYPASS_EXPIRY_EVENT",
    "COMMIT_ANCHOR_CLOSURE_EVENT",
    "IDEMPOTENT_REEMIT_EVENT",
    "GovernedTransitionCheck",
    "GovernedTransitionError",
    "GovernedTransitionErrorCode",
    "GovernedTransitionInput",
    "IllegalTransition",
    "StaleProofRef",
    "check_governed_exception_transition",
]
