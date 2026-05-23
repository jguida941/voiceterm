#!/usr/bin/env python3
"""A16 G19/G20/G21 guard: active topology liveness for the current PlanRow.

Per delete_after_ingest.md A16, this guard runs *before* a bounded
implementation slice starts. It composes three current-row invariants:

    G19 provider pre-tool hook coverage
    G20 active topology liveness (mutation_owner, implementer lane present)
    G21 reviewer-coding-route (reviewer must hand off to implementer)

The guard fails closed when any of the following are true:

- a reviewer/orchestrator actor attempts implementation mutation while the
  current-row implementer handoff is missing or unconsumed
- mutation_owner names a different actor than the one attempting mutation
- no implementer lane is bound to the current row
- an active provider lane has no proven pre-tool hook (hook_missing) or only a
  configured-but-untested hook (hook_configured)

Machine reasons are stable across releases so router/policy/CI tools can match
on them directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.value_coercion import (  # noqa: E402
    coerce_bool,
    coerce_string,
)


COMMAND = "check_active_topology_liveness"
CONTRACT_ID = "ActiveTopologyLivenessGuard"

ACTIVE_TOPOLOGY_NOT_LIVE_REASON = "active_topology_not_live"
IMPLEMENTER_LANE_IDLE_REASON = "implementer_lane_idle_or_missing"
MUTATION_OWNER_MISMATCH_REASON = "mutation_owner_mismatch"
PROVIDER_HOOK_MISSING_REASON = "provider_pre_tool_hook_missing"
PROVIDER_HOOK_UNPROVEN_REASON = "provider_pre_tool_hook_unproven"
REVIEWER_CODING_WITHOUT_HANDOFF_REASON = (
    "reviewer_coding_instead_of_implementer_handoff"
)
TYPED_HANDOFF_MISSING_REASON = "typed_collaboration_handoff_missing"

# A17 G23/G24/G25 reasons (extending A16 topology liveness invariants).
PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON = (
    "packet_body_observation_route_missing"
)
REVIEWER_SPOOFED_BODY_OPEN_REASON = "reviewer_spoofs_implementer_body_open"
EXPIRED_SELECTED_ACTION_REQUEST_REASON = "expired_selected_action_request"
CHAT_VISIBILITY_WITHOUT_TYPED_PATH_REASON = (
    "chat_visibility_without_typed_lifecycle_path"
)

# Per rev_pkt_4813 review finding: live sync-status / agent_work_board /
# reviewer_runtime projections name a "canonical active" packet that does NOT
# carry same_row_blocker classification for the current row. The renderers
# that build those projections do not consult typed plan_packet_routing,
# producing multi-projection disagreement. This guard detects the disagreement
# and emits a typed blocker; aligning the source projections belongs to a
# different owner row.
PROJECTION_DISAGREES_WITH_ROUTING_REASON = "projection_disagrees_with_plan_routing"

# Per rev_pkt_4815 / A16 G20: reviewer_mode collapsed to any of these states
# during an implementation slice must emit a typed blocker unless an
# accompanying typed blocker explains the collapse.
COLLAPSED_REVIEWER_MODE_REASON = "collapsed_reviewer_mode_for_implementation_slice"
COLLAPSED_REVIEWER_MODES = frozenset(
    {
        "single_agent",
        "reviewer_only",
        "tools_only",
        "observer_dashboard_lane_read_only",
    }
)

# A17 G26 (per plan-ingest-60ad4bbc16dc3569): a reviewer session with valid
# control-decision input that attempts review_accepted / review_failed and is
# blocked by body_open_required from a prior unconsumed implementer packet
# must surface a typed route blocker — NOT be silently rejected, and NOT be
# read as permission for the reviewer to take the implementer lane.
REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON = "reviewer_route_lifecycle_blocked"
REVIEWER_RESULT_PACKET_KINDS = frozenset(
    {"review_accepted", "review_failed", "review_started"}
)
BODY_OPEN_BLOCKING_REASONS = frozenset(
    {
        "body_open_required",
        "non_body_open_action_after_body_open_required",
        "packet_body_open_required",
    }
)

# A17 G29 (per codex packet rev_pkt_4822 + plan amendment): when an
# implementer AgentLoopDecision has a packet-attention reason_code
# (body_open_required / semantic_ingestion_required) AND a concrete
# next_command targeting a sanctioned review-channel command for the
# same actor/session, the decision must expose a non-empty allowed action
# for that command. Empty allowed_actions + concrete next_command is a
# bootstrap contradiction the controller must not ship silently.
PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON = (
    "packet_attention_bootstrap_lane_missing"
)
PACKET_ATTENTION_REASON_CODES = frozenset(
    {
        "packet_body_open_required",
        "packet_semantic_ingestion_required",
        "packet_absorption_required",
        "packet_ack_required",
    }
)
PACKET_ATTENTION_COMMAND_PATTERNS = (
    ("review-channel", "--action", "show"),
    ("review-channel", "--action", "ingest"),
    ("review-channel", "--action", "absorb"),
    ("review-channel", "--action", "ack"),
    ("review-channel", "--action", "implementer-ack"),
)

DISPLAY_TEXT = (
    "Active topology is not live for the current PlanRow. The reviewer lane "
    "cannot perform implementation mutation while the implementer lane is "
    "idle, mutation_owner is mismatched, the current-row implementer handoff "
    "is unconsumed, or pre-tool hook coverage is unproven."
)

# Lifecycle states that disqualify a packet from being the active handoff.
# Per rev_pkt_4810 review finding. Note: ``applied`` / ``completed`` are NOT
# excluded — those are the *consumed* end-states where body_observed+acked
# downstream logic correctly returns ok=true. Only archive/expire/dismiss
# terminal markers are exclusionary.
INACTIVE_HANDOFF_STATUSES = frozenset({"archived", "expired", "dismissed"})
INACTIVE_HANDOFF_LIFECYCLE_STATES = frozenset({"archived", "expired"})
INACTIVE_HANDOFF_DISPOSITION_SINKS = frozenset({"archived", "dismissed"})

DEFAULT_LIVE_STATE_PATH = REPO_ROOT / "dev/reports/review_channel/state/latest.json"

REVIEWER_ROLES = frozenset(
    {"reviewer", "orchestrator", "plan_steward", "plan-steward"}
)
IMPLEMENTER_ROLES = frozenset({"implementer", "implementation", "builder", "coder"})
PROVEN_HOOK_STATES = frozenset({"hook_tested"})
UNPROVEN_HOOK_STATES = frozenset({"hook_configured"})
MISSING_HOOK_STATES = frozenset({"hook_missing", "hook_unavailable_blocker", ""})


@dataclass(frozen=True, slots=True)
class TopologyViolation:
    reason: str
    detail: str
    actor: str = ""
    role: str = ""
    severity: str = "blocking"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ActiveTopologyLivenessReport:
    ok: bool
    current_plan_row_id: str
    mutation_owner: str
    attempted_actor: str
    attempted_role: str
    implementer_handoff_packet_id: str
    handoff_body_observed: bool
    handoff_acked: bool
    provider_hook_states: dict[str, str]
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    checked_surfaces: tuple[str, ...] = field(default_factory=tuple)
    command: str = COMMAND
    timestamp: str = ""
    schema_version: int = 1
    contract_id: str = CONTRACT_ID
    display_text: str = DISPLAY_TEXT

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["violations"] = list(self.violations)
        payload["warnings"] = list(self.warnings)
        payload["checked_surfaces"] = list(self.checked_surfaces)
        return payload


def build_report(
    *,
    report_override: Mapping[str, object] | None = None,
    input_path: Path | None = None,
    stdin_text: str = "",
    live_state_path: Path = DEFAULT_LIVE_STATE_PATH,
) -> dict[str, object]:
    state, checked_surfaces, warnings = _load_state(
        report_override=report_override,
        input_path=input_path,
        stdin_text=stdin_text,
        live_state_path=live_state_path,
    )
    return evaluate_active_topology_liveness(
        state=state,
        checked_surfaces=checked_surfaces,
        warnings=warnings,
    ).to_dict()


def evaluate_active_topology_liveness(
    *,
    state: Mapping[str, object],
    checked_surfaces: Iterable[str] = (),
    warnings: Iterable[str] = (),
) -> ActiveTopologyLivenessReport:
    checked = tuple(checked_surfaces)
    is_fixture_only = checked == ("fixture",)
    current_row = _derive_current_plan_row_id(state)
    decision = _primary_decision(state)
    attempted = _attempted_action(state)
    attempted_actor = coerce_string(attempted.get("actor")).strip()
    attempted_role_raw = coerce_string(attempted.get("role")).strip().lower()
    attempted_role = attempted_role_raw.replace("-", "_")
    collaboration = _mapping(state.get("collaboration"))
    mutation_owner = coerce_string(collaboration.get("mutation_owner")).strip()

    provider_hook_states = _provider_hook_states(
        state,
        allow_g19_composition=not is_fixture_only,
    )
    handoff = _current_row_implementer_handoff(state, current_row)
    handoff_packet_id = coerce_string(handoff.get("packet_id")).strip()
    handoff_body_observed = bool(coerce_string(handoff.get("body_observed_at_utc")).strip())
    handoff_acked = bool(coerce_string(handoff.get("acked_at_utc")).strip())
    handoff_consumed = handoff_body_observed and handoff_acked

    violations: list[TopologyViolation] = []
    mutation_attempted = _action_is_mutation(attempted)

    # rev_pkt_4808 review finding: typed_collaboration_handoff_missing must fire on
    # pending+unconsumed handoff state regardless of whether a mutation is being
    # attempted right now. Otherwise the bug is invisible until someone tries to edit.
    if current_row:
        violations.extend(
            _handoff_violations(
                attempted_actor=attempted_actor,
                attempted_role=attempted_role,
                handoff=handoff,
                handoff_consumed=handoff_consumed,
            )
        )
    if mutation_attempted:
        violations.extend(
            _mutation_owner_violations(
                attempted_actor=attempted_actor,
                attempted_role=attempted_role,
                mutation_owner=mutation_owner,
            )
        )

    violations.extend(
        _implementer_lane_violations(
            collaboration=collaboration,
            state=state,
        )
    )
    violations.extend(_provider_hook_violations(provider_hook_states))
    now_utc = _resolve_now_utc(state)
    violations.extend(
        _body_observation_route_violations(
            handoff=handoff,
            now_utc=now_utc,
        )
    )
    violations.extend(
        _expired_action_request_violations(
            state=state,
            current_row=current_row,
            now_utc=now_utc,
        )
    )
    violations.extend(
        _chat_visibility_violations(
            state=state,
            handoff=handoff,
            handoff_consumed=handoff_consumed,
        )
    )
    violations.extend(
        _projection_disagreement_violations(
            state=state,
            current_row=current_row,
        )
    )
    violations.extend(
        _collapsed_reviewer_mode_violations(
            collaboration=collaboration,
            handoff=handoff,
            mutation_attempted=mutation_attempted,
        )
    )
    violations.extend(_reviewer_route_lifecycle_violations(state=state))
    violations.extend(_packet_attention_bootstrap_lane_violations(state=state))

    if violations and not any(
        v.reason == ACTIVE_TOPOLOGY_NOT_LIVE_REASON for v in violations
    ):
        violations.append(
            TopologyViolation(
                reason=ACTIVE_TOPOLOGY_NOT_LIVE_REASON,
                detail=(
                    "Active topology is not live for the current PlanRow; see "
                    "earlier violations for the specific gap."
                ),
                actor=attempted_actor,
                role=attempted_role,
            )
        )

    ok = not violations
    return ActiveTopologyLivenessReport(
        ok=ok,
        current_plan_row_id=current_row,
        mutation_owner=mutation_owner,
        attempted_actor=attempted_actor,
        attempted_role=attempted_role,
        implementer_handoff_packet_id=handoff_packet_id,
        handoff_body_observed=handoff_body_observed,
        handoff_acked=handoff_acked,
        provider_hook_states=dict(provider_hook_states),
        violations=tuple(v.to_dict() for v in violations),
        warnings=tuple(warnings),
        checked_surfaces=tuple(checked_surfaces),
        timestamp=utc_timestamp(),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_plan_row_id: {report.get('current_plan_row_id')}")
    lines.append(f"- mutation_owner: {report.get('mutation_owner')}")
    lines.append(f"- attempted_actor: {report.get('attempted_actor')}")
    lines.append(f"- attempted_role: {report.get('attempted_role')}")
    lines.append(
        f"- implementer_handoff_packet_id: {report.get('implementer_handoff_packet_id')}"
    )
    lines.append(f"- handoff_body_observed: {report.get('handoff_body_observed')}")
    lines.append(f"- handoff_acked: {report.get('handoff_acked')}")
    provider_states = report.get("provider_hook_states")
    if isinstance(provider_states, Mapping):
        for provider, state_value in sorted(provider_states.items()):
            lines.append(f"- hook[{provider}]: {state_value}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        if violations:
            lines.extend(("", "## Violations", ""))
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(f"- {violation.get('reason')}: {violation.get('detail', '')}")
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)):
        if warnings:
            lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {w}" for w in warnings)
    return "\n".join(lines)


def _load_state(
    *,
    report_override: Mapping[str, object] | None,
    input_path: Path | None,
    stdin_text: str,
    live_state_path: Path,
) -> tuple[Mapping[str, object], tuple[str, ...], tuple[str, ...]]:
    if report_override is not None:
        return report_override, ("fixture",), ()
    if input_path is not None:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        return _ensure_mapping(payload), (str(input_path),), ()
    if stdin_text.strip():
        payload = json.loads(stdin_text)
        return _ensure_mapping(payload), ("stdin",), ()
    warnings: list[str] = []
    if live_state_path.exists():
        payload = json.loads(live_state_path.read_text(encoding="utf-8"))
    else:
        payload = {}
        warnings.append("live review-channel state missing")
    return _ensure_mapping(payload), (str(live_state_path),), tuple(warnings)


def _ensure_mapping(payload: object) -> Mapping[str, object]:
    return payload if isinstance(payload, Mapping) else {}


def _primary_decision(state: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("agent_loop_decision", "control_decision"):
        value = state.get(key)
        if isinstance(value, Mapping):
            return value
    decisions = state.get("agent_loop_decisions")
    if isinstance(decisions, Sequence) and not isinstance(decisions, (str, bytes)):
        for item in decisions:
            if isinstance(item, Mapping):
                return item
    return {}


def _attempted_action(state: Mapping[str, object]) -> Mapping[str, object]:
    for key in ("attempted_action", "attempted_actions"):
        value = state.get(key)
        if isinstance(value, Mapping):
            return value
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                if isinstance(item, Mapping):
                    return item
    return {}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _action_is_mutation(action: Mapping[str, object]) -> bool:
    if not action:
        return False
    if coerce_bool(action.get("mutates")) or coerce_bool(action.get("writes_state")):
        return True
    action_kind = coerce_string(action.get("action_kind")).strip().lower()
    return action_kind in {"implementation_edit", "implementation.edit", "edit_files"}


def _provider_hook_states(
    state: Mapping[str, object],
    *,
    allow_g19_composition: bool = True,
) -> dict[str, str]:
    """Collect pre_tool_hook_state per provider/agent from the typed projection.

    Supports three sources, in precedence order:
      1. Explicit fixture inline: ``state["g19_provider_hook_states"]`` for
         deterministic test composition without touching live files.
      2. Registry projection: ``state["registry"]["providers"][name]`` or
         ``state["registry"]["agents"]`` carrying ``pre_tool_hook_state``.
      3. Live G19 composition (only when ``allow_g19_composition=True``):
         calls ``check_provider_pre_tool_hook_coverage.derive_provider_hook_state_map``
         to fill blank entries for providers whose projection lacks the field.

    A blank value from sources 1 or 2 maps to ``provider_pre_tool_hook_missing``.
    Source 3 lets the live topology guard see G19's effective derivation
    (``.claude/settings.json``, ``.codex/hooks.json``, etc.) rather than the
    raw projection field — per rev_pkt_4820.
    """
    # Collect base states from the registry projection first.
    registry = _mapping(state.get("registry"))
    states: dict[str, str] = {}
    providers = _mapping(registry.get("providers"))
    for name, payload in providers.items():
        if not isinstance(payload, Mapping):
            continue
        states[str(name)] = coerce_string(payload.get("pre_tool_hook_state")).strip()
    agents = registry.get("agents")
    if isinstance(agents, Sequence) and not isinstance(agents, (str, bytes)):
        for entry in agents:
            if not isinstance(entry, Mapping):
                continue
            name = (
                coerce_string(entry.get("provider")).strip()
                or coerce_string(entry.get("agent_id")).strip()
            )
            if not name or name in states:
                continue
            states[name] = coerce_string(entry.get("pre_tool_hook_state")).strip()

    # Derived states from either an inline fixture or live G19 derivation.
    derived: dict[str, str] = {}
    inline = state.get("g19_provider_hook_states")
    if isinstance(inline, Mapping):
        derived = {
            str(k): coerce_string(v).strip()
            for k, v in inline.items()
        }
    elif allow_g19_composition:
        try:
            try:
                from check_provider_pre_tool_hook_coverage import (  # type: ignore
                    derive_provider_hook_state_map,
                )
            except ModuleNotFoundError:
                from dev.scripts.checks.check_provider_pre_tool_hook_coverage import (
                    derive_provider_hook_state_map,
                )
            derived = derive_provider_hook_state_map()
        except Exception:  # broad-except: composition is best-effort
            derived = {}

    # rev_pkt_4821: merge derived into registry states by precedence — a
    # stronger derived value must override a weaker registry value, not just
    # fill blanks. Empty existing entries always accept derived; non-empty
    # ones are replaced only when the derived score exceeds the registry one.
    if derived:
        precedence = _load_hook_state_precedence()
        for name, derived_state in derived.items():
            if not derived_state:
                continue
            existing = states.get(name, "")
            if not existing:
                states[name] = derived_state
                continue
            existing_score = precedence.get(existing, 0)
            derived_score = precedence.get(derived_state, 0)
            if derived_score > existing_score:
                states[name] = derived_state
    return states


def _load_hook_state_precedence() -> Mapping[str, int]:
    """Import ``HOOK_STATE_PRECEDENCE`` from G19 with a defensive fallback so
    cross-guard composition still works in degraded import contexts.
    """
    try:
        try:
            from check_provider_pre_tool_hook_coverage import (  # type: ignore
                HOOK_STATE_PRECEDENCE,
            )
        except ModuleNotFoundError:
            from dev.scripts.checks.check_provider_pre_tool_hook_coverage import (
                HOOK_STATE_PRECEDENCE,
            )
        return HOOK_STATE_PRECEDENCE
    except Exception:
        return {}


def _derive_current_plan_row_id(state: Mapping[str, object]) -> str:
    """Resolve the current PlanRow id from typed sources.

    Fixture shape stores it at ``state["current_plan_row_id"]``. Live state
    buries it inside ``state["packets"][i]["packet_creation_binding"]
    ["plan_packet_routing"]["current_plan_row_id"]``. Both must work so that
    the same guard fires identically on a test fixture and the real
    review-channel projection.
    """
    explicit = coerce_string(state.get("current_plan_row_id")).strip()
    if explicit:
        return explicit
    decision = _primary_decision(state)
    if coerce_string(decision.get("target_kind")).strip().lower() == "plan":
        target = coerce_string(decision.get("target_ref")).strip()
        if target:
            return target
    for source_key in ("packets", "packet_inbox", "agent_sync_pending_packets"):
        packets = state.get(source_key)
        if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
            continue
        for packet in packets:
            if not isinstance(packet, Mapping):
                continue
            for binding_key in ("packet_creation_binding", "durable_binding"):
                routing = _mapping(_mapping(packet.get(binding_key)).get("plan_packet_routing"))
                row = coerce_string(routing.get("current_plan_row_id")).strip()
                if row:
                    return row
    return ""


def _resolve_now_utc(state: Mapping[str, object]) -> str:
    """Return the timestamp the guard should treat as 'now'.

    Per rev_pkt_4811 reviewer finding, live ``latest.json`` has ``now_utc=None``,
    which made expiry filters short-circuit. The guard owns its own wall clock
    when state does not supply one — deterministic from state when fixtures want
    a frozen clock, live UTC otherwise.
    """
    supplied = coerce_string(state.get("now_utc")).strip()
    if supplied:
        return supplied
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _current_row_implementer_handoff(
    state: Mapping[str, object],
    current_row: str,
) -> Mapping[str, object]:
    """Select the active current-row implementer action_request, if any.

    Per rev_pkt_4810 review finding, this must NOT pick:
      - archived/expired/dismissed packets (lifecycle terminal)
      - packets whose target_session_id names a session different from the
        active implementer session

    Returns the first lifecycle-active packet matching all filters, or {}.
    """
    if not current_row:
        return {}
    now_utc = _resolve_now_utc(state)
    active_implementer_session = _active_implementer_session_id(state)
    for source_key in ("packets", "packet_inbox", "agent_sync_pending_packets"):
        packets = state.get(source_key)
        if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
            continue
        for packet in packets:
            if not isinstance(packet, Mapping):
                continue
            if not _packet_targets_current_row(packet, current_row):
                continue
            if coerce_string(packet.get("kind")).strip().lower() != "action_request":
                continue
            if coerce_string(packet.get("target_role")).strip().lower() not in IMPLEMENTER_ROLES:
                continue
            if not _handoff_lifecycle_active(packet, now_utc=now_utc):
                continue
            if not _handoff_session_matches_active(
                packet,
                active_session=active_implementer_session,
            ):
                continue
            return packet
    return {}


def _handoff_lifecycle_active(
    packet: Mapping[str, object],
    *,
    now_utc: str,
) -> bool:
    """A packet is lifecycle-active iff none of its terminal markers are set
    and its ``expires_at_utc`` (when known) is in the future relative to
    ``now_utc`` (when known).
    """
    status = coerce_string(packet.get("status")).strip().lower()
    if status in INACTIVE_HANDOFF_STATUSES:
        return False
    lifecycle = coerce_string(packet.get("lifecycle_current_state")).strip().lower()
    if lifecycle in INACTIVE_HANDOFF_LIFECYCLE_STATES:
        return False
    disposition = _mapping(packet.get("disposition"))
    sink = coerce_string(disposition.get("sink")).strip().lower()
    if sink in INACTIVE_HANDOFF_DISPOSITION_SINKS:
        return False
    expires = coerce_string(packet.get("expires_at_utc")).strip()
    if expires and now_utc and expires <= now_utc:
        return False
    return True


def _handoff_session_matches_active(
    packet: Mapping[str, object],
    *,
    active_session: str,
) -> bool:
    """If both the active implementer session and the packet's target session
    are known, they must match. Either being unknown is permissive — the
    handoff_lifecycle filter is the primary gate.
    """
    if not active_session:
        return True
    packet_session = coerce_string(packet.get("target_session_id")).strip()
    if not packet_session:
        return True
    return packet_session == active_session


def _active_implementer_session_id(state: Mapping[str, object]) -> str:
    """Find the implementer actor's session_id from agent_loop_decisions."""
    decisions = state.get("agent_loop_decisions")
    iterable: Iterable[object] = ()
    if isinstance(decisions, Sequence) and not isinstance(decisions, (str, bytes)):
        iterable = decisions
    else:
        single = state.get("agent_loop_decision")
        if isinstance(single, Mapping):
            iterable = (single,)
    for item in iterable:
        if not isinstance(item, Mapping):
            continue
        role = coerce_string(item.get("actor_role")).strip().lower()
        if role in IMPLEMENTER_ROLES:
            session = coerce_string(item.get("session_id")).strip()
            if session:
                return session
    return ""


