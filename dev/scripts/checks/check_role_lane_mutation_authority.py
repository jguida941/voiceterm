#!/usr/bin/env python3
"""Fail when a typed role lane mutates without typed mutation authority."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
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

from dev.scripts.devctl.runtime.command_envelope_classification import (  # noqa: E402
    classify_command_mutation,
)
from dev.scripts.devctl.runtime.control_decision_action_matching import (  # noqa: E402
    action_text,
    allowed_controller_action,
)
from dev.scripts.devctl.runtime.control_decision_obedience import (  # noqa: E402
    extract_decision_and_attempted_actions,
)
from dev.scripts.devctl.runtime.role_profile import (  # noqa: E402
    TandemRole,
    normalize_tandem_role,
)
from dev.scripts.devctl.runtime.typed_action_mutation import (  # noqa: E402
    typed_action_is_mutation,
)
from dev.scripts.devctl.runtime.value_coercion import (  # noqa: E402
    coerce_bool,
    coerce_string,
)


COMMAND = "check_role_lane_mutation_authority"
CONTRACT_ID = "RoleLaneMutationAuthorityGuard"
ROLE_LANE_MUTATION_REASON = "role_lane_mutation_without_authority"
LOOSE_PROVIDER_INSTRUCTION_REASON = (
    "loose_provider_instruction_without_typed_review_channel_state"
)
DISPLAY_TEXT = (
    "AI DUMBASS ALERT: role lane violation. Stay in your typed lane. "
    "Reviewer/orchestrator cannot mutate implementation files without typed "
    "mutation authority."
)
DEFAULT_LIVE_STATE_PATH = REPO_ROOT / "dev/reports/review_channel/state/latest.json"

READ_ONLY_ROLES = frozenset(
    {
        "reviewer",
        "review",
        "orchestrator",
        "plan_steward",
        "plan-steward",
        "architecture_review",
        "duplicate_scope_guard",
        "dogfood_test",
        "governance_receipt",
        "watcher",
        "codex_research",
        "observer",
        "dashboard",
        "operator",
    }
)
IMPLEMENTER_ROLES = frozenset({"implementer", "implementation", "builder", "coder"})
COLLABORATION_HANDOFF_SOURCE_ROLES = frozenset(
    {
        "reviewer",
        "orchestrator",
        "plan_steward",
        "architecture_review",
        "duplicate_scope_guard",
        "dogfood_test",
        "governance_receipt",
        "codex_research",
    }
)
FORBIDDEN_AUTHORITY_SOURCES = frozenset(
    {
        "agent_mind",
        "agent-mind",
        "campaign",
        "chat",
        "controller_output",
        "develop_next",
        "develop next",
        "packet_watch",
        "packet-watch",
        "projection",
        "startup",
    }
)
MUTATION_MODES_WITH_LEASE = frozenset({"live_tree", "isolated_worktree"})
MUTATION_ACTIONS = frozenset(
    {"implementation.edit", "implementation_edit", "edit_files", "run_checks"}
)
MUTATION_CAPABILITIES = frozenset({"repo.stage", "repo.commit", "implementation.edit"})


@dataclass(frozen=True, slots=True)
class RoleLaneViolation:
    reason: str
    detail: str
    actor: str = ""
    role: str = ""
    session_id: str = ""
    severity: str = "blocking"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RoleLaneMutationAuthorityReport:
    ok: bool
    evaluated_action_count: int
    mutating_action_count: int
    violation_count: int
    checked_surfaces: tuple[str, ...]
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    command: str = COMMAND
    timestamp: str = ""
    schema_version: int = 1
    contract_id: str = CONTRACT_ID
    display_text: str = DISPLAY_TEXT

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checked_surfaces"] = list(self.checked_surfaces)
        payload["violations"] = list(self.violations)
        payload["warnings"] = list(self.warnings)
        return payload


def build_report(
    *,
    report_override: Mapping[str, object] | None = None,
    input_path: Path | None = None,
    stdin_text: str = "",
    live_state_path: Path = DEFAULT_LIVE_STATE_PATH,
    mode: str = "pre_mutation",
) -> dict[str, object]:
    payload, checked_surfaces, warnings = _load_payload(
        report_override=report_override,
        input_path=input_path,
        stdin_text=stdin_text,
        live_state_path=live_state_path,
        mode=mode,
    )
    return evaluate_role_lane_mutation_authority(
        payload=payload,
        checked_surfaces=checked_surfaces,
        warnings=warnings,
    ).to_dict()


def evaluate_role_lane_mutation_authority(
    *,
    payload: object,
    checked_surfaces: Iterable[str] = (),
    warnings: Iterable[str] = (),
) -> RoleLaneMutationAuthorityReport:
    contexts = tuple(_contexts_from_payload(payload))
    violations: list[RoleLaneViolation] = []
    mutating_count = 0
    for decision, action in contexts:
        if not _action_is_mutation(decision or {}, action):
            continue
        mutating_count += 1
        violations.extend(_violations_for_mutation(decision, action))
    ok = not violations
    return RoleLaneMutationAuthorityReport(
        ok=ok,
        evaluated_action_count=len(contexts),
        mutating_action_count=mutating_count,
        violation_count=len(violations),
        checked_surfaces=tuple(checked_surfaces),
        violations=tuple(violation.to_dict() for violation in violations),
        warnings=tuple(warnings),
        timestamp=utc_timestamp(),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- evaluated_action_count: {report.get('evaluated_action_count')}")
    lines.append(f"- mutating_action_count: {report.get('mutating_action_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        if violations:
            lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(f"- {violation.get('reason')}: {violation.get('detail', '')}")
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)):
        if warnings:
            lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def _load_payload(
    *,
    report_override: Mapping[str, object] | None,
    input_path: Path | None,
    stdin_text: str,
    live_state_path: Path,
    mode: str,
) -> tuple[object, tuple[str, ...], tuple[str, ...]]:
    if report_override is not None:
        return report_override, ("fixture",), ()
    if input_path is not None:
        return json.loads(input_path.read_text(encoding="utf-8")), (str(input_path),), ()
    if stdin_text.strip():
        return json.loads(stdin_text), ("stdin",), ()
    checked_surfaces: list[str] = [str(live_state_path)]
    warnings: list[str] = []
    if live_state_path.exists():
        payload: object = json.loads(live_state_path.read_text(encoding="utf-8"))
    else:
        payload = {}
        warnings.append("live review-channel state missing")
    if mode == "pre_mutation":
        payload, worktree_warnings = _attach_live_worktree_mutations(payload)
        checked_surfaces.append("git status --porcelain=v1 --untracked-files=all")
        warnings.extend(worktree_warnings)
    return payload, tuple(checked_surfaces), tuple(warnings)


def _contexts_from_payload(
    payload: object,
) -> Iterable[tuple[Mapping[str, object] | None, Mapping[str, object]]]:
    decision, actions = extract_decision_and_attempted_actions(payload)
    for action in actions:
        yield decision, action
    if isinstance(payload, Mapping):
        worktree_decision = decision or _primary_decision_from_payload(payload)
        for action in _worktree_mutation_actions(payload):
            yield worktree_decision, action
        decisions = payload.get("agent_loop_decisions")
        if isinstance(decisions, Sequence) and not isinstance(decisions, (str, bytes)):
            for item in decisions:
                if isinstance(item, Mapping):
                    yield from _contexts_from_decision(item)
        elif _looks_like_decision(payload) and not actions:
            yield from _contexts_from_decision(payload)


def _primary_decision_from_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object] | None:
    for key in ("agent_loop_decision", "control_decision"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    decisions = payload.get("agent_loop_decisions")
    if isinstance(decisions, Sequence) and not isinstance(decisions, (str, bytes)):
        for item in decisions:
            if isinstance(item, Mapping):
                return item
    if _looks_like_decision(payload):
        return payload
    return None


def _attach_live_worktree_mutations(payload: object) -> tuple[object, tuple[str, ...]]:
    warnings: list[str] = []
    try:
        worktree_mutations = _git_worktree_mutations(REPO_ROOT)
    except Exception as exc:  # broad-except: guards report inability to inspect worktree instead of hiding it
        return payload, (f"git worktree mutation inspection failed: {exc}",)
    if not worktree_mutations:
        return payload, ()
    if isinstance(payload, Mapping):
        merged = dict(payload)
    else:
        merged = {"raw_payload": payload}
        warnings.append("live review-channel payload was not a JSON object")
    existing = merged.get("worktree_mutations")
    merged["worktree_mutations"] = list(_mutation_items(existing)) + worktree_mutations
    return merged, tuple(warnings)


def _git_worktree_mutations(repo_root: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    mutations: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line or len(line) < 4:
            continue
        status = line[:2].strip() or "?"
        path = line[3:].strip()
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[-1].strip()
        if not _path_requires_mutation_authority(path):
            continue
        mutations.append({"path": path, "change_status": status, "source": "git_status"})
    return mutations


def _worktree_mutation_actions(
    payload: Mapping[str, object],
) -> Iterable[Mapping[str, object]]:
    for key in ("worktree_mutations", "current_worktree_mutations", "dirty_paths"):
        for item in _mutation_items(payload.get(key)):
            path = coerce_string(item.get("path") or item.get("file") or item.get("name"))
            if not path or not _path_requires_mutation_authority(path):
                continue
            status = coerce_string(
                item.get("change_status") or item.get("status") or item.get("state")
            )
            yield {
                "action_kind": "implementation_edit",
                "command": f"git dirty {status or 'modified'} {path}",
                "path": path,
                "change_status": status,
                "authority_source": item.get("authority_source", "git_worktree"),
                "source_kind": "git_worktree",
                "mutates": True,
                "writes_state": True,
                "executes_command": False,
            }


def _mutation_items(value: object) -> Iterable[Mapping[str, object]]:
    if isinstance(value, Mapping):
        yield value
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                yield item
            else:
                text = coerce_string(item).strip()
                if text:
                    yield {"path": text}


def _path_requires_mutation_authority(path: str) -> bool:
    normalized = path.strip().lstrip("./")
    if not normalized or normalized.startswith(".git/"):
        return False
    return normalized.startswith(
        (
            "dev/",
            "src/",
            "app/",
            "rust/",
            "scripts/",
            "tests/",
            "repo_packs/",
        )
    )


def _contexts_from_decision(
    decision: Mapping[str, object],
) -> Iterable[tuple[Mapping[str, object], Mapping[str, object]]]:
    for command_key in ("next_command", "repair_command", "next_loop_command"):
        command = coerce_string(decision.get(command_key)).strip()
        if not command:
            continue
        yield decision, {
            "action_kind": coerce_string(decision.get("next_action")) or command_key,
            "command": command,
            "actor": coerce_string(decision.get("actor_id")),
            "role": coerce_string(decision.get("actor_role")),
            "session_id": coerce_string(decision.get("session_id")),
            "executes_command": True,
            "source_latest_event_id": coerce_string(
                decision.get("source_latest_event_id")
            ),
            "source_snapshot_id": coerce_string(decision.get("source_snapshot_id")),
        }


def _looks_like_decision(payload: Mapping[str, object]) -> bool:
    return coerce_string(payload.get("contract_id")) == "AgentLoopDecision" or any(
        key in payload
        for key in (
            "actor_id",
            "actor_role",
            "may_mutate",
            "can_run_next_command",
            "operator_override",
        )
    )


def _violations_for_mutation(
    decision: Mapping[str, object] | None,
    action: Mapping[str, object],
) -> list[RoleLaneViolation]:
    decision_payload = decision or {}
    actor = _actor(action, decision_payload)
    role = _role(action, decision_payload)
    session_id = _session_id(action, decision_payload)
    violations: list[RoleLaneViolation] = []
    if _projection_or_chat_authority_claimed(decision_payload, action):
        violations.append(
            _violation(
                "projection_or_chat_authority_not_typed",
                "Projection/chat/controller text cannot authorize role switching or mutation.",
                actor=actor,
                role=role,
                session_id=session_id,
            )
        )
    if _loose_provider_instruction(action):
        violations.append(
            _violation(
                LOOSE_PROVIDER_INSTRUCTION_REASON,
                "Provider instruction is not backed by typed review-channel packet state.",
                actor=actor,
                role=role,
                session_id=session_id,
            )
        )
    if _has_typed_mutation_authority(decision_payload, action):
        return violations
    detail = (
        f"actor={actor or '(missing)'} role={role or '(missing)'} "
        f"session_id={session_id or '(missing)'} action={_action_detail(action)}"
    )
    violations.append(
        _violation(
            ROLE_LANE_MUTATION_REASON,
            detail,
            actor=actor,
            role=role,
            session_id=session_id,
        )
    )
    return violations


def _has_typed_mutation_authority(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    return (
        _typed_packet_lifecycle_control_action(decision, action)
        or _bound_proxy_authorizes(decision, action)
        or _typed_role_switch_authorizes(decision, action)
        or _operator_override_authorizes(decision, action)
        or _typed_mutation_lease_authorizes(decision, action)
        or _implementer_authorizes(decision, action)
    )


def _typed_packet_lifecycle_control_action(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if not _decision_binds_action_actor(decision, action):
        return False
    if not _is_review_channel_packet_lifecycle_action(action):
        return False
    if not allowed_controller_action(action, decision=decision):
        return False
    return bool(coerce_string(decision.get("source_latest_event_id")).strip())


def _is_review_channel_packet_lifecycle_action(
    action: Mapping[str, object],
) -> bool:
    text = action_text(action)
    return (
        "review-channel" in text
        and "--packet-id" in text
        and (
            "--action show" in text
            or "--action ingest" in text
            or "--action absorb" in text
        )
    )


def _typed_mutation_lease_authorizes(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if not _decision_binds_action_actor(decision, action):
        return False
    lease = _first_text(
        decision.get("mutation_lease_id"),
        decision.get("work_scope_lease_id"),
        action.get("mutation_lease_id"),
        action.get("work_scope_lease_id"),
    )
    mutation_mode = _first_text(decision.get("mutation_mode"), action.get("mutation_mode"))
    if not lease or mutation_mode not in MUTATION_MODES_WITH_LEASE:
        return False
    return _action_allowed(decision, action) or coerce_bool(decision.get("may_mutate"))


def _operator_override_authorizes(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if not _decision_binds_action_actor(decision, action):
        return False
    override = decision.get("operator_override")
    if not isinstance(override, Mapping):
        return False
    return (
        coerce_bool(override.get("requested"))
        and coerce_bool(override.get("active"))
        and coerce_string(override.get("state")).strip() == "active"
        and coerce_string(override.get("scope")).strip() == "edit-only"
        and "implementation.edit" in _string_set(override.get("allowed_actions"))
        and bool(coerce_string(override.get("target_ref")).strip())
    )


def _bound_proxy_authorizes(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if not coerce_bool(action.get("proxy_execution")):
        return False
    if not _decision_binds_proxy_executor(decision, action):
        return False
    if not _proxy_subject_is_action_subject(action):
        return False
    proxy_ref = coerce_string(action.get("proxy_authority_ref")).strip()
    return bool(proxy_ref) and proxy_ref in _decision_authority_refs(decision)


def _typed_role_switch_authorizes(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    switch = action.get("typed_role_switch") or decision.get("typed_role_switch")
    if not isinstance(switch, Mapping):
        return False
    if coerce_string(switch.get("contract_id")).strip() not in {
        "RoleSwitch",
        "RoleAssignment",
        "CognitiveRoleFleetAssignment",
    }:
        return False
    if not coerce_bool(switch.get("active")):
        return False
    if _source_is_forbidden(switch.get("authority_source") or switch.get("source")):
        return False
    if not _role_switch_binds_action(decision, action, switch):
        return False
    return _action_allowed(decision, action) or coerce_bool(decision.get("may_mutate"))


def _implementer_authorizes(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if not _decision_binds_action_actor(decision, action):
        return False
    role = _role(action, decision)
    if _normalized_role(role) != "implementer":
        return False
    if not coerce_bool(decision.get("may_mutate")):
        return False
    if not (_action_allowed(decision, action) or _has_mutation_capability(decision, action)):
        return False
    return bool(
        _first_text(
            decision.get("work_scope_lease_id"),
            action.get("work_scope_lease_id"),
            decision.get("mutation_lease_id"),
            action.get("mutation_lease_id"),
        )
    ) or coerce_string(decision.get("mutation_mode")).strip() in MUTATION_MODES_WITH_LEASE


def _action_allowed(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    allowed = _string_set(decision.get("allowed_actions"))
    if not allowed:
        return False
    candidates = {
        _norm_action(action.get("action_kind")),
        _norm_action(action.get("command_name")),
        _norm_action(action.get("next_action")),
    }
    candidates.discard("")
    return bool(candidates & {_norm_action(item) for item in allowed}) or bool(
        MUTATION_ACTIONS & allowed
    )


def _has_mutation_capability(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    capabilities = _string_set(decision.get("granted_capabilities")) | _string_set(
        action.get("granted_capabilities")
    )
    return bool(capabilities & MUTATION_CAPABILITIES)


def _projection_or_chat_authority_claimed(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    for payload in (decision, action):
        for key in (
            "authority_source",
            "authorization_source",
            "role_switch_source",
            "source_kind",
        ):
            if _source_is_forbidden(payload.get(key)):
                return True
    return False


def _loose_provider_instruction(action: Mapping[str, object]) -> bool:
    source = coerce_string(action.get("instruction_source")).strip().lower()
    if not source:
        return False
    target_role = _normalized_role(
        _first_text(action.get("target_role"), action.get("role"), action.get("subject_role"))
    )
    if target_role != "implementer":
        return False
    return not _first_text(
        action.get("packet_id"),
        action.get("review_channel_event_id"),
        action.get("source_latest_event_id"),
        action.get("source_snapshot_id"),
    )


def _action_is_mutation(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if _typed_collaboration_handoff_transport(decision, action):
        return False
    if coerce_bool(action.get("mutates")) or coerce_bool(action.get("writes_state")):
        return True
    for key in ("action_kind", "command_name", "next_action"):
        if typed_action_is_mutation(action.get(key)):
            return True
    _kind, risk = classify_command_mutation(action_text(action))
    return risk != "none"


def _typed_collaboration_handoff_transport(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    if "review-channel.post_action_request" not in _string_set(
        decision.get("allowed_actions")
    ):
        return False
    argv = _action_argv(action)
    if _argv_option_value(argv, "--action") != "post":
        return False
    if _argv_option_value(argv, "--kind") != "action_request":
        return False
    if _argv_option_value(argv, "--requested-action") != "implementer_handoff":
        return False
    if _argv_option_value(argv, "--target-kind") != "plan":
        return False
    if not _argv_option_value(argv, "--target-ref"):
        return False
    if _normalized_role(_argv_option_value(argv, "--target-role")) != "implementer":
        return False
    source_role = _normalized_role(
        _first_text(_argv_option_value(argv, "--actor-role"), _role(action, decision))
    )
    if source_role not in COLLABORATION_HANDOFF_SOURCE_ROLES:
        return False
    return True


def _decision_binds_action_actor(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    decision_actor = coerce_string(decision.get("actor_id")).strip()
    action_actor = _actor(action, decision)
    if decision_actor and action_actor and decision_actor != action_actor:
        return False
    decision_session = coerce_string(decision.get("session_id")).strip()
    action_session = _session_id(action, decision)
    if decision_session and action_session and decision_session != action_session:
        return False
    decision_role = _normalized_role(coerce_string(decision.get("actor_role")).strip())
    action_role = _normalized_role(_role(action, decision))
    if decision_role and action_role and decision_role != action_role:
        return False
    return bool(decision_actor or decision_session or decision_role)


def _decision_binds_proxy_executor(
    decision: Mapping[str, object],
    action: Mapping[str, object],
) -> bool:
    executor = {
        "actor": action.get("executor_actor"),
        "role": action.get("executor_role"),
        "session_id": action.get("executor_session_id"),
    }
    return _decision_binds_action_actor(decision, executor)


def _proxy_subject_is_action_subject(action: Mapping[str, object]) -> bool:
    subject_actor = coerce_string(action.get("subject_actor")).strip()
    subject_role = _normalized_role(coerce_string(action.get("subject_role")).strip())
    subject_session = coerce_string(action.get("subject_session_id")).strip()
    action_actor = coerce_string(action.get("actor")).strip()
    action_role = _normalized_role(coerce_string(action.get("role")).strip())
    action_session = coerce_string(action.get("session_id")).strip()
    if subject_actor and action_actor and subject_actor != action_actor:
        return False
    if subject_role and action_role and subject_role != action_role:
        return False
    if subject_session and action_session and subject_session != action_session:
        return False
    return bool(subject_actor or subject_role or subject_session)


def _role_switch_binds_action(
    decision: Mapping[str, object],
    action: Mapping[str, object],
    switch: Mapping[str, object],
) -> bool:
    switch_actor = coerce_string(switch.get("actor_id")).strip()
    switch_role = _normalized_role(coerce_string(switch.get("actor_role")).strip())
    switch_session = coerce_string(switch.get("session_id")).strip()
    if not (switch_actor or switch_role or switch_session):
        return _decision_binds_action_actor(decision, action)
    action_actor = _actor(action, decision)
    action_role = _normalized_role(_role(action, decision))
    action_session = _session_id(action, decision)
    if switch_actor and action_actor and switch_actor != action_actor:
        return False
    if switch_role and action_role and switch_role != action_role:
        return False
    if switch_session and action_session and switch_session != action_session:
        return False
    return bool(action_actor or action_role or action_session)


def _actor(action: Mapping[str, object], decision: Mapping[str, object]) -> str:
    return _first_text(
        action.get("actor"),
        action.get("subject_actor"),
        decision.get("actor_id"),
        action.get("executor_actor"),
    )


def _role(action: Mapping[str, object], decision: Mapping[str, object]) -> str:
    return _first_text(
        action.get("role"),
        action.get("subject_role"),
        decision.get("actor_role"),
        action.get("executor_role"),
    )


def _session_id(action: Mapping[str, object], decision: Mapping[str, object]) -> str:
    return _first_text(
        action.get("session_id"),
        action.get("subject_session_id"),
        decision.get("session_id"),
        action.get("executor_session_id"),
    )


def _normalized_role(role: str) -> str:
    tandem = normalize_tandem_role(role)
    if tandem == TandemRole.REVIEWER:
        return "reviewer"
    if tandem == TandemRole.IMPLEMENTER:
        return "implementer"
    if tandem == TandemRole.OPERATOR:
        return "operator"
    return coerce_string(role).strip().lower().replace("-", "_").replace(" ", "_")


def _decision_authority_refs(decision: Mapping[str, object]) -> set[str]:
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


def _string_set(value: object) -> set[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {coerce_string(item).strip() for item in value if coerce_string(item).strip()}
    text = coerce_string(value).strip()
    return {text} if text else set()


def _norm_action(value: object) -> str:
    return coerce_string(value).strip().lower().replace("_", ".").replace("-", ".")


def _source_is_forbidden(value: object) -> bool:
    return coerce_string(value).strip().lower() in FORBIDDEN_AUTHORITY_SOURCES


def _first_text(*values: object) -> str:
    for value in values:
        text = coerce_string(value).strip()
        if text:
            return text
    return ""


def _action_detail(action: Mapping[str, object]) -> str:
    return action_text(action) or repr(dict(action))


def _action_argv(action: Mapping[str, object]) -> tuple[str, ...]:
    argv = action.get("argv")
    if isinstance(argv, Sequence) and not isinstance(argv, (str, bytes)):
        return tuple(
            coerce_string(item).strip().lower()
            for item in argv
            if coerce_string(item).strip()
        )
    command = coerce_string(action.get("command")).strip()
    if not command:
        return ()
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return tuple(coerce_string(part).strip().lower() for part in parts if part)


def _argv_option_value(argv: Sequence[str], option: str) -> str:
    normalized_option = option.strip().lower()
    for index, token in enumerate(argv):
        if coerce_string(token).strip().lower() != normalized_option:
            continue
        if index + 1 >= len(argv):
            return ""
        return coerce_string(argv[index + 1]).strip()
    return ""


def _violation(
    reason: str,
    detail: str,
    *,
    actor: str,
    role: str,
    session_id: str,
) -> RoleLaneViolation:
    return RoleLaneViolation(
        reason=reason,
        detail=detail,
        actor=actor,
        role=role,
        session_id=session_id,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("audit", "pre_mutation"),
        default="pre_mutation",
        help=(
            "audit checks supplied/self-reported actions; pre_mutation also "
            "inspects the live git worktree/index for dirty mutation evidence."
        ),
    )
    parser.add_argument("--input", type=Path, help="JSON report to inspect")
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
            mode=args.mode,
        )
    except Exception as exc:  # broad-except: guard entrypoints emit structured reports instead of traceback fallback=typed runtime error
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
