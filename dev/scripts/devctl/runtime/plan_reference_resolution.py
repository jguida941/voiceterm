"""Shared plan/task reference resolution across runtime and guard surfaces."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from pathlib import Path

from ..platform.planning_ir_plan_content import parse_execution_plan_phases
from .plan_reference_resolution_decision_prompts import (
    contains_untyped_decision_prompt,
)
from .plan_reference_resolution_index import append_bare_mp_id, append_paths
from .plan_registry_projection import plan_index_by_mp
from .project_governance import PlanRegistry

_MP_ID_RE = re.compile(r"\bMP-\d+\b", re.IGNORECASE)
_PHASE_TASK_RE = re.compile(r"\bMP\d+-P\d+(?:-T\d+)?\b", re.IGNORECASE)


def build_plan_reference_index(
    *,
    repo_root: Path | None,
    plan_registry: PlanRegistry | None,
) -> dict[str, tuple[str, ...]]:
    """Return one lookup of typed plan ids/task ids to owning plan docs."""
    mapping: dict[str, list[str]] = {}
    for token, paths in plan_index_by_mp(plan_registry).items():
        append_paths(mapping, _normalize_reference_token(token), paths)

    if repo_root is None or plan_registry is None:
        return {token: tuple(paths) for token, paths in mapping.items()}

    for entry in plan_registry.entries:
        relative_path = str(entry.path or "").strip()
        if not relative_path:
            continue
        plan_path = repo_root / relative_path
        try:
            plan_text = plan_path.read_text(encoding="utf-8")
        except OSError:
            continue
        phases = parse_execution_plan_phases(plan_text)
        for phase in phases:
            if phase.phase_id:
                append_paths(
                    mapping,
                    _normalize_reference_token(phase.phase_id),
                    (relative_path,),
                )
                append_bare_mp_id(
                    mapping,
                    phase.phase_id,
                    relative_path,
                    normalize_token=_normalize_reference_token,
                )
            for task in phase.tasks:
                if task.task_id:
                    append_paths(
                        mapping,
                        _normalize_reference_token(task.task_id),
                        (relative_path,),
                    )
                    append_bare_mp_id(
                        mapping,
                        task.task_id,
                        relative_path,
                        normalize_token=_normalize_reference_token,
                    )
    return {token: tuple(paths) for token, paths in mapping.items()}


def extract_plan_reference_tokens(values: Iterable[object]) -> tuple[str, ...]:
    """Return unique normalized MP/phase/task tokens found in arbitrary text."""
    tokens: list[str] = []
    for value in values:
        text = _flatten_text(value)
        if not text:
            continue
        for pattern in (_MP_ID_RE, _PHASE_TASK_RE):
            for match in pattern.finditer(text):
                token = _normalize_reference_token(match.group(0))
                if token and token not in tokens:
                    tokens.append(token)
    return tuple(tokens)


def unresolved_plan_reference_tokens(
    *,
    repo_root: Path | None,
    plan_registry: PlanRegistry | None,
    values: Iterable[object],
) -> tuple[str, ...]:
    """Return tokens mentioned in text that do not resolve to typed plan authority."""
    index = build_plan_reference_index(repo_root=repo_root, plan_registry=plan_registry)
    unresolved: list[str] = []
    for token in extract_plan_reference_tokens(values):
        if token in index:
            continue
        if token not in unresolved:
            unresolved.append(token)
    return tuple(unresolved)


def unresolved_review_state_plan_reference_tokens(
    *,
    repo_root: Path | None,
    plan_registry: PlanRegistry | None,
    review_state: object | None,
) -> tuple[str, ...]:
    """Return unresolved plan/task references mentioned by the live review state."""
    return unresolved_plan_reference_tokens(
        repo_root=repo_root,
        plan_registry=plan_registry,
        values=review_state_reference_values(review_state),
    )


def review_state_reference_values(review_state: object | None) -> tuple[object, ...]:
    """Return the bounded review-state fields that may carry plan authority."""
    if review_state is None:
        return ()
    review = getattr(review_state, "review", None)
    current_session = getattr(review_state, "current_session", None)
    return (
        getattr(current_session, "last_reviewed_scope", ""),
        getattr(review, "plan_id", ""),
        getattr(current_session, "current_instruction", ""),
        getattr(current_session, "open_findings", ""),
    )


def collect_packet_plan_authority_gaps(
    *,
    repo_root: Path | None,
    plan_registry: PlanRegistry | None,
    packets: Iterable[Mapping[str, object]],
) -> tuple[str, ...]:
    """Return unresolved packet-only plan references and freeform decision prompts."""
    issues: list[str] = []
    for packet in packets:
        packet_id = str(packet.get("packet_id") or "packet").strip() or "packet"
        unresolved = unresolved_plan_reference_tokens(
            repo_root=repo_root,
            plan_registry=plan_registry,
            values=_packet_reference_values(packet),
        )
        if unresolved:
            issues.append(
                f"{packet_id} references unresolved plan/task ids: {', '.join(unresolved)}"
            )
        if contains_untyped_decision_prompt(packet, flatten_text=_flatten_text):
            issues.append(
                f"{packet_id} carries a freeform decision prompt that has not been promoted into typed plan/decision authority"
            )
    return tuple(issues)


def _packet_reference_values(packet: Mapping[str, object]) -> tuple[object, ...]:
    return (
        packet.get("summary"),
        packet.get("body"),
        packet.get("evidence_refs"),
        packet.get("requested_action"),
        packet.get("plan_id"),
        packet.get("target_ref"),
        packet.get("anchor_refs"),
        packet.get("intake_ref"),
    )


def _normalize_reference_token(token: str) -> str:
    return str(token or "").strip().upper()


def _flatten_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


__all__ = [
    "build_plan_reference_index",
    "collect_packet_plan_authority_gaps",
    "extract_plan_reference_tokens",
    "review_state_reference_values",
    "unresolved_plan_reference_tokens",
    "unresolved_review_state_plan_reference_tokens",
]
