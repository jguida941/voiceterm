"""Canonical reducer for startup-blocker authority (top_blocker/next_action).

Before this module, three surfaces re-derived ``top_blocker`` from the
same raw inputs (quality signals, doctor status, session findings):

* ``commands/dashboard_builders._derive_top_blocker`` -- keyed on the
  ``quality["failing"]`` file list (populated by the dashboard-data
  quality renderer).
* ``runtime/control_plane_resolve.resolve_blocker_and_action`` -- keyed
  on ``quality["last_guard_ok"]`` + ``check_details`` from the same push
  report, but used a slightly different fallback ordering.
* ``runtime/control_plane_read_model`` -- consumed the resolved blocker
  dict, but the two producers above meant dashboard and read-model could
  emit different blocker strings for the same tree.

That is the classic authority-drift failure mode called out by Q99: the
load-bearing "what should I do next" field had multiple independent
producers. This module owns the reducer once so every consumer reads the
same typed ``BlockerSnapshot`` via ``StartupContext.blocker``.

The reference pattern is ``runtime/control_topology.py`` -- one
``derive_observed_control_topology`` producer, six consumers, zero
drift. Q99 applies the same shape to top_blocker/next_action.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

from .topology_authority_facts import live_implementer_provider

if TYPE_CHECKING:
    from .review_state_models import ReviewState
    from .startup_push_models import PushDecisionState


class _DictSerializable(Protocol):
    def to_dict(self) -> Mapping[str, Any]: ...


# Provider identity is not startup-repair authority. Known implementer-owned
# startup repairs fall back to the role placeholder until typed collaboration
# names a live `coding_agent` provider.
_IMPLEMENTER_OWNER_ROLE = "implementer"

# Acceptable blocker sources. Ordered by severity so that the first
# source that fires wins when multiple conditions are true at once.
BlockerSource = Literal[
    "startup_authority",
    "quality",
    "doctor",
    "recovery",
    "session",
    "none",
]
IMPORT_INDEX_ATOMICITY_BLOCKER_KIND = "import_index_atomicity"
STARTUP_AUTHORITY_NEXT_ACTION_PREFIX = "checkpoint_blocked_by_startup_authority:"


_STARTUP_AUTHORITY_REPAIR_DIRECTIVES: dict[
    str, tuple[str, str, str, str, str]
] = {
    "import_index_atomicity": (
        _IMPLEMENTER_OWNER_ROLE,
        "dev/state/import_index.jsonl",
        "import_index_atomicity_violation",
        # v4.43.3 (rev_pkt_4718): the prior repair command
        # ``devctl.py check --target import-index-atomicity --format md`` was
        # NOT runnable — ``devctl check`` has no ``--target`` flag.
        # v4.43.4 (rev_pkt_4720): switched to the stable public shim path
        # ``dev/scripts/checks/check_startup_authority_contract.py`` so the
        # AI-facing typed control surface (agent-loop, develop next,
        # generated boot cards, check-router) converges on one public
        # command shape. The shim wraps the same implementation in
        # ``dev/scripts/checks/startup_authority_contract/command.py``.
        "python3 dev/scripts/checks/check_startup_authority_contract.py --format md",
        "",
    ),
    "startup_authority_failed": (
        _IMPLEMENTER_OWNER_ROLE,
        "dev/scripts/devctl/runtime/startup_authority.py",
        "startup_authority_failed",
        (
            "python3 dev/scripts/devctl.py session --role observer "
            "--include-review-status always --format json"
        ),
        "",
    ),
    "checkpoint_required": (
        _IMPLEMENTER_OWNER_ROLE,
        "dev/scripts/devctl/runtime/agent_loop_decision_builder.py",
        "checkpoint_required",
        (
            "python3 dev/scripts/devctl.py develop next --actor agent "
            "--enforce-final-response-gate --format json"
        ),
        "",
    ),
}


_DEFAULT_STARTUP_AUTHORITY_REPAIR: tuple[str, str, str, str, str] = (
    "operator",
    "dev/scripts/devctl/runtime/startup_blocker_decision.py",
    "startup_authority_kind_unknown",
    "",
    "stop_anchor:startup_authority:operator_review_required",
)


def _resolve_startup_authority_repair(
    startup_kind: str,
    *,
    collaboration: Mapping[str, object] | None = None,
) -> tuple[str, str, str, str, str]:
    """Return (owner, target, reason, repair_command, stop_anchor) for a startup kind.

    Phase 0.6.A v4.17 (rev_pkt_4672): live startup-authority blockers must carry
    an actionable typed repair. Known kinds get a runnable command; unknown
    kinds escalate to a stop_anchor so the agent does not loop on an unmappable
    blocker. Exactly one of ``repair_command`` or ``stop_anchor`` is non-empty.

    v4.55 continuation (rev_pkt_4788): when typed `collaboration` is
    supplied AND the resolved directive's owner is the implementer role
    placeholder, the typed ``live_implementer_provider`` overrides it.
    Without typed collaboration, the owner remains a role, not a provider.
    """
    owner, target, reason, repair_command, stop_anchor = (
        _STARTUP_AUTHORITY_REPAIR_DIRECTIVES.get(
            startup_kind, _DEFAULT_STARTUP_AUTHORITY_REPAIR
        )
    )
    if owner == _IMPLEMENTER_OWNER_ROLE and collaboration is not None:
        typed_owner = live_implementer_provider(collaboration)
        if typed_owner:
            owner = typed_owner
    return (owner, target, reason, repair_command, stop_anchor)


@dataclass(frozen=True, slots=True)
class BlockerSnapshot:
    """Typed startup-blocker authority shared across every surface.

    ``top_blocker`` and ``next_action`` are the load-bearing strings that
    drive "what should I do next" on the dashboard, startup receipt,
    control-plane read model, and operator console. ``blocker_source``
    names the rule that fired so the reducer's trace is auditable, and
    ``derivation_evidence`` lists the observed facts that justified the
    choice.

    Phase 0.6.A v4.17 (rev_pkt_4672) adds five typed action fields so
    startup_authority_failed / repair_startup_authority / final-response
    blockers carry enough context for an agent to act, not just observe:

    - ``blocker_owner``: who is responsible for resolving the blocker
      (``operator``, ``claude``, ``codex``, ``system``).
    - ``blocker_target``: the slice/path/runtime the blocker scopes
      (e.g. ``MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1``).
    - ``blocker_reason``: typed short-form reason code/text.
    - ``repair_command``: runnable shell command an agent can execute, OR
    - ``stop_anchor``: typed anchor reference that formally pauses the goal.

    Exactly one of ``repair_command`` or ``stop_anchor`` SHOULD be non-empty
    for live-agent blockers; both empty is allowed when the blocker_source
    is ``none`` (no actionable repair needed). Self-referential read-only
    agent-loop commands MUST NOT be the only ``repair_command`` value
    returned twice in a row without a changed blocker, command, or stop_anchor
    (loop-detection enforced by the consumer).

    Phase 0.6.A v4.18 (rev_pkt_4674) adds ``repair_command_runnable`` so
    callers can distinguish between commands that are safe to auto-execute
    and commands that are informational only (e.g. they would fail
    ``ControlDecisionObeyedGuard`` because they mutate state without the
    necessary controller-decision context):

    - ``repair_command_runnable=True`` (default): the command is expected to
      pass its guard when run by the named ``blocker_owner``. Read-only
      commands (session, status, inbox, show, develop next, check) are
      always runnable; write commands (review-channel post / ingest / ack,
      vcs.commit, vcs.push) MUST carry obedience-pass context or be marked
      unrunnable.
    - ``repair_command_runnable=False``: the command is informational
      ``see also`` guidance, NOT a literal directive to execute. ``blocker_owner``
      + ``blocker_target`` identify the typed plan row / human action that
      must occur instead. The agent loop MUST NOT auto-execute these.
    """

    schema_version: int = 1
    contract_id: str = "BlockerSnapshot"
    top_blocker: str = "none"
    next_action: str = ""
    blocker_source: BlockerSource = "none"
    derivation_evidence: tuple[str, ...] = field(default_factory=tuple)
    blocker_owner: str = ""
    blocker_target: str = ""
    blocker_reason: str = ""
    repair_command: str = ""
    stop_anchor: str = ""
    repair_command_runnable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "top_blocker": self.top_blocker,
            "next_action": self.next_action,
            "blocker_source": self.blocker_source,
            "derivation_evidence": list(self.derivation_evidence),
            "blocker_owner": self.blocker_owner,
            "blocker_target": self.blocker_target,
            "blocker_reason": self.blocker_reason,
            "repair_command": self.repair_command,
            "stop_anchor": self.stop_anchor,
            "repair_command_runnable": self.repair_command_runnable,
        }


def _first_line_clip(value: str, limit: int = 60) -> str:
    """Shape a free-form blocker string into a single bounded line."""
    first_line = value.strip().splitlines()[0].lstrip("- ").strip()
    if len(first_line) > limit:
        return first_line[:limit] + "..."
    return first_line


_PENDING_REVIEW_PACKET_RE = re.compile(
    r"^(?P<count>\d+)\s+pending review packet\(s\)$",
    re.IGNORECASE,
)


def _normalize_pending_review_packet_blocker(
    findings: str,
    pending_count: int | None,
) -> str:
    """Prefer the typed pending-packet count over stale prose summaries.

    Some surfaces still project ``session.open_findings`` as a string like
    ``"1 pending review packet(s)"`` while the typed packet queue already
    knows the live total. When both signals refer to pending review packets,
    prefer the typed count so blocker text does not drift across dashboard,
    control-plane, and session surfaces.
    """
    if pending_count is None:
        return findings
    stripped = findings.strip()
    if not stripped:
        return findings
    first_line = stripped.splitlines()[0].lstrip("- ").strip()
    if "pending review packet" not in first_line.lower():
        return findings
    match = _PENDING_REVIEW_PACKET_RE.match(first_line)
    if match is None:
        return findings
    if pending_count <= 0:
        return ""
    current_count = int(match.group("count"))
    if current_count == pending_count:
        return findings
    return f"{pending_count} pending review packet(s)"


def startup_authority_blocker_kind(startup_authority: object) -> str:
    """Return the strongest typed startup-authority blocker kind.

    The continuation gate reports structured checkpoint fields, while older
    receipts only carry human-readable startup-authority error strings. Keep
    this classifier centralized so dashboard, control-plane, and startup
    receipts do not each parse those strings differently.
    """
    authority = _mapping(startup_authority)
    if not authority:
        return ""
    governance = _mapping(authority.get("governance"))
    push_enforcement = _mapping(governance.get("push_enforcement"))
    if push_enforcement:
        merged = dict(push_enforcement)
        merged.update(authority)
        authority = merged
    errors = _string_items(authority.get("errors")) or _string_items(
        authority.get("startup_authority_errors")
    )
    if (
        _int_value(authority.get("import_index_atomicity_violations")) > 0
        or _has_import_index_atomicity_finding_records(authority)
        or any(_is_import_index_atomicity_error(error) for error in errors)
    ):
        return IMPORT_INDEX_ATOMICITY_BLOCKER_KIND
    if bool(authority.get("checkpoint_required")) or (
        "safe_to_continue_editing" in authority
        and not bool(authority.get("safe_to_continue_editing"))
    ):
        reason = str(
            authority.get("checkpoint_reason")
            or authority.get("push_reason")
            or authority.get("advisory_reason")
            or authority.get("recommended_action")
            or ""
        ).strip()
        return reason or "checkpoint_required"
    if not bool(authority.get("ok", authority.get("startup_authority_ok", True))):
        if errors:
            return "startup_authority_failed"
    return ""


def _mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    try:
        payload = cast(_DictSerializable, value).to_dict()
    except (AttributeError, TypeError, ValueError):
        return {}
    if isinstance(payload, Mapping):
        return cast(Mapping[str, Any], payload)
    return {}


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    items = cast(list[object] | tuple[object, ...], value)
    return tuple(str(item).strip() for item in items if str(item).strip())


def _has_import_index_atomicity_finding_records(authority: Mapping[str, Any]) -> bool:
    records = authority.get("import_index_atomicity_finding_records")
    if not isinstance(records, (list, tuple)):
        return False
    record_items = cast(list[object] | tuple[object, ...], records)
    return any(
        _is_import_index_atomicity_finding_record(record)
        for record in record_items
    )


def _is_import_index_atomicity_finding_record(record: object) -> bool:
    payload = _mapping(record)
    if not payload:
        return False
    contract_id = str(payload.get("contract_id") or "").strip()
    finding_kind = str(payload.get("finding_kind") or "").strip()
    return contract_id == "ImportIndexAtomicityFinding" or (
        finding_kind == "import_index_atomicity_missing_module"
    )


def _int_value(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if not isinstance(value, (int, float, str, bytes, bytearray)):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_import_index_atomicity_error(error: str) -> bool:
    lowered = error.lower()
    return (
        "import_index_atomicity" in lowered
        or "import-index atomicity" in lowered
        or "missing from git index" in lowered
    )


def derive_blocker_decision(
    *,
    quality: dict[str, Any] | None,
    doctor: dict[str, Any] | None,
    session: dict[str, Any] | None,
    push_action: str = "",
    pending_count: int | None = None,
    startup_authority: object = None,
    collaboration: Mapping[str, object] | None = None,
) -> BlockerSnapshot:
    """Canonical reducer for top_blocker + next_action.

    Priority order (highest severity wins, preserving the semantics of
    the legacy ``dashboard_builders._derive_top_blocker`` and
    ``control_plane_resolve._derive_top_blocker`` functions this replaces):

    1. **Quality failure** -- ``quality["last_guard_ok"]`` is False or
       ``quality["failing"]`` has entries. Emits a guard/failing-file
       blocker string. ``blocker_source="quality"``.
    2. **Doctor blocked** -- ``doctor["blocked_reason"]`` is set to a
       real cause (not the sentinel ``pipeline_unavailable``).
       ``blocker_source="doctor"``.
    3. **Session findings** -- ``session["open_findings"]`` has a
       non-empty, non-"none" value. The first bullet becomes the
       blocker string. ``blocker_source="session"``.
    When ``pending_count`` is supplied and the session blocker prose is a
    pending-review-packet summary, the reducer normalizes that prose to the
    typed count before clipping it. This keeps stale packet prose from
    outranking the live typed queue.

    4. **Default** -- no blocker detected. ``blocker_source="none"``.

    ``next_action`` mirrors ``push_action`` from the governed push
    decision. Callers that only need the blocker field may omit it and
    the snapshot falls back to an empty string, which the downstream
    read-model treats as "n/a".
    """
    quality = quality or {}
    doctor = doctor or {}
    session = session or {}

    evidence: list[str] = []

    startup_kind = startup_authority_blocker_kind(startup_authority)
    if startup_kind:
        evidence.append(f"startup_authority.blocker_kind={startup_kind}")
        owner, target, reason, repair_command, stop_anchor = (
            _resolve_startup_authority_repair(
                startup_kind,
                collaboration=collaboration,
            )
        )
        return BlockerSnapshot(
            top_blocker=f"startup authority: {startup_kind}",
            next_action=f"{STARTUP_AUTHORITY_NEXT_ACTION_PREFIX}{startup_kind}",
            blocker_source="startup_authority",
            derivation_evidence=tuple(evidence),
            blocker_owner=owner,
            blocker_target=target,
            blocker_reason=reason,
            repair_command=repair_command,
            stop_anchor=stop_anchor,
        )

    failing = quality.get("failing")
    if isinstance(failing, list) and failing:
        failing_items = cast(list[object], failing)
        first = str(failing_items[0]).strip()
        evidence.append(f"quality.failing[0]={first}")
        return BlockerSnapshot(
            top_blocker=f"code-shape debt in {first}",
            next_action=push_action,
            blocker_source="quality",
            derivation_evidence=tuple(evidence),
        )

    last_guard_ok = quality.get("last_guard_ok")
    if last_guard_ok is False:
        details = quality.get("check_details")
        if isinstance(details, (list, tuple)) and details:
            detail_items = cast(list[object] | tuple[object, ...], details)
            first_detail = detail_items[0]
            check_name = "unknown"
            if isinstance(first_detail, Mapping):
                first_mapping = cast(Mapping[str, object], first_detail)
                raw = (
                    first_mapping.get("check")
                    or first_mapping.get("step_name")
                    or "unknown"
                )
                check_name = str(raw).strip() or "unknown"
            evidence.append(f"quality.last_guard_ok=False;check={check_name}")
            return BlockerSnapshot(
                top_blocker=f"guard fail: {check_name}",
                next_action=push_action,
                blocker_source="quality",
                derivation_evidence=tuple(evidence),
            )
        evidence.append("quality.last_guard_ok=False;no details")
        return BlockerSnapshot(
            top_blocker="code-shape debt",
            next_action=push_action,
            blocker_source="quality",
            derivation_evidence=tuple(evidence),
        )

    blocked = str(doctor.get("blocked_reason") or "").strip()
    if blocked and blocked != "pipeline_unavailable":
        evidence.append(f"doctor.blocked_reason={blocked}")
        return BlockerSnapshot(
            top_blocker=blocked,
            next_action=push_action,
            blocker_source="doctor",
            derivation_evidence=tuple(evidence),
        )

    findings = str(session.get("open_findings") or "").strip()
    findings = _normalize_pending_review_packet_blocker(findings, pending_count)
    if findings and findings.lower() != "none":
        clipped = _first_line_clip(findings)
        evidence.append("session.open_findings[0]")
        return BlockerSnapshot(
            top_blocker=clipped,
            next_action=push_action,
            blocker_source="session",
            derivation_evidence=tuple(evidence),
        )

    return BlockerSnapshot(
        top_blocker="none",
        next_action=push_action,
        blocker_source="none",
        derivation_evidence=("no_blocker_detected",),
    )


def derive_startup_blocker(
    *,
    review_state: "ReviewState | None",
    push_decision: "PushDecisionState",
) -> BlockerSnapshot:
    """Thread the canonical reducer with startup-context inputs.

    ``build_startup_context`` does not load the push report, so ``quality``
    data (``failing`` / ``last_guard_ok``) is unavailable at that layer.
    The reducer falls through to doctor/session signals automatically
    when quality is absent, so the packet still renders a typed blocker
    for dashboards, session-resume, and the control-plane read model.
    """
    session: dict[str, Any] = {}
    doctor: dict[str, Any] = {}
    if review_state is not None:
        rs_payload = _mapping(review_state.to_dict())
        session = dict(_mapping(rs_payload.get("current_session")))
        reviewer_runtime = _mapping(rs_payload.get("reviewer_runtime"))
        doctor_value = reviewer_runtime.get("doctor", {})
        if isinstance(doctor_value, Mapping):
            doctor = dict(cast(Mapping[str, Any], doctor_value))
    return derive_blocker_decision(
        quality=None,
        doctor=doctor,
        session=session,
        push_action=push_decision.action,
    )


def detect_self_referential_loop(
    snapshot: BlockerSnapshot,
    previous_snapshot: BlockerSnapshot | None,
) -> bool:
    """True when the new snapshot would self-reference the prior one.

    Phase 0.6.A v4.17 (rev_pkt_4672): the agent-loop cannot return the same
    self-referential read-only ``repair_command`` twice in a row without a
    changed blocker, command, or ``stop_anchor``. A loop is detected when:

      - The previous snapshot exists and named a non-empty ``repair_command``,
      - The new snapshot has the same ``top_blocker``, ``repair_command``,
        and ``stop_anchor`` as the previous, AND
      - There is no explicit operator override active (handled by the caller
        via :func:`escalate_self_referential_loop_to_stop_anchor` after this
        predicate fires).

    Returns False if either snapshot lacks a ``repair_command`` (the predicate
    only fires for command-based loops; a stop_anchor sequence is already an
    explicit pause, not a self-loop).
    """
    if previous_snapshot is None:
        return False
    if not snapshot.repair_command:
        return False
    if not previous_snapshot.repair_command:
        return False
    if snapshot.repair_command != previous_snapshot.repair_command:
        return False
    if snapshot.top_blocker != previous_snapshot.top_blocker:
        return False
    if snapshot.stop_anchor != previous_snapshot.stop_anchor:
        return False
    return True


def escalate_self_referential_loop_to_stop_anchor(
    snapshot: BlockerSnapshot,
) -> BlockerSnapshot:
    """Convert a self-referential blocker into a typed stop_anchor escalation.

    Called by the agent-loop driver when :func:`detect_self_referential_loop`
    returns True. Preserves blocker context but swaps the unactionable
    ``repair_command`` for a ``stop_anchor`` that names the operator as owner
    of the next step. Adds a typed derivation_evidence line so audits can
    trace why the escalation fired.
    """
    return BlockerSnapshot(
        schema_version=snapshot.schema_version,
        contract_id=snapshot.contract_id,
        top_blocker=snapshot.top_blocker,
        next_action=snapshot.next_action,
        blocker_source=snapshot.blocker_source,
        derivation_evidence=snapshot.derivation_evidence
        + ("loop_detected:same_repair_command_twice",),
        blocker_owner="operator",
        blocker_target=snapshot.blocker_target,
        blocker_reason=(
            f"loop:{snapshot.blocker_reason}"
            if snapshot.blocker_reason
            else "loop:self_referential_repair_command"
        ),
        repair_command="",
        stop_anchor=(
            f"stop_anchor:self_referential_loop:{snapshot.blocker_reason}"
            if snapshot.blocker_reason
            else "stop_anchor:self_referential_loop:operator_override_required"
        ),
    )


__all__ = [
    "BlockerSnapshot",
    "BlockerSource",
    "derive_blocker_decision",
    "derive_startup_blocker",
    "detect_self_referential_loop",
    "escalate_self_referential_loop_to_stop_anchor",
]