def _packet_targets_current_row(packet: Mapping[str, object], current_row: str) -> bool:
    """A packet 'targets' the current row only via typed plan-packet-routing.

    Per rev_pkt_4808 reviewer finding: matching on ``routing.current_plan_row_id``
    is wrong because that field carries system-state-at-creation, not the packet's
    own target. The correct discriminator is ``routing.target_plan_row_id`` paired
    with ``classification == "same_row_blocker"``. Packets classified as
    ``future_row_note`` or ``stale_unbound_communication`` must NOT be selected
    as current-row handoff even when they were created while this row was active.

    Fixture/test shape with no routing falls back to matching the packet's own
    ``current_plan_row_id`` / ``target_ref`` / ``target_plan_row_id`` strings so
    the simpler test scenarios still work.
    """
    routing = _packet_routing(packet)
    if routing:
        classification = coerce_string(routing.get("classification")).strip().lower()
        target_row = coerce_string(routing.get("target_plan_row_id")).strip()
        return (
            classification == "same_row_blocker"
            and target_row == current_row
        )
    for candidate in (
        packet.get("current_plan_row_id"),
        packet.get("target_ref"),
        packet.get("target_plan_row_id"),
    ):
        text = coerce_string(candidate).strip()
        if text == current_row or text.endswith(f":{current_row}"):
            return True
    return False


