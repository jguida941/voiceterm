"""Plain-English render helpers for SessionPosture consumers."""

from __future__ import annotations

from collections.abc import Mapping


def render_simple_posture_snapshot(
    *,
    title: str,
    next_action: object = "",
    top_blocker: object = "",
    session_posture: object = None,
) -> str:
    """Render a compact operator-facing posture summary."""
    posture = _mapping(session_posture)
    actors = _actor_rows(posture)
    lines = [f"# {title}", ""]
    if next_action:
        lines.append(f"- next: {_text(next_action)}")
    if top_blocker:
        lines.append(f"- blocker: {_text(top_blocker)}")
    lines.append(
        "- mode: "
        f"{_text(posture.get('interaction_mode')) or 'unknown'} / "
        f"{_text(posture.get('reviewer_mode')) or 'unknown'}"
    )
    lines.append("")
    lines.append("## Actors")
    if not actors:
        lines.append("- no live actor posture available")
        return "\n".join(lines)
    for actor in actors:
        live = "live" if bool(actor.get("live")) else _text(actor.get("presence")) or "idle"
        provider = _text(actor.get("provider")) or _text(actor.get("actor_id")) or "actor"
        activity = _text(actor.get("current_activity")) or "waiting"
        target = _text(actor.get("current_target"))
        detail = f" on {target}" if target else ""
        lines.append(f"- {provider}: {live}, {activity}{detail}")
    return "\n".join(lines)


def _actor_rows(posture: Mapping[str, object]) -> list[Mapping[str, object]]:
    rows = posture.get("actors")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()
