"""Sequence checks that prove the next attempted action obeyed controller output."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass

from .control_decision_action_matching import (
    action_mutates,
    action_text,
    allowed_controller_action,
)
from .value_coercion import coerce_bool, coerce_string

ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID = "AttemptedActionReceipt"
ATTEMPTED_ACTION_RECEIPT_SCHEMA_VERSION = 1
CONTROL_DECISION_OBEYED_CONTRACT_ID = "ControlDecisionObeyedGuard"
CONTROL_DECISION_OBEYED_SCHEMA_VERSION = 1
@dataclass(frozen=True, slots=True)
class AttemptedActionReceipt:
    receipt_id: str
    action_kind: str
    command: str
    argv: tuple[str, ...]
    actor: str
    role: str
    session_id: str
    executor_actor: str
    executor_role: str
    executor_session_id: str
    subject_actor: str
    subject_role: str
    subject_session_id: str
    proxy_execution: bool
    proxy_authority_ref: str
    mutates: bool
    writes_state: bool
    executes_command: bool
    source_decision_id: str
    source_snapshot_id: str
    source_latest_event_id: str
    started_at_utc: str
    schema_version: int = ATTEMPTED_ACTION_RECEIPT_SCHEMA_VERSION
    contract_id: str = ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["argv"] = list(self.argv)
        return payload


@dataclass(frozen=True, slots=True)
class ControlDecisionObedienceViolation:
    reason: str
    detail: str = ""
    severity: str = "blocking"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StaleControllerDecisionBlocker:
    """v4.43 (rev_pkt_4715): typed blocker for stale-source-decision failures.

    Emitted when ``_violations_for_action`` would report opaque obedience
    violations BUT the underlying decision input is older than the
    attempted action's observed event id. Distinguishes "your action is
    wrong" (real violation) from "your decision input was stale" (refresh
    decision and retry).

    Codex's rev_pkt_4715 reproduction: ``review_accepted`` post against
    fresh body-observed state failed with 4 raw violations because the
    decision input was sourced from ``agent-runtime-clock:rev_evt_84896``
    while the action observed a much later event id. Refreshing the
    decision would have made the action legal.
    """

    blocker_id: str
    decision_source_latest_event_id: str
    action_observed_event_id: str
    suppressed_violation_reasons: tuple[str, ...] = ()
    detail: str = ""
    schema_version: int = 1
    contract_id: str = "StaleControllerDecisionBlocker"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["suppressed_violation_reasons"] = list(
            self.suppressed_violation_reasons
        )
        return payload


DEFAULT_EXPECTED_DECISION_PATH = (
    "dev/reports/review_channel/state/latest.json"
)


@dataclass(frozen=True, slots=True)
class MissingDecisionRefreshHint:
    """Typed recovery hint when no controller decision was supplied.

    Invariant C (TDD Inv 4): when ``evaluate_control_decision_obedience``
    receives ``decision=None`` and ``allow_empty=False``, the consumer needs
    a typed recovery shape that names the exact controller artifact path the
    obedience layer expected to read AND the per-actor/role/session refresh
    command. Raw ``no_control_decision_input`` violations alone tell the
    caller *that* the decision was missing but not *how* to recover.
    """

    hint_id: str
    next_command: str
    refresh_command: str
    expected_decision_path: str = DEFAULT_EXPECTED_DECISION_PATH
    actor: str = ""
    role: str = ""
    session_id: str = ""
    detail: str = ""
    schema_version: int = 1
    contract_id: str = "MissingDecisionRefreshHint"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ControlDecisionObedienceReport:
    ok: bool
    decision_present: bool
    attempted_action_count: int
    violation_count: int
    violations: tuple[dict[str, str], ...] = ()
    # v4.43 (rev_pkt_4715): when an obedience failure is driven by stale
    # decision input (vs. a real action violation), the report carries a
    # typed ``stale_decision_blocker`` so consumers can refresh the
    # decision and retry instead of seeing raw violations.
    stale_decision_blocker: dict[str, object] | None = None
    missing_decision_refresh_hint: dict[str, object] | None = None
    next_command: str = ""
    refresh_command: str = ""
    schema_version: int = CONTROL_DECISION_OBEYED_SCHEMA_VERSION
    contract_id: str = CONTROL_DECISION_OBEYED_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_control_decision_obedience(
    *,
    decision: Mapping[str, object] | None,
    attempted_actions: Iterable[Mapping[str, object]],
    allow_empty: bool = False,
    actor: str = "",
    role: str = "",
    session_id: str = "",
    expected_decision_path: str = DEFAULT_EXPECTED_DECISION_PATH,
) -> ControlDecisionObedienceReport:
    """Fail when an attempted action violates the last controller decision.

    v4.43 (rev_pkt_4715): when violations are driven by stale decision
    input (the decision's ``source_latest_event_id`` is older than the
    attempted action's observed event id), a typed
    ``StaleControllerDecisionBlocker`` is emitted instead of (or alongside)
    the raw violations. Consumers can distinguish "refresh decision and
    retry" from "real action violation, fix the action".

    Invariant C (TDD Inv 4): when ``decision is None`` and
    ``allow_empty=False`` the report carries a typed
    ``MissingDecisionRefreshHint`` so callers can refresh the controller
    artifact and retry. The hint names the per-actor/role/session refresh
    command and the canonical typed-state path the loader expected to read.
    Optional ``actor``/``role``/``session_id`` kwargs let callers thread
    their own scope when no attempted action carries one; the
    ``expected_decision_path`` kwarg lets non-default loaders override the
    canonical artifact path.
    """

    actions = tuple(attempted_actions)
    violations: list[ControlDecisionObedienceViolation] = []
    missing_decision_refresh_hint_payload: dict[str, object] | None = None
    next_command = ""
    refresh_command = ""
    if decision is None and not allow_empty:
        violations.append(
            ControlDecisionObedienceViolation(
                reason="no_control_decision_input",
                detail="No AgentLoopDecision/control decision was supplied.",
            )
        )
        hint = _missing_decision_refresh_hint(
            actions,
            actor=actor,
            role=role,
            session_id=session_id,
            expected_decision_path=expected_decision_path,
        )
        missing_decision_refresh_hint_payload = hint.to_dict()
        next_command = hint.next_command
        refresh_command = hint.refresh_command
    if not actions and not allow_empty:
        violations.append(
            ControlDecisionObedienceViolation(
                reason="no_attempted_action_input",
                detail="No attempted action was supplied.",
            )
        )
    if decision is not None:
        for action in actions:
            violations.extend(_violations_for_action(decision, action))
    violation_payloads = tuple(violation.to_dict() for violation in violations)

    # v4.43 (rev_pkt_4715): detect stale-decision failures and emit typed
    # blocker. Triggers when ALL of the following hold:
    #   - decision is present (not a no_control_decision_input failure)
    #   - at least one obedience violation fired
    #   - the decision's source_latest_event_id is strictly older than the
    #     observed event id on at least one attempted action
    stale_decision_blocker_payload: dict[str, object] | None = None
    if decision is not None and violations and actions:
        stale_blocker = _detect_stale_decision_blocker(decision, actions, violations)
        if stale_blocker is not None:
            stale_decision_blocker_payload = stale_blocker.to_dict()

    return ControlDecisionObedienceReport(
        ok=not violation_payloads,
        decision_present=decision is not None,
        attempted_action_count=len(actions),
        violation_count=len(violation_payloads),
        violations=violation_payloads,
        stale_decision_blocker=stale_decision_blocker_payload,
        missing_decision_refresh_hint=missing_decision_refresh_hint_payload,
        next_command=next_command,
        refresh_command=refresh_command,
    )


def _missing_decision_refresh_hint(
    actions: tuple[Mapping[str, object], ...],
    *,
    actor: str = "",
    role: str = "",
    session_id: str = "",
    expected_decision_path: str = DEFAULT_EXPECTED_DECISION_PATH,
) -> MissingDecisionRefreshHint:
    """Build a typed refresh hint scoped to the caller's actor/role/session.

    Caller-supplied ``actor``/``role``/``session_id`` kwargs win; otherwise
    the first attempted-action row supplying each field is used. The
    ``next_command`` template threads the resolved scope into
    ``develop next`` so the refresh runs in the same role/session the
    consumer is acting under.
    """

    resolved_actor = coerce_string(actor).strip() or _first_action_field(
        actions, "actor"
    )
    resolved_role = coerce_string(role).strip() or _first_action_field(
        actions, "role"
    )
    resolved_session_id = coerce_string(session_id).strip() or _first_action_field(
        actions, "session_id"
    )
    expected_path = (
        coerce_string(expected_decision_path).strip() or DEFAULT_EXPECTED_DECISION_PATH
    )
    parts = ["python3", "dev/scripts/devctl.py", "develop", "next"]
    if resolved_actor:
        parts.extend(("--actor", resolved_actor))
    if resolved_role:
        parts.extend(("--role", resolved_role))
    if resolved_session_id:
        parts.extend(("--session-id", resolved_session_id))
    parts.extend(("--format", "json"))
    command = " ".join(parts)
    return MissingDecisionRefreshHint(
        hint_id="missing_control_decision:refresh_agent_loop_decision",
        next_command=command,
        refresh_command=command,
        expected_decision_path=expected_path,
        actor=resolved_actor,
        role=resolved_role,
        session_id=resolved_session_id,
        detail=(
            "No AgentLoopDecision/control decision was supplied. Refresh the "
            f"typed controller decision at {expected_path} and retry the "
            "attempted action against that fresh decision."
        ),
    )


def _first_action_field(
    actions: tuple[Mapping[str, object], ...],
    field: str,
) -> str:
    for action in actions:
        value = coerce_string(action.get(field)).strip()
        if value:
            return value
    return ""


def _detect_stale_decision_blocker(
    decision: Mapping[str, object],
    actions: tuple[Mapping[str, object], ...],
    violations: list[ControlDecisionObedienceViolation],
) -> StaleControllerDecisionBlocker | None:
    """Return a typed blocker if the obedience failure is driven by stale state.

    v4.43 (rev_pkt_4715): the decision's ``source_latest_event_id`` is
    compared against each attempted action's observed event id (or
    ``started_at_utc`` as a fallback). When the decision is strictly older
    by event-rank, the obedience violations are likely artifacts of stale
    state — the consumer should refresh the decision and retry rather
    than treat them as real action violations.

    v4.43.1 (rev_pkt_4716): the live ``_review_channel_lifecycle_gate``
    copies the action's ``source_latest_event_id`` from the loaded decision
    (same event id on both sides → never triggers). The detector now
    PREFERS ``observed_event_id`` when set — this is the gate-supplied
    fresh observation from canonical typed review-channel state, distinct
    from the action's source-decision provenance.
    """
    decision_event_id = coerce_string(
        decision.get("source_latest_event_id")
    ).strip()
    if not decision_event_id:
        return None
    decision_rank = _event_id_rank(decision_event_id)
    if decision_rank < 0:
        return None
    for action in actions:
        # v4.43.1: prefer the gate-supplied ``observed_event_id`` (canonical
        # review-channel state) over the action's ``source_latest_event_id``
        # (copied from the decision and therefore equal to ``decision_event_id``
        # in the live path).
        action_event_id = coerce_string(
            action.get("observed_event_id")
            or action.get("source_latest_event_id")
            or action.get("latest_event_id")
        ).strip()
        if not action_event_id:
            continue
        action_rank = _event_id_rank(action_event_id)
        if action_rank < 0:
            continue
        if action_rank > decision_rank:
            blocker_id = (
                f"stale_decision:{decision_event_id}:vs:{action_event_id}"
            )
            return StaleControllerDecisionBlocker(
                blocker_id=blocker_id,
                decision_source_latest_event_id=decision_event_id,
                action_observed_event_id=action_event_id,
                suppressed_violation_reasons=tuple(
                    v.reason for v in violations
                ),
                detail=(
                    f"Decision input is from {decision_event_id}; attempted "
                    f"action observed {action_event_id}. Refresh decision "
                    f"before retrying."
                ),
            )
    return None


def _event_id_rank(event_id: str) -> int:
    """Extract the numeric rank from a ``rev_evt_NNNNN`` event id.

    Returns -1 if the input is not in the expected form so callers can
    fall back to event-id-string equality. Mirrors the helper in
    ``review_channel/event_models.py:event_id_rank`` but locally inlined
    so this guard module stays leaf-safe (no review_channel imports).
    """
    prefix = "rev_evt_"
    if not event_id.startswith(prefix):
        return -1
    try:
        return int(event_id[len(prefix):])
    except ValueError:
        return -1


def build_attempted_action_receipt(
    *,
    action_kind: str,
    command: str,
    argv: Sequence[str] = (),
    actor: str = "",
    role: str = "",
    session_id: str = "",
    executor_actor: str = "",
    executor_role: str = "",
    executor_session_id: str = "",
    subject_actor: str = "",
    subject_role: str = "",
    subject_session_id: str = "",
    proxy_authority_ref: str = "",
    mutates: bool = False,
    writes_state: bool = False,
    executes_command: bool = False,
    source_decision_id: str = "",
    source_snapshot_id: str = "",
    source_latest_event_id: str = "",
    started_at_utc: str = "",
) -> AttemptedActionReceipt:
    argv_tuple = tuple(coerce_string(item) for item in argv if coerce_string(item))
    subject_actor_value = coerce_string(subject_actor) or coerce_string(actor)
    subject_role_value = coerce_string(subject_role) or coerce_string(role)
    subject_session_value = coerce_string(subject_session_id) or coerce_string(
        session_id
    )
    executor_actor_value = coerce_string(executor_actor) or subject_actor_value
    executor_role_value = coerce_string(executor_role) or subject_role_value
    executor_session_value = coerce_string(executor_session_id) or subject_session_value
    proxy_execution = _proxy_execution(
        executor_actor=executor_actor_value,
        executor_role=executor_role_value,
        executor_session_id=executor_session_value,
        subject_actor=subject_actor_value,
        subject_role=subject_role_value,
        subject_session_id=subject_session_value,
    )
    fingerprint_source = "\x00".join(
        (
            coerce_string(action_kind),
            coerce_string(command),
            "\x1f".join(argv_tuple),
            coerce_string(actor),
            coerce_string(role),
            coerce_string(session_id),
            executor_actor_value,
            executor_role_value,
            executor_session_value,
            subject_actor_value,
            subject_role_value,
            subject_session_value,
            str(proxy_execution),
            coerce_string(proxy_authority_ref),
            str(bool(mutates)),
            str(bool(writes_state)),
            str(bool(executes_command)),
            coerce_string(source_decision_id),
            coerce_string(source_snapshot_id),
            coerce_string(source_latest_event_id),
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return AttemptedActionReceipt(
        receipt_id=f"attempted_action:{coerce_string(action_kind)}:{fingerprint}",
        action_kind=coerce_string(action_kind),
        command=coerce_string(command),
        argv=argv_tuple,
        actor=coerce_string(actor),
        role=coerce_string(role),
        session_id=coerce_string(session_id),
        executor_actor=executor_actor_value,
        executor_role=executor_role_value,
        executor_session_id=executor_session_value,
        subject_actor=subject_actor_value,
        subject_role=subject_role_value,
        subject_session_id=subject_session_value,
        proxy_execution=proxy_execution,
        proxy_authority_ref=coerce_string(proxy_authority_ref),
        mutates=bool(mutates),
        writes_state=bool(writes_state),
        executes_command=bool(executes_command),
        source_decision_id=coerce_string(source_decision_id),
        source_snapshot_id=coerce_string(source_snapshot_id),
        source_latest_event_id=coerce_string(source_latest_event_id),
        started_at_utc=coerce_string(started_at_utc),
    )


def extract_decision_and_attempted_actions(
    payload: object,
) -> tuple[Mapping[str, object] | None, tuple[Mapping[str, object], ...]]:
    """Extract one decision plus attempted action rows from a report payload."""

    if not isinstance(payload, Mapping):
        return None, ()
    decision = _decision_from_payload(payload)
    actions: list[Mapping[str, object]] = []
    for key in ("attempted_action", "next_attempted_action"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            actions.append(value)
    for key in ("attempted_actions", "next_attempted_actions"):
        value = payload.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            actions.extend(item for item in value if isinstance(item, Mapping))
    _collect_attempted_action_receipts(payload, actions)
    return decision, tuple(actions)


def _decision_from_payload(payload: Mapping[str, object]) -> Mapping[str, object] | None:
    decision = payload.get("agent_loop_decision") or payload.get("control_decision")
    if isinstance(decision, Mapping):
        return decision
    if coerce_string(payload.get("contract_id")) == "AgentLoopDecision":
        return payload
    return None


def _collect_attempted_action_receipts(
    payload: object,
    actions: list[Mapping[str, object]],
) -> None:
    if isinstance(payload, Mapping):
        if coerce_string(payload.get("contract_id")) == ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID:
            receipt_id = coerce_string(payload.get("receipt_id"))
            if receipt_id and any(
                coerce_string(action.get("receipt_id")) == receipt_id
                for action in actions
            ):
                return
            actions.append(payload)
            return
        for value in payload.values():
            _collect_attempted_action_receipts(value, actions)
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for item in payload:
            _collect_attempted_action_receipts(item, actions)


def _violations_for_action(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> list[ControlDecisionObedienceViolation]:
    violations: list[ControlDecisionObedienceViolation] = []
    violations.extend(_scope_violations_for_action(decision, action))
    violations.extend(_proxy_violations_for_action(decision, action))
    may_mutate = coerce_bool(decision.get("may_mutate"))
    can_run_next_command = coerce_bool(decision.get("can_run_next_command"))
    override = decision.get("operator_override")
    override_payload = override if isinstance(override, Mapping) else {}
    override_requested = coerce_bool(override_payload.get("requested"))
    override_active = coerce_bool(override_payload.get("active"))
    decision_value = _norm(decision.get("decision"))
    required_action = _norm(decision.get("required_action"))
    body_open_required = coerce_bool(decision.get("body_open_required"))

    if may_mutate is False and action_mutates(action, decision=decision):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="mutation_attempt_after_may_mutate_false",
                detail=_action_detail(action),
            )
        )
    if (
        can_run_next_command is False
        and _action_executes_command(action)
        and not allowed_controller_action(action, decision=decision)
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="command_attempt_after_can_run_next_command_false",
                detail=_action_detail(action),
            )
        )
    if override_requested and not override_active and action_mutates(
        action,
        decision=decision,
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="mutation_attempt_after_override_inactive",
                detail=_action_detail(action),
            )
        )
    if decision_value == "wait" and not allowed_controller_action(
        action,
        decision=decision,
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="non_observation_action_after_wait_decision",
                detail=_action_detail(action),
            )
        )
    if body_open_required and not allowed_controller_action(
        action,
        decision=decision,
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="non_body_open_action_after_body_open_required",
                detail=_action_detail(action),
            )
        )
    if required_action.startswith("wait_for_scoped_packet") and not (
        allowed_controller_action(action, decision=decision)
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="non_packet_attention_action_after_wait_for_scoped_packet",
                detail=_action_detail(action),
            )
        )
    return violations


def _scope_violations_for_action(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> list[ControlDecisionObedienceViolation]:
    violations: list[ControlDecisionObedienceViolation] = []
    for decision_key, action_key, reason in (
        ("actor_id", "actor", "attempted_action_actor_scope_mismatch"),
        ("actor_role", "role", "attempted_action_role_scope_mismatch"),
        ("session_id", "session_id", "attempted_action_session_scope_mismatch"),
    ):
        expected = coerce_string(decision.get(decision_key)).strip()
        if not expected:
            continue
        actual = coerce_string(action.get(action_key)).strip()
        if not actual or actual != expected:
            violations.append(
                ControlDecisionObedienceViolation(
                    reason=reason,
                    detail=(
                        f"{action_key}={actual or '(missing)'};"
                        f"expected={expected}"
                    ),
                )
            )
    return violations


def _proxy_violations_for_action(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> list[ControlDecisionObedienceViolation]:
    if not _action_proxy_execution(action):
        return []
    proxy_ref = coerce_string(action.get("proxy_authority_ref")).strip()
    if not proxy_ref:
        return [
            ControlDecisionObedienceViolation(
                reason="attempted_action_proxy_authority_missing",
                detail=(
                    f"executor_actor={coerce_string(action.get('executor_actor')) or '(missing)'};"
                    f"subject_actor={coerce_string(action.get('subject_actor')) or coerce_string(action.get('actor')) or '(missing)'}"
                ),
            )
        ]
    decision_refs = _decision_proxy_authority_refs(decision)
    if not decision_refs:
        return [
            ControlDecisionObedienceViolation(
                reason="attempted_action_proxy_authority_unbound",
                detail="Loaded decision has no receipt_id/source_snapshot_id/source_latest_event_id.",
            )
        ]
    if proxy_ref not in decision_refs:
        return [
            ControlDecisionObedienceViolation(
                reason="attempted_action_proxy_authority_mismatch",
                detail=f"proxy_authority_ref={proxy_ref};expected_one_of={','.join(sorted(decision_refs))}",
            )
        ]
    return []


def _decision_proxy_authority_refs(decision: Mapping[str, object]) -> set[str]:
    return {
        value
        for value in (
            coerce_string(decision.get("receipt_id")).strip(),
            coerce_string(decision.get("source_decision_id")).strip(),
            coerce_string(decision.get("source_snapshot_id")).strip(),
            coerce_string(decision.get("source_latest_event_id")).strip(),
        )
        if value
    }


def _action_proxy_execution(action: Mapping[str, object]) -> bool:
    explicit = action.get("proxy_execution")
    if explicit is not None:
        return coerce_bool(explicit)
    return _proxy_execution(
        executor_actor=coerce_string(action.get("executor_actor")),
        executor_role=coerce_string(action.get("executor_role")),
        executor_session_id=coerce_string(action.get("executor_session_id")),
        subject_actor=(
            coerce_string(action.get("subject_actor"))
            or coerce_string(action.get("actor"))
        ),
        subject_role=(
            coerce_string(action.get("subject_role")) or coerce_string(action.get("role"))
        ),
        subject_session_id=(
            coerce_string(action.get("subject_session_id"))
            or coerce_string(action.get("session_id"))
        ),
    )


# v4.41 (rev_pkt_4713): ``_proxy_execution`` moved to the neutral
# ``runtime/proxy_execution.py`` module so downstream modules (e.g.
# ``command_envelope_classification``) can consume the primitive without
# importing the whole control-decision-obedience graph. The name is
# re-exported here for backwards-compat — existing callers continue to
# import ``_proxy_execution`` from ``control_decision_obedience``.
from .proxy_execution import _proxy_execution as _proxy_execution  # noqa: PLC0414


def _action_executes_command(action: Mapping[str, object]) -> bool:
    if coerce_bool(action.get("executes_command")):
        return True
    return bool(action_text(action))


def _action_detail(action: Mapping[str, object]) -> str:
    return action_text(action) or repr(dict(action))


def _norm(value: object) -> str:
    return coerce_string(value).strip().lower().replace("-", "_").replace(" ", "_")


__all__ = [
    "ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID",
    "ATTEMPTED_ACTION_RECEIPT_SCHEMA_VERSION",
    "CONTROL_DECISION_OBEYED_CONTRACT_ID",
    "CONTROL_DECISION_OBEYED_SCHEMA_VERSION",
    "DEFAULT_EXPECTED_DECISION_PATH",
    "AttemptedActionReceipt",
    "ControlDecisionObedienceReport",
    "ControlDecisionObedienceViolation",
    "MissingDecisionRefreshHint",
    "StaleControllerDecisionBlocker",
    "build_attempted_action_receipt",
    "evaluate_control_decision_obedience",
    "extract_decision_and_attempted_actions",
]