def _packet_routing(packet: Mapping[str, object]) -> Mapping[str, object]:
    routing = _mapping(packet.get("plan_packet_routing"))
    if routing:
        return routing
    binding = _mapping(packet.get("packet_creation_binding"))
    return _mapping(binding.get("plan_packet_routing"))


def _handoff_violations(
    *,
    attempted_actor: str,
    attempted_role: str,
    handoff: Mapping[str, object],
    handoff_consumed: bool,
) -> list[TopologyViolation]:
    violations: list[TopologyViolation] = []
    if not handoff:
        violations.append(
            TopologyViolation(
                reason=TYPED_HANDOFF_MISSING_REASON,
                detail=(
                    "No active current-row implementer action_request handoff "
                    "packet found in the live review-channel state."
                ),
                actor=attempted_actor,
                role=attempted_role,
            )
        )
    elif not handoff_consumed:
        violations.append(
            TopologyViolation(
                reason=TYPED_HANDOFF_MISSING_REASON,
                detail=(
                    f"Handoff packet {coerce_string(handoff.get('packet_id'))} "
                    "exists but is not body-observed and acked."
                ),
                actor=attempted_actor,
                role=attempted_role,
            )
        )

    # REVIEWER_CODING_WITHOUT_HANDOFF only fires when there IS an attempted
    # mutation. The unconsumed-handoff signal is already captured above by
    # TYPED_HANDOFF_MISSING_REASON; this reason adds the role-attribution overlay
    # specifically when a reviewer is the one mutating.
    if attempted_actor and attempted_role in REVIEWER_ROLES and not handoff_consumed:
        violations.append(
            TopologyViolation(
                reason=REVIEWER_CODING_WITHOUT_HANDOFF_REASON,
                detail=(
                    "Reviewer/orchestrator attempted implementation mutation "
                    "while no current-row implementer handoff is consumed."
                ),
                actor=attempted_actor,
                role=attempted_role,
            )
        )

    return violations


