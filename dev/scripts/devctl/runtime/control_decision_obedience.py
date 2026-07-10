"""Sequence checks that prove the next attempted action obeyed controller output."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass

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
    mutates: bool
    writes_state: bool
    executes_command: bool
    source_decision_id: str
    source_snapshot_id: str
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
class ControlDecisionObedienceReport:
    ok: bool
    decision_present: bool
    attempted_action_count: int
    violation_count: int
    violations: tuple[dict[str, str], ...] = ()
    schema_version: int = CONTROL_DECISION_OBEYED_SCHEMA_VERSION
    contract_id: str = CONTROL_DECISION_OBEYED_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_control_decision_obedience(
    *,
    decision: Mapping[str, object] | None,
    attempted_actions: Iterable[Mapping[str, object]],
    allow_empty: bool = False,
) -> ControlDecisionObedienceReport:
    """Fail when an attempted action violates the last controller decision."""

    actions = tuple(attempted_actions)
    violations: list[ControlDecisionObedienceViolation] = []
    if decision is None and not allow_empty:
        violations.append(
            ControlDecisionObedienceViolation(
                reason="no_control_decision_input",
                detail="No AgentLoopDecision/control decision was supplied.",
            )
        )
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
    return ControlDecisionObedienceReport(
        ok=not violation_payloads,
        decision_present=decision is not None,
        attempted_action_count=len(actions),
        violation_count=len(violation_payloads),
        violations=violation_payloads,
    )


def build_attempted_action_receipt(
    *,
    action_kind: str,
    command: str,
    argv: Sequence[str] = (),
    actor: str = "",
    role: str = "",
    session_id: str = "",
    mutates: bool = False,
    writes_state: bool = False,
    executes_command: bool = False,
    source_decision_id: str = "",
    source_snapshot_id: str = "",
    started_at_utc: str = "",
) -> AttemptedActionReceipt:
    argv_tuple = tuple(coerce_string(item) for item in argv if coerce_string(item))
    fingerprint_source = "\x00".join(
        (
            coerce_string(action_kind),
            coerce_string(command),
            "\x1f".join(argv_tuple),
            coerce_string(actor),
            coerce_string(role),
            coerce_string(session_id),
            str(bool(mutates)),
            str(bool(writes_state)),
            str(bool(executes_command)),
            coerce_string(source_decision_id),
            coerce_string(source_snapshot_id),
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
        mutates=bool(mutates),
        writes_state=bool(writes_state),
        executes_command=bool(executes_command),
        source_decision_id=coerce_string(source_decision_id),
        source_snapshot_id=coerce_string(source_snapshot_id),
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
    may_mutate = coerce_bool(decision.get("may_mutate"))
    can_run_next_command = coerce_bool(decision.get("can_run_next_command"))
    override = decision.get("operator_override")
    override_payload = override if isinstance(override, Mapping) else {}
    override_requested = coerce_bool(override_payload.get("requested"))
    override_active = coerce_bool(override_payload.get("active"))
    decision_value = _norm(decision.get("decision"))
    required_action = _norm(decision.get("required_action"))
    body_open_required = coerce_bool(decision.get("body_open_required"))

    if may_mutate is False and _action_mutates(action, decision=decision):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="mutation_attempt_after_may_mutate_false",
                detail=_action_detail(action),
            )
        )
    if (
        can_run_next_command is False
        and _action_executes_command(action)
        and not _allowed_packet_attention_action(action, decision=decision)
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="command_attempt_after_can_run_next_command_false",
                detail=_action_detail(action),
            )
        )
    if override_requested and not override_active and _action_mutates(
        action,
        decision=decision,
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="mutation_attempt_after_override_inactive",
                detail=_action_detail(action),
            )
        )
    if decision_value == "wait" and not _allowed_packet_attention_action(
        action,
        decision=decision,
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="non_observation_action_after_wait_decision",
                detail=_action_detail(action),
            )
        )
    if body_open_required and not _allowed_packet_attention_action(
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
        _allowed_packet_attention_action(action, decision=decision)
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="non_packet_attention_action_after_wait_for_scoped_packet",
                detail=_action_detail(action),
            )
        )
    return violations


def _action_mutates(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    if _allowed_packet_attention_action(action, decision=decision):
        return False
    if coerce_bool(action.get("mutates")) or coerce_bool(action.get("writes_state")):
        return True
    text = _action_text(action)
    mutation_tokens = (
        "apply_patch",
        "git commit",
        "git push",
        "raw-git",
        "raw_git",
        "devctl.py push",
        " review-channel --action post",
        " review-channel --action apply",
        " review-channel --action dismiss",
        " review-channel --action absorb",
    )
    return any(token in text for token in mutation_tokens)


def _action_executes_command(action: Mapping[str, object]) -> bool:
    if coerce_bool(action.get("executes_command")):
        return True
    return bool(_action_text(action))


def _allowed_packet_attention_action(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    text = _action_text(action)
    is_show = "review-channel --action show" in text
    is_ingest = "review-channel --action ingest" in text
    if not (is_show or is_ingest):
        return False
    packet_id = _packet_id_from_action(action)
    if is_ingest:
        if not coerce_bool(decision.get("semantic_ingestion_required")):
            return False
        allowed_packet_ids = {
            coerce_string(decision.get("semantic_ingestion_packet_id")),
            coerce_string(decision.get("attention_packet_id")),
        }
    else:
        if not coerce_bool(decision.get("body_open_required")):
            return False
        allowed_packet_ids = {
            coerce_string(decision.get("body_open_packet_id")),
            coerce_string(decision.get("active_packet_id")),
            coerce_string(decision.get("attention_packet_id")),
        }
    allowed_packet_ids.discard("")
    return bool(allowed_packet_ids) and packet_id in allowed_packet_ids


def _packet_id_from_action(action: Mapping[str, object]) -> str:
    explicit = coerce_string(action.get("packet_id"))
    if explicit:
        return explicit
    text = _action_text(action)
    marker = "--packet-id "
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split()[0].strip("'\"")


def _action_text(action: Mapping[str, object]) -> str:
    argv = action.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        return " ".join(coerce_string(item) for item in argv).lower()
    return " ".join(
        coerce_string(action.get(key))
        for key in ("action_kind", "command_name", "command", "next_action")
    ).lower()


def _action_detail(action: Mapping[str, object]) -> str:
    return _action_text(action) or repr(dict(action))


def _norm(value: object) -> str:
    return coerce_string(value).strip().lower().replace("-", "_").replace(" ", "_")


__all__ = [
    "ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID",
    "ATTEMPTED_ACTION_RECEIPT_SCHEMA_VERSION",
    "CONTROL_DECISION_OBEYED_CONTRACT_ID",
    "CONTROL_DECISION_OBEYED_SCHEMA_VERSION",
    "AttemptedActionReceipt",
    "ControlDecisionObedienceReport",
    "ControlDecisionObedienceViolation",
    "build_attempted_action_receipt",
    "evaluate_control_decision_obedience",
    "extract_decision_and_attempted_actions",
]
