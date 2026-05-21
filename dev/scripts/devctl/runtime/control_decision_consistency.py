"""Consistency checks for authority-bearing controller decisions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass

from .value_coercion import coerce_bool, coerce_string

CONTROL_DECISION_CONSISTENCY_CONTRACT_ID = "ControlDecisionConsistencyGuard"
CONTROL_DECISION_CONSISTENCY_SCHEMA_VERSION = 1
CONTROL_DECISION_VIOLATION_CONTRACT_ID = "ControlDecisionConsistencyViolation"


@dataclass(frozen=True, slots=True)
class ControlDecisionViolation:
    """A contradiction inside one controller decision payload."""

    source: str
    reason: str
    detail: str = ""
    severity: str = "blocking"
    schema_version: int = CONTROL_DECISION_CONSISTENCY_SCHEMA_VERSION
    contract_id: str = CONTROL_DECISION_VIOLATION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ControlDecisionConsistencyReport:
    """Guard report over one or more controller decisions."""

    ok: bool
    decision_count: int
    violation_count: int
    violations: tuple[dict[str, object], ...] = ()
    schema_version: int = CONTROL_DECISION_CONSISTENCY_SCHEMA_VERSION
    contract_id: str = CONTROL_DECISION_CONSISTENCY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_control_decision_consistency(
    decisions: Iterable[Mapping[str, object]],
    *,
    source: str = "control-decision",
    allow_empty: bool = False,
) -> ControlDecisionConsistencyReport:
    """Return a fail-closed report for contradictory controller output."""

    rows = tuple(decisions)
    violations: list[ControlDecisionViolation] = []
    if not rows and not allow_empty:
        violation = ControlDecisionViolation(
            source=source,
            reason="no_control_decision_input",
            detail="No AgentLoopDecision/control decision was supplied or loaded.",
        )
        return ControlDecisionConsistencyReport(
            ok=False,
            decision_count=0,
            violation_count=1,
            violations=(violation.to_dict(),),
        )
    for index, decision in enumerate(rows):
        decision_source = _decision_source(decision, source=source, index=index)
        violations.extend(
            control_decision_violations(decision, source=decision_source)
        )
    violation_payloads = tuple(violation.to_dict() for violation in violations)
    return ControlDecisionConsistencyReport(
        ok=not violation_payloads,
        decision_count=len(rows),
        violation_count=len(violation_payloads),
        violations=violation_payloads,
    )


def control_decision_violations(
    decision: Mapping[str, object],
    *,
    source: str = "control-decision",
) -> tuple[ControlDecisionViolation, ...]:
    """Evaluate one controller decision mapping for semantic contradictions."""

    violations: list[ControlDecisionViolation] = []
    next_action = _text(decision.get("next_action"))
    next_command = _text(decision.get("next_command"))
    may_mutate = _bool(decision.get("may_mutate"))
    can_run_next_command = _bool(decision.get("can_run_next_command"))
    decision_value = _normalized(decision.get("decision"))
    required_action = _normalized(decision.get("required_action"))
    top_blocker = _normalized(decision.get("top_blocker"))
    operator_override = decision.get("operator_override")
    override_payload = operator_override if isinstance(operator_override, Mapping) else {}
    override_requested = _bool(override_payload.get("requested"))
    override_active = _bool(override_payload.get("active"))

    if may_mutate is False and _mutation_next_action(next_action):
        reason = (
            "push_projected_while_mutation_blocked"
            if _push_action(next_action)
            else "mutation_projected_while_mutation_blocked"
        )
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason=reason,
                detail=f"may_mutate=false next_action={next_action}",
            )
        )
    # v4.42 (rev_pkt_4714 Finding 2): when next_action is blank but
    # next_command names a governed mutation, still flag the violation —
    # may_mutate=False must hold regardless of which surface carries the
    # mutation intent.
    elif (
        may_mutate is False
        and not _mutation_next_action(next_action)
        and _mutation_next_command(next_command)
    ):
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="mutation_command_projected_while_mutation_blocked",
                detail=f"may_mutate=false next_command={next_command}",
            )
        )

    violations.extend(
        _packet_lifecycle_command_violations(
            decision,
            source=source,
            next_command=next_command,
        )
    )

    if (
        can_run_next_command is False
        and _actionable_next_command(next_command)
        and not _controller_permitted_next_command(decision, next_command)
    ):
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="next_command_projected_while_command_blocked",
                detail=f"can_run_next_command=false next_command={next_command}",
            )
        )

    if (
        override_requested is True
        and override_active is False
        and _mutation_next_action(next_action)
    ):
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="mutation_projected_while_override_inactive",
                detail=f"operator_override.active=false next_action={next_action}",
            )
        )

    if decision_value == "wait" and _blocker_is_none(top_blocker):
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="wait_decision_without_blocker",
                detail="decision=wait top_blocker=none",
            )
        )

    if _requires_blocker(required_action) and _blocker_is_none(top_blocker):
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="required_action_without_blocker",
                detail=f"required_action={required_action} top_blocker=none",
            )
        )

    return tuple(violations)


def extract_control_decisions(payload: object) -> tuple[Mapping[str, object], ...]:
    """Extract known controller decision rows from a report-like payload."""

    rows: list[Mapping[str, object]] = []
    _append_control_decisions(payload, rows)
    return tuple(rows)


def _append_control_decisions(payload: object, rows: list[Mapping[str, object]]) -> None:
    if isinstance(payload, Mapping):
        if _text(payload.get("contract_id")) == "AgentLoopDecision":
            rows.append(payload)
        agent_loop_decision = payload.get("agent_loop_decision")
        if isinstance(agent_loop_decision, Mapping):
            rows.append(agent_loop_decision)
        for key in (
            "agent_loop_decisions",
            "control_decisions",
            "controller_decisions",
        ):
            value = payload.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    if isinstance(item, Mapping):
                        rows.append(item)
        orchestration = payload.get("orchestration")
        if isinstance(orchestration, Mapping):
            _append_control_decisions(orchestration, rows)
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for item in payload:
            _append_control_decisions(item, rows)


def _decision_source(
    decision: Mapping[str, object],
    *,
    source: str,
    index: int,
) -> str:
    snapshot = _text(decision.get("source_snapshot_id"))
    event = _text(decision.get("source_latest_event_id"))
    if snapshot:
        return snapshot
    if event:
        return event
    return f"{source}:{index}"


def _bool(value: object) -> bool | None:
    if value is None:
        return None
    return coerce_bool(value)


def _text(value: object) -> str:
    return coerce_string(value).strip()


def _normalized(value: object) -> str:
    return _text(value).lower().replace("-", "_").replace(" ", "_")


def _mutation_next_action(value: str) -> bool:
    """Return True when a typed next-action identifier names a mutation.

    v4.42 (rev_pkt_4714 Finding 2 — part 1): delegates to the typed-action
    adapter ``runtime/typed_action_mutation.py`` so the mutation registry
    stays in one place. The ``blocked`` short-circuit is preserved as a
    fast-path negative.
    """
    normalized = _normalized(value)
    if not normalized or "blocked" in normalized:
        return False
    from .typed_action_mutation import typed_action_is_mutation  # noqa: PLC0415
    return typed_action_is_mutation(normalized)


def _mutation_next_command(command: object) -> bool:
    """Return True when a free-text next-command names a mutation.

    v4.42 (rev_pkt_4714 Finding 2 — part 2): codex caught the consistency
    guard ignoring destructive ``next_command`` (e.g. ``git clean -fdx``)
    when ``next_action`` is blank. This helper closes that gap by
    classifying the command text via the shared classifier.
    """
    text = coerce_string(command).strip()
    if not text:
        return False
    from .command_envelope_classification import classify_command_mutation  # noqa: PLC0415
    _, risk = classify_command_mutation(text)
    return risk != "none"


def _push_action(value: str) -> bool:
    normalized = _normalized(value)
    return "push" in normalized


def _actionable_next_command(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return False
    inert_prefixes = ("#", "echo ")
    return not normalized.startswith(inert_prefixes)


def _controller_permitted_next_command(
    decision: Mapping[str, object],
    next_command: str,
) -> bool:
    return _status_probe_command(next_command) or _packet_lifecycle_command_matches(
        decision,
        next_command=next_command,
    )


def _status_probe_command(value: str) -> bool:
    normalized = value.strip().lower()
    return "devctl.py agent-loop " in normalized or normalized.endswith("devctl.py agent-loop")


def _packet_lifecycle_command_violations(
    decision: Mapping[str, object],
    *,
    source: str,
    next_command: str,
) -> tuple[ControlDecisionViolation, ...]:
    expected_action, expected_packet_id = _expected_packet_lifecycle(decision)
    if not (expected_action and expected_packet_id):
        return ()
    violations: list[ControlDecisionViolation] = []
    target_kind = _normalized(decision.get("target_kind"))
    target_ref = _text(decision.get("target_ref"))
    if target_kind == "packet" and target_ref and target_ref != expected_packet_id:
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="packet_lifecycle_target_ref_mismatch",
                detail=(
                    f"target_ref={target_ref} expected_packet_id={expected_packet_id}"
                ),
            )
        )
    action = _review_channel_lifecycle_action(next_command)
    if not action:
        return tuple(violations)
    packet_id = _packet_id_from_command(next_command)
    if action != expected_action or packet_id != expected_packet_id:
        violations.append(
            ControlDecisionViolation(
                source=source,
                reason="packet_lifecycle_next_command_mismatch",
                detail=(
                    f"next_command_action={action or '(missing)'};"
                    f"next_command_packet={packet_id or '(missing)'};"
                    f"expected_action={expected_action};"
                    f"expected_packet={expected_packet_id}"
                ),
            )
        )
    return tuple(violations)


def _packet_lifecycle_command_matches(
    decision: Mapping[str, object],
    *,
    next_command: str,
) -> bool:
    expected_action, expected_packet_id = _expected_packet_lifecycle(decision)
    if not (expected_action and expected_packet_id):
        return False
    return (
        _review_channel_lifecycle_action(next_command) == expected_action
        and _packet_id_from_command(next_command) == expected_packet_id
    )


def _expected_packet_lifecycle(decision: Mapping[str, object]) -> tuple[str, str]:
    if _bool(decision.get("absorption_required")):
        return "absorb", _text(decision.get("absorption_packet_id"))
    if _bool(decision.get("semantic_ingestion_required")):
        return "ingest", _text(decision.get("semantic_ingestion_packet_id"))
    if _bool(decision.get("body_open_required")):
        return "show", _text(decision.get("body_open_packet_id"))
    return "", ""


def _review_channel_lifecycle_action(value: str) -> str:
    normalized = value.strip().lower()
    if "review-channel" not in normalized:
        return ""
    for action in ("show", "ingest", "absorb"):
        if f"--action {action}" in normalized:
            return action
    return ""


def _packet_id_from_command(value: str) -> str:
    marker = "--packet-id "
    normalized = value.strip()
    lower = normalized.lower()
    if marker not in lower:
        return ""
    start = lower.index(marker) + len(marker)
    raw = normalized[start:].split(maxsplit=1)[0]
    return raw.strip("'\"")


def _blocker_is_none(value: str) -> bool:
    return value in {"", "none", "no_blocker", "top_blocker_none"}


def _requires_blocker(required_action: str) -> bool:
    if not required_action:
        return False
    return required_action.startswith(("wait", "repair", "checkpoint"))


__all__ = [
    "CONTROL_DECISION_CONSISTENCY_CONTRACT_ID",
    "CONTROL_DECISION_CONSISTENCY_SCHEMA_VERSION",
    "CONTROL_DECISION_VIOLATION_CONTRACT_ID",
    "ControlDecisionConsistencyReport",
    "ControlDecisionViolation",
    "control_decision_violations",
    "evaluate_control_decision_consistency",
    "extract_control_decisions",
]