def _mutation_owner_violations(
    *,
    attempted_actor: str,
    attempted_role: str,
    mutation_owner: str,
) -> list[TopologyViolation]:
    if not mutation_owner or not attempted_actor:
        return []
    if mutation_owner == attempted_actor:
        return []
    if attempted_role in IMPLEMENTER_ROLES and attempted_actor == mutation_owner:
        return []
    return [
        TopologyViolation(
            reason=MUTATION_OWNER_MISMATCH_REASON,
            detail=(
                f"mutation_owner={mutation_owner!r} but attempted_actor="
                f"{attempted_actor!r} with role={attempted_role!r}."
            ),
            actor=attempted_actor,
            role=attempted_role,
        )
    ]


def _implementer_lane_violations(
    *,
    collaboration: Mapping[str, object],
    state: Mapping[str, object],
) -> list[TopologyViolation]:
    mutation_owner = coerce_string(collaboration.get("mutation_owner")).strip()
    if mutation_owner:
        return []
    reviewer_mode = coerce_string(collaboration.get("reviewer_mode")).strip().lower()
    if reviewer_mode in {"active_dual_agent"} and _state_has_implementer_decision(state):
        return []
    return [
        TopologyViolation(
            reason=IMPLEMENTER_LANE_IDLE_REASON,
            detail=(
                f"No implementer lane bound to the current row "
                f"(reviewer_mode={reviewer_mode or 'unknown'!r}, mutation_owner empty)."
            ),
        )
    ]


