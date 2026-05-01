"""Pure plan-context derivation for packet continuity surfaces."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from .plan_reference_resolution import _flatten_text as _flatten_reference_text

_MP_ID_RE = re.compile(r"\bMP-\d+\b", re.IGNORECASE)
_PHASE_TASK_RE = re.compile(r"\bMP\d+-P\d+(?:-T\d+)?\b", re.IGNORECASE)
_ANCHOR_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class PacketPlanContext:
    """Plan continuity metadata copied onto non-mutating packet posts."""

    plan_id: str = ""
    anchor_refs: tuple[str, ...] = ()
    intake_ref: str = ""
    source: str = ""

    def has_values(self) -> bool:
        return bool(self.plan_id or self.anchor_refs or self.intake_ref)


def packet_plan_context_from_work_intake(
    work_intake: Mapping[str, object],
    *,
    fallback_plan_id: str = "",
) -> PacketPlanContext:
    """Return compact plan context from an existing WorkIntakePacket mapping."""
    active_target = _mapping(work_intake.get("active_target"))
    plan_routing = _mapping(work_intake.get("plan_routing"))
    plan_id = _first_mp_token(
        (
            *tuple(_rows(work_intake.get("scope_hints"))),
            active_target.get("plan_scope"),
            plan_routing.get("task_id"),
            plan_routing.get("phase_id"),
            fallback_plan_id,
        )
    )
    anchor_refs = _dedupe(
        (
            _anchor(active_target.get("anchor_ref")),
            _typed_anchor("checklist", plan_routing.get("task_id")),
            _typed_anchor("checklist", plan_routing.get("phase_id")),
            _typed_anchor("section", plan_id),
        )
    )
    intake_ref = _intake_ref(active_target, plan_id)
    return PacketPlanContext(
        plan_id=plan_id,
        anchor_refs=anchor_refs,
        intake_ref=intake_ref,
        source="work_intake" if active_target or plan_routing else "plan_id_fallback",
    )


def packet_plan_context_from_plan_id(plan_id: object) -> PacketPlanContext:
    """Return a minimal fallback context for a known plan id."""
    resolved_plan_id = _first_mp_token((plan_id,))
    if not resolved_plan_id:
        return PacketPlanContext()
    return PacketPlanContext(
        plan_id=resolved_plan_id,
        anchor_refs=(_typed_anchor("section", resolved_plan_id),),
        intake_ref=f"plan://{resolved_plan_id}",
        source="plan_id_fallback",
    )


def _intake_ref(active_target: Mapping[str, object], plan_id: str) -> str:
    target_id = str(active_target.get("target_id") or "").strip()
    if target_id:
        return "work_intake://" + target_id.replace(":", "/")
    if plan_id:
        return f"plan://{plan_id}"
    return ""


def _first_mp_token(values: tuple[object, ...]) -> str:
    for value in values:
        text = _flatten_reference_text(value)
        for pattern in (_MP_ID_RE, _PHASE_TASK_RE):
            match = pattern.search(text)
            if match:
                return match.group(0).upper()
    return ""


def _typed_anchor(prefix: str, value: object) -> str:
    token = _anchor_token(value)
    return f"{prefix}:{token}" if token else ""


def _anchor(value: object) -> str:
    text = str(value or "").strip()
    if not text or ":" not in text:
        return ""
    prefix, token = text.split(":", 1)
    if prefix and _ANCHOR_TOKEN_RE.fullmatch(token):
        return text
    return ""


def _anchor_token(value: object) -> str:
    text = str(value or "").strip().strip("`")
    if not text:
        return ""
    return text if _ANCHOR_TOKEN_RE.fullmatch(text) else ""


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    rows: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in rows:
            rows.append(text)
    return tuple(rows)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: object) -> list[object]:
    return list(value) if isinstance(value, (list, tuple)) else []


__all__ = [
    "PacketPlanContext",
    "packet_plan_context_from_plan_id",
    "packet_plan_context_from_work_intake",
]
