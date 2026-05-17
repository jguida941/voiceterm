"""Typed phase/task routing models for startup work-intake."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class PlanRoutingState:
    """Bounded active phase/task route derived from typed plan content."""

    phase_id: str = ""
    phase_title: str = ""
    phase_status: str = ""
    phase_owner_doc: str = ""
    task_id: str = ""
    task_summary: str = ""
    task_status: str = ""
    task_owner_doc: str = ""
    dependencies: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["dependencies"] = list(self.dependencies)
        if not self.phase_id and not self.task_id:
            return {}
        return payload


def plan_routing_markdown_lines(routing: object) -> tuple[str, ...]:
    """Render the bounded typed phase/task route for startup-context."""
    if not isinstance(routing, dict) or not routing:
        return ()
    phase_id = str(routing.get("phase_id") or "").strip()
    task_id = str(routing.get("task_id") or "").strip()
    if not phase_id and not task_id:
        return ()

    lines = []
    if phase_id:
        phase_title = str(routing.get("phase_title") or "").strip()
        phase_status = str(routing.get("phase_status") or "").strip()
        phase_bits = [f"`{phase_id}`"]
        if phase_title:
            phase_bits.append(phase_title)
        if phase_status:
            phase_bits.append(f"status=`{phase_status}`")
        lines.append("- plan_phase: " + " | ".join(phase_bits))
    if task_id:
        task_summary = str(routing.get("task_summary") or "").strip()
        task_status = str(routing.get("task_status") or "").strip()
        task_bits = [f"`{task_id}`"]
        if task_summary:
            task_bits.append(task_summary)
        if task_status:
            task_bits.append(f"status=`{task_status}`")
        lines.append("- plan_task: " + " | ".join(task_bits))

    task_owner_doc = str(routing.get("task_owner_doc") or "").strip()
    if task_owner_doc:
        lines.append(f"- plan_task_owner_doc: `{task_owner_doc}`")
    dependencies = routing.get("dependencies")
    if isinstance(dependencies, list) and dependencies:
        joined = ", ".join(
            f"`{value}`" for value in dependencies[:4] if str(value).strip()
        )
        if joined:
            lines.append(f"- plan_dependencies: {joined}")
    return tuple(lines)


__all__ = ["PlanRoutingState", "plan_routing_markdown_lines"]