def _state_has_implementer_decision(state: Mapping[str, object]) -> bool:
    decisions = state.get("agent_loop_decisions")
    iterable: Iterable[object] = ()
    if isinstance(decisions, Sequence) and not isinstance(decisions, (str, bytes)):
        iterable = decisions
    else:
        single = state.get("agent_loop_decision")
        if isinstance(single, Mapping):
            iterable = (single,)
    for item in iterable:
        if not isinstance(item, Mapping):
            continue
        role = coerce_string(item.get("actor_role")).strip().lower()
        if role in IMPLEMENTER_ROLES:
            return True
    return False


def _body_observation_route_violations(
    *,
    handoff: Mapping[str, object],
    now_utc: str,
) -> list[TopologyViolation]:
    """A17 G23: a selected implementer handoff with no typed body-open route fails.

    Distinguishes:
      - body visible in projection only (delivery_emitted but no body_observed)
      - body opened by a non-target actor (reviewer spoof)
    """
    if not handoff:
        return []
    if coerce_string(handoff.get("status")).strip().lower() not in {"pending", "delivery_pending"}:
        return []
    target_role = coerce_string(handoff.get("target_role")).strip().lower()
    target_session = coerce_string(handoff.get("target_session_id")).strip()
    body_observed_by = coerce_string(handoff.get("body_observed_by")).strip()
    body_observed_role = coerce_string(handoff.get("body_observed_role")).strip().lower()
    body_observed_session = coerce_string(handoff.get("body_observed_session_id")).strip()
    body_observed_at = coerce_string(handoff.get("body_observed_at_utc")).strip()
    delivery_emitted = coerce_string(handoff.get("delivery_emitted_at_utc")).strip()
    violations: list[TopologyViolation] = []

    if delivery_emitted and not body_observed_at:
        violations.append(
            TopologyViolation(
                reason=PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON,
                detail=(
                    f"Packet {coerce_string(handoff.get('packet_id'))} was delivery_emitted but "
                    f"body_observed_at_utc remains empty for target_role={target_role!r} "
                    f"target_session_id={target_session!r}."
                ),
                role=target_role,
            )
        )

    if body_observed_at:
        if target_role and body_observed_role and body_observed_role not in IMPLEMENTER_ROLES:
            violations.append(
                TopologyViolation(
                    reason=REVIEWER_SPOOFED_BODY_OPEN_REASON,
                    detail=(
                        f"body_observed_role={body_observed_role!r} is not an implementer role "
                        f"but recorded body-open for target_role={target_role!r}."
                    ),
                    actor=body_observed_by,
                    role=body_observed_role,
                )
            )
        if (
            target_session
            and body_observed_session
            and body_observed_session != target_session
        ):
            violations.append(
                TopologyViolation(
                    reason=REVIEWER_SPOOFED_BODY_OPEN_REASON,
                    detail=(
                        f"body_observed_session_id={body_observed_session!r} does not match "
                        f"target_session_id={target_session!r}."
                    ),
                    actor=body_observed_by,
                    role=body_observed_role,
                )
            )
    return violations


