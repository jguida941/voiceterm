"""Sequence checks that prove the next attempted action obeyed controller output."""

from __future__ import annotations

import hashlib
import shlex
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass

from .value_coercion import coerce_bool, coerce_string

ATTEMPTED_ACTION_RECEIPT_CONTRACT_ID = "AttemptedActionReceipt"
ATTEMPTED_ACTION_RECEIPT_SCHEMA_VERSION = 1
CONTROL_DECISION_OBEYED_CONTRACT_ID = "ControlDecisionObeyedGuard"
CONTROL_DECISION_OBEYED_SCHEMA_VERSION = 1
_REVIEW_CHANNEL_POST_ACTION_BY_KIND = {
    "finding": "review-channel.post_finding",
    "action_request": "review-channel.post_action_request",
    "continuation_anchor": "review-channel.post_continuation_anchor",
    "stop_anchor": "review-channel.post_stop_anchor",
}


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
        and not _allowed_controller_action(action, decision=decision)
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
    if decision_value == "wait" and not _allowed_controller_action(
        action,
        decision=decision,
    ):
        violations.append(
            ControlDecisionObedienceViolation(
                reason="non_observation_action_after_wait_decision",
                detail=_action_detail(action),
            )
        )
    if body_open_required and not _allowed_controller_action(
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
        _allowed_controller_action(action, decision=decision)
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


def _proxy_execution(
    *,
    executor_actor: str,
    executor_role: str,
    executor_session_id: str,
    subject_actor: str,
    subject_role: str,
    subject_session_id: str,
) -> bool:
    if not executor_actor or not subject_actor:
        return False
    if executor_actor != subject_actor:
        return True
    if executor_role and subject_role and executor_role != subject_role:
        return True
    if executor_session_id and subject_session_id and executor_session_id != subject_session_id:
        return True
    return False


def _action_mutates(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    if _allowed_controller_action(action, decision=decision):
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


def _allowed_controller_action(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    return _allowed_packet_attention_action(
        action,
        decision=decision,
    ) or _allowed_review_channel_post(action, decision=decision)


def _allowed_packet_attention_action(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    text = _action_text(action)
    is_show = "review-channel --action show" in text
    is_ingest = "review-channel --action ingest" in text
    is_absorb = "review-channel --action absorb" in text
    if not (is_show or is_ingest or is_absorb):
        return False
    packet_id = _packet_id_from_action(action)
    if is_absorb:
        if not coerce_bool(decision.get("absorption_required")):
            return False
        allowed_packet_ids = {
            coerce_string(decision.get("absorption_packet_id")),
            coerce_string(decision.get("attention_packet_id")),
        }
    elif is_ingest:
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


def _allowed_review_channel_post(
    action: Mapping[str, object],
    *,
    decision: Mapping[str, object],
) -> bool:
    argv = _action_argv(action)
    if not _argv_is_review_channel_post(argv, action):
        return False
    kind = _argv_option_value(argv, "--kind").strip().lower()
    required_allowed_action = _REVIEW_CHANNEL_POST_ACTION_BY_KIND.get(kind)
    if not required_allowed_action:
        return False
    allowed_actions = decision.get("allowed_actions")
    if not isinstance(allowed_actions, Sequence) or isinstance(
        allowed_actions,
        (str, bytes),
    ):
        return False
    normalized_allowed = {
        coerce_string(item).strip().lower() for item in allowed_actions
    }
    if required_allowed_action not in normalized_allowed:
        return False
    if kind == "action_request":
        return _allowed_review_channel_action_request_post(argv)
    return True


def _allowed_review_channel_action_request_post(argv: Sequence[str]) -> bool:
    requested_action = _argv_option_value(argv, "--requested-action").strip()
    target_kind = _argv_option_value(argv, "--target-kind").strip()
    target_ref = _argv_option_value(argv, "--target-ref").strip()
    target_revision = _argv_option_value(argv, "--target-revision").strip()
    guard_evidence = _argv_option_value(argv, "--full-guard-bundle-evidence").strip()
    return (
        requested_action == "stage_commit_pipeline"
        and target_kind == "runtime"
        and target_ref.startswith("devctl_commit:")
        and bool(target_revision)
        and bool(guard_evidence)
    )


def _argv_is_review_channel_post(
    argv: Sequence[str],
    action: Mapping[str, object],
) -> bool:
    normalized = tuple(coerce_string(item).strip().lower() for item in argv)
    if "review-channel" not in normalized:
        return False
    if _argv_option_value(normalized, "--action").strip().lower() == "post":
        return True
    return coerce_string(action.get("action_kind")).strip().lower() == "review-channel.post"


def _argv_option_value(argv: Sequence[str], option: str) -> str:
    for index, token in enumerate(argv):
        if coerce_string(token).strip().lower() != option:
            continue
        if index + 1 >= len(argv):
            return ""
        return coerce_string(argv[index + 1])
    return ""


def _action_argv(action: Mapping[str, object]) -> tuple[str, ...]:
    argv = action.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        return tuple(coerce_string(item).strip() for item in argv if coerce_string(item).strip())
    command = coerce_string(action.get("command")).strip()
    if command:
        try:
            return tuple(shlex.split(command))
        except ValueError:
            return tuple(command.split())
    return ()


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