def _expired_action_request_violations(
    *,
    state: Mapping[str, object],
    current_row: str,
    now_utc: str,
) -> list[TopologyViolation]:
    """A17 G24: an expired action_request that is still 'selected' for this row.

    A current-row implementer action_request whose ``expires_at_utc`` is in the
    past must not stay selectable; a typed refresh packet must reference it.
    """
    if not current_row:
        return []
    if not now_utc:
        # _resolve_now_utc guarantees a non-empty value in normal flow, but
        # defensive guard for callers that bypass it.
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    packets = state.get("packets")
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return []
    violations: list[TopologyViolation] = []
    refreshed_packet_ids = _refreshed_packet_ids(packets, current_row)
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if not _packet_targets_current_row(packet, current_row):
            continue
        if coerce_string(packet.get("kind")).strip().lower() != "action_request":
            continue
        if coerce_string(packet.get("target_role")).strip().lower() not in IMPLEMENTER_ROLES:
            continue
        expires = coerce_string(packet.get("expires_at_utc")).strip()
        if not expires or expires > now_utc:
            continue
        body_observed = coerce_string(packet.get("body_observed_at_utc")).strip()
        acked = coerce_string(packet.get("acked_at_utc")).strip()
        if body_observed and acked:
            continue
        packet_id = coerce_string(packet.get("packet_id")).strip()
        if packet_id in refreshed_packet_ids:
            continue
        violations.append(
            TopologyViolation(
                reason=EXPIRED_SELECTED_ACTION_REQUEST_REASON,
                detail=(
                    f"Packet {packet_id!r} expired at {expires} without body-open/ack and "
                    f"no refresh packet referencing it was found for current row {current_row!r}."
                ),
            )
        )
    return violations


def _refreshed_packet_ids(
    packets: Sequence[object],
    current_row: str,
) -> set[str]:
    refreshed: set[str] = set()
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if not _packet_targets_current_row(packet, current_row):
            continue
        for ref in _evidence_refs(packet):
            if ref.startswith("packet:rev_pkt_"):
                refreshed.add(ref.split("packet:", 1)[1])
    return refreshed


def _evidence_refs(packet: Mapping[str, object]) -> list[str]:
    raw = packet.get("evidence_refs")
    refs: list[str] = []
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for item in raw:
            text = coerce_string(item).strip()
            if text:
                refs.append(text)
    return refs


def _chat_visibility_violations(
    *,
    state: Mapping[str, object],
    handoff: Mapping[str, object],
    handoff_consumed: bool,
) -> list[TopologyViolation]:
    """A17 G25: chat visibility cannot become implementation authority.

    If the live state declares ``chat_body_visible_for_handoff=true`` (the
    operator has acknowledged the body was visible to the target session) but
    no typed lifecycle transition is available, emit a typed blocker — the
    reviewer is NOT allowed to take the implementer lane in that gap.
    """
    if handoff_consumed or not handoff:
        return []
    collaboration = _mapping(state.get("collaboration"))
    chat_visible = coerce_bool(collaboration.get("chat_body_visible_for_handoff"))
    if not chat_visible:
        return []
    return [
        TopologyViolation(
            reason=CHAT_VISIBILITY_WITHOUT_TYPED_PATH_REASON,
            detail=(
                "Packet body was visible in chat/projection but no typed lifecycle "
                "transition (body-open + ack) exists for the target session. The "
                "required output is a typed blocker or refreshed packet, NOT reviewer "
                "taking the implementer lane."
            ),
            role=coerce_string(handoff.get("target_role")).strip(),
        )
    ]


def _packet_attention_bootstrap_lane_violations(
    *,
    state: Mapping[str, object],
) -> list[TopologyViolation]:
    """A17 G29: detect AgentLoopDecisions where the controller tells the actor
    to run a packet-attention command (review-channel show/ingest/absorb/ack)
    but ships an empty allowed_actions + None lane.

    Per the G29 spec, the controller must either grant the narrow needed
    action OR emit a typed blocker. This guard provides the typed blocker
    when the reducer hasn't been patched to grant the narrow action.
    """
    decisions = _all_agent_loop_decisions(state)
    violations: list[TopologyViolation] = []
    for decision in decisions:
        reason_code = coerce_string(decision.get("reason_code")).strip().lower()
        if reason_code not in PACKET_ATTENTION_REASON_CODES:
            continue
        next_command = coerce_string(decision.get("next_command")).strip()
        if not next_command:
            next_command = coerce_string(decision.get("next_loop_command")).strip()
        if not _is_packet_attention_command(next_command):
            continue
        allowed = decision.get("allowed_actions") or []
        if isinstance(allowed, Sequence) and not isinstance(allowed, (str, bytes)):
            allowed_count = len(allowed)
        else:
            allowed_count = 0
        if allowed_count > 0:
            continue
        lane_value = decision.get("lane")
        agent_lane_value = decision.get("agent_lane")
        if lane_value not in (None, "", "null") and agent_lane_value not in (None, "", "null"):
            continue
        actor = coerce_string(decision.get("actor_id")).strip()
        role = coerce_string(decision.get("actor_role")).strip()
        session_id = coerce_string(decision.get("session_id")).strip()
        violations.append(
            TopologyViolation(
                reason=PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON,
                detail=(
                    f"AgentLoopDecision for actor={actor!r} role={role!r} "
                    f"session_id={session_id!r} requires {reason_code!r} with "
                    f"concrete next_command {next_command!r}, but lane is "
                    "absent and allowed_actions is empty. The controller must "
                    "either grant the narrow packet-attention action or emit "
                    "an explicit typed blocker — this guard surfaces the gap "
                    "until the reducer is patched."
                ),
                actor=actor,
                role=role,
            )
        )
    return violations


def _all_agent_loop_decisions(state: Mapping[str, object]) -> list[Mapping[str, object]]:
    decisions: list[Mapping[str, object]] = []
    raw = state.get("agent_loop_decisions")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for item in raw:
            if isinstance(item, Mapping):
                decisions.append(item)
    single = state.get("agent_loop_decision")
    if isinstance(single, Mapping):
        decisions.append(single)
    return decisions


def _is_packet_attention_command(command: str) -> bool:
    if not command:
        return False
    normalized = command.lower()
    for pattern in PACKET_ATTENTION_COMMAND_PATTERNS:
        if all(token in normalized for token in pattern):
            return True
    return False


def _reviewer_route_lifecycle_violations(
    *,
    state: Mapping[str, object],
) -> list[TopologyViolation]:
    """A17 G26: detect reviewer review_accepted/review_failed posts that were
    rejected by ``body_open_required`` (or related body-open gate reasons)
    while the reviewer supplied valid control-decision input.

    Each match emits ``reviewer_route_lifecycle_blocked`` so the operator and
    Codex see a typed route blocker (not a silent rejection, and not permission
    for the reviewer to take the implementer lane). Receipts can live in:

    * ``state.attempted_action_receipts[]`` (list, fixture or projection)
    * ``state.queue.last_failed_action_request`` (singleton, live state)
    * ``state.control_decision_obedience.attempted_action_receipt`` (current attempt)
    """
    receipts = _collect_reviewer_route_receipts(state)
    violations: list[TopologyViolation] = []
    for receipt in receipts:
        if not _is_reviewer_result_post_attempt(receipt):
            continue
        rejection = _attempt_rejection_reason(receipt)
        if rejection not in BODY_OPEN_BLOCKING_REASONS:
            continue
        if not _has_control_decision_input(receipt):
            continue
        receipt_id = coerce_string(receipt.get("receipt_id")).strip() or "<unknown>"
        packet_kind = _attempt_packet_kind(receipt) or "review_*"
        actor = coerce_string(receipt.get("actor")).strip()
        role = coerce_string(receipt.get("role")).strip()
        violations.append(
            TopologyViolation(
                reason=REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON,
                detail=(
                    f"Reviewer post of kind {packet_kind!r} via {receipt_id} "
                    f"was rejected as {rejection!r} while a valid "
                    "control-decision input was supplied. Supported next "
                    "transition: clear the prior implementer body-open gate or "
                    "post a typed task_blocked naming the unconsumed packet — "
                    "do NOT let the reviewer take the implementer lane."
                ),
                actor=actor,
                role=role,
            )
        )
    return violations


def _collect_reviewer_route_receipts(
    state: Mapping[str, object],
) -> list[Mapping[str, object]]:
    receipts: list[Mapping[str, object]] = []
    raw_list = state.get("attempted_action_receipts")
    if isinstance(raw_list, Sequence) and not isinstance(raw_list, (str, bytes)):
        for entry in raw_list:
            if isinstance(entry, Mapping):
                receipts.append(entry)
    queue = _mapping(state.get("queue"))
    last_failed = queue.get("last_failed_action_request")
    if isinstance(last_failed, Mapping):
        receipts.append(last_failed)
    obedience = _mapping(state.get("control_decision_obedience"))
    aar = obedience.get("attempted_action_receipt")
    if isinstance(aar, Mapping):
        receipts.append(aar)
    return receipts


def _is_reviewer_result_post_attempt(receipt: Mapping[str, object]) -> bool:
    role = coerce_string(receipt.get("role")).strip().lower()
    if role not in REVIEWER_ROLES:
        return False
    # The packet_kind may be reported in different shapes depending on source.
    packet_kind = _attempt_packet_kind(receipt)
    if packet_kind in REVIEWER_RESULT_PACKET_KINDS:
        return True
    action_kind = coerce_string(receipt.get("action_kind")).strip().lower()
    if action_kind != "review-channel.post":
        return False
    requested_action = coerce_string(receipt.get("requested_action")).strip().lower()
    return requested_action in REVIEWER_RESULT_PACKET_KINDS


def _attempt_packet_kind(receipt: Mapping[str, object]) -> str:
    for key in ("packet_kind", "kind", "requested_kind"):
        value = coerce_string(receipt.get(key)).strip().lower()
        if value:
            return value
    argv = receipt.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        items = list(argv)
        for index, token in enumerate(items):
            if coerce_string(token).strip().lower() == "--kind" and index + 1 < len(items):
                return coerce_string(items[index + 1]).strip().lower()
    command = coerce_string(receipt.get("command")).strip()
    if "--kind" in command:
        tail = command.split("--kind", 1)[1].strip()
        token = tail.split()[0] if tail else ""
        return token.strip().lower()
    return ""


def _attempt_rejection_reason(receipt: Mapping[str, object]) -> str:
    for key in ("rejection_reason", "execution_failed_reason", "required_recovery"):
        value = coerce_string(receipt.get(key)).strip().lower()
        if value:
            return value
    violations = receipt.get("violations") or receipt.get("rejection_reasons")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        for entry in violations:
            if isinstance(entry, Mapping):
                reason = coerce_string(entry.get("reason")).strip().lower()
                if reason:
                    return reason
            else:
                text = coerce_string(entry).strip().lower()
                if text:
                    return text
    return ""


def _has_control_decision_input(receipt: Mapping[str, object]) -> bool:
    for key in (
        "source_decision_id",
        "source_snapshot_id",
        "source_latest_event_id",
        "control_decision_input",
    ):
        if coerce_string(receipt.get(key)).strip():
            return True
    argv = receipt.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        for token in argv:
            text = coerce_string(token).strip().lower()
            if text in {
                "--control-decision-input",
                "--source-decision-id",
                "--source-snapshot-id",
                "--source-latest-event-id",
            }:
                return True
    command = coerce_string(receipt.get("command"))
    return (
        "--control-decision-input" in command
        or "--source-decision-id" in command
        or "--source-snapshot-id" in command
        or "--source-latest-event-id" in command
    )


def _collapsed_reviewer_mode_violations(
    *,
    collaboration: Mapping[str, object],
    handoff: Mapping[str, object],
    mutation_attempted: bool,
) -> list[TopologyViolation]:
    """A16 G20: reviewer_mode collapsed to a non-dual-agent state during an
    implementation slice must emit a typed blocker.

    Implementation slice is in progress when EITHER a current-row implementer
    handoff exists (operator routed work to the implementer lane) OR a
    mutation is being attempted right now. A typed blocker on
    ``collaboration.collapse_blockers[]`` for the named mode silences the
    violation.
    """
    mode = coerce_string(collaboration.get("reviewer_mode")).strip().lower()
    if mode not in COLLAPSED_REVIEWER_MODES:
        return []
    implementation_slice_active = bool(handoff) or mutation_attempted
    if not implementation_slice_active:
        return []
    if _typed_blocker_for_collapse(collaboration, mode):
        return []
    return [
        TopologyViolation(
            reason=COLLAPSED_REVIEWER_MODE_REASON,
            detail=(
                f"reviewer_mode={mode!r} is collapsed for an implementation "
                "slice (handoff exists or mutation attempted) with no typed "
                "blocker on collaboration.collapse_blockers explaining the "
                "collapse."
            ),
        )
    ]


def _typed_blocker_for_collapse(
    collaboration: Mapping[str, object],
    mode: str,
) -> bool:
    """Return True iff a typed blocker entry on ``collaboration.collapse_blockers``
    names the collapsed mode and carries a non-empty ``blocker_ref``.
    """
    blockers = collaboration.get("collapse_blockers")
    if not isinstance(blockers, Sequence) or isinstance(blockers, (str, bytes)):
        return False
    for entry in blockers:
        if not isinstance(entry, Mapping):
            continue
        entry_mode = coerce_string(entry.get("mode")).strip().lower()
        if entry_mode != mode:
            continue
        if coerce_string(entry.get("blocker_ref")).strip():
            return True
    return False


def _projection_disagreement_violations(
    *,
    state: Mapping[str, object],
    current_row: str,
) -> list[TopologyViolation]:
    """Per rev_pkt_4813: detect projections naming a 'canonical active' packet
    whose typed routing does not classify it as ``same_row_blocker`` for the
    current row. Each disagreement is a typed blocker pointing back at the
    source projection path.
    """
    if not current_row:
        return []
    packet_routing_index = _packet_routing_index(state)
    if not packet_routing_index:
        return []
    candidates = _projection_active_packet_candidates(state)
    violations: list[TopologyViolation] = []
    for source_path, packet_id in candidates:
        routing = packet_routing_index.get(packet_id)
        if routing is None:
            continue
        classification = coerce_string(routing.get("classification")).strip().lower()
        target_row = coerce_string(routing.get("target_plan_row_id")).strip()
        if classification == "same_row_blocker" and target_row == current_row:
            continue
        violations.append(
            TopologyViolation(
                reason=PROJECTION_DISAGREES_WITH_ROUTING_REASON,
                detail=(
                    f"Projection {source_path!r} names {packet_id!r} as the "
                    f"active packet, but plan_packet_routing classifies it as "
                    f"{classification!r} targeting {target_row!r} (current row "
                    f"is {current_row!r})."
                ),
            )
        )
    return violations


def _packet_routing_index(state: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    """Build packet_id -> plan_packet_routing index across packet sources."""
    index: dict[str, Mapping[str, object]] = {}
    for source_key in ("packets", "packet_inbox", "agent_sync_pending_packets"):
        packets = state.get(source_key)
        if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
            continue
        for packet in packets:
            if not isinstance(packet, Mapping):
                continue
            packet_id = coerce_string(packet.get("packet_id")).strip()
            if not packet_id or packet_id in index:
                continue
            routing = _packet_routing(packet)
            if routing:
                index[packet_id] = routing
    return index


def _projection_active_packet_candidates(
    state: Mapping[str, object],
) -> list[tuple[str, str]]:
    """Collect (source_path, packet_id) pairs from known 'active packet' projections."""
    pairs: list[tuple[str, str]] = []
    reviewer_runtime = _mapping(state.get("reviewer_runtime"))
    session_posture = _mapping(reviewer_runtime.get("session_posture"))
    actors = session_posture.get("actors")
    if isinstance(actors, Sequence) and not isinstance(actors, (str, bytes)):
        for index, actor in enumerate(actors):
            if not isinstance(actor, Mapping):
                continue
            target = coerce_string(actor.get("current_target")).strip()
            if target.startswith("rev_pkt_"):
                pairs.append(
                    (f"reviewer_runtime.session_posture.actors[{index}].current_target", target)
                )
    work_board = _mapping(state.get("agent_work_board"))
    rows = work_board.get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                continue
            for field_name in ("active_packet_id", "attention_packet_id"):
                value = coerce_string(row.get(field_name)).strip()
                if value.startswith("rev_pkt_"):
                    pairs.append(
                        (f"agent_work_board.rows[{index}].{field_name}", value)
                    )
    return pairs


def _provider_hook_violations(
    provider_hook_states: Mapping[str, str],
) -> list[TopologyViolation]:
    violations: list[TopologyViolation] = []
    for provider, hook_state in sorted(provider_hook_states.items()):
        normalized = hook_state.strip().lower()
        if normalized in PROVEN_HOOK_STATES:
            continue
        if normalized in UNPROVEN_HOOK_STATES:
            violations.append(
                TopologyViolation(
                    reason=PROVIDER_HOOK_UNPROVEN_REASON,
                    detail=(
                        f"Provider {provider!r} has pre_tool_hook_state="
                        f"{hook_state!r} (configured but not tested)."
                    ),
                    actor=provider,
                )
            )
        elif normalized in MISSING_HOOK_STATES:
            violations.append(
                TopologyViolation(
                    reason=PROVIDER_HOOK_MISSING_REASON,
                    detail=(
                        f"Provider {provider!r} has pre_tool_hook_state="
                        f"{hook_state!r}; no mutation-tool interception proven."
                    ),
                    actor=provider,
                )
            )
        else:
            violations.append(
                TopologyViolation(
                    reason=PROVIDER_HOOK_UNPROVEN_REASON,
                    detail=(
                        f"Provider {provider!r} pre_tool_hook_state="
                        f"{hook_state!r} is unknown."
                    ),
                    actor=provider,
                )
            )
    return violations


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON state to inspect")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin.")
    parser.add_argument(
        "--live-state-path",
        type=Path,
        default=DEFAULT_LIVE_STATE_PATH,
        help="Review-channel live state JSON used when no input is supplied.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        stdin_text = sys.stdin.read() if args.stdin else ""
        report = build_report(
            input_path=args.input,
            stdin_text=stdin_text,
            live_state_path=args.live_state_path,
        )
    except Exception as exc:  # broad-except: guards emit typed error reports
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
