"""Shared helper logic for `devctl loop-packet` packet generation.

Keep this module as the stable compatibility surface while source-discovery
helpers live in a smaller sibling module.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..context_graph.escalation import ContextEscalationPacket
from .packets.loop_packet_context import build_loop_packet_context_packet
from .packets.loop_packet_probe_guidance import load_loop_packet_probe_guidance
from .packets.loop_packet_sources import (
    DEFAULT_SOURCE_CANDIDATES,
    RISK_CONFIDENCE,
    ArtifactSourceRow,
    LoopPacketSourceCommand,
    _build_live_triage_source,
    _choose_source,
    _discover_artifact_sources,
    _freshness_hours,
)


def _truncate_chars(value: str, max_chars: int) -> str:
    trimmed = str(value)
    if max_chars <= 0:
        return ""
    if len(trimmed) <= max_chars:
        return trimmed
    return trimmed[: max_chars - 3] + "..."


def _build_packet_body(
    *,
    source_command: str,
    payload: dict[str, Any],
) -> tuple[str, str, list[str], ContextEscalationPacket | None, list[dict[str, object]]]:
    context_packet = build_loop_packet_context_packet(
        source_command=source_command,
        payload=payload,
    )
    if source_command == "triage-loop":
        unresolved = int(payload.get("unresolved_count") or 0)
        reason = str(payload.get("reason") or "unknown")
        branch = str(payload.get("branch") or "unknown")
        source_run = payload.get("source_run_id")
        context = [
            f"CodeRabbit loop snapshot for branch `{branch}`.",
            f"Reason: `{reason}`.",
            f"Unresolved medium/high findings: `{unresolved}`.",
        ]
        if isinstance(source_run, int) and source_run > 0:
            context.append(f"Source run id: `{source_run}`.")
        risk = "low" if unresolved == 0 else ("high" if unresolved > 8 else "medium")
        actions = []
        probe_guidance = load_loop_packet_probe_guidance(payload)
        if unresolved == 0:
            actions.append("No medium/high backlog remains. Continue with normal CI verification.")
        else:
            actions.append("Review unresolved findings and apply bounded fixes with the same source run correlation.")
            actions.append("Re-run report-only loop and verify unresolved count trends downward.")
        if probe_guidance:
            actions.insert(
                0,
                "Apply the matched probe guidance in the next bounded remediation step before broadening scope.",
            )
        if _guidance_requires_approval(probe_guidance):
            actions.insert(
                0,
                "One or more matched probe decisions require approval before mutation; explain the plan and request approval first.",
            )
        guidance_lines: list[str] = []
        if probe_guidance:
            guidance_lines.extend(["", "Probe guidance for the unresolved slice:"])
            for entry in probe_guidance:
                probe = str(entry.get("probe") or "probe").strip()
                file_path = str(entry.get("file_path") or entry.get("symbol") or "matched file").strip()
                line_value = entry.get("line")
                location = file_path
                if isinstance(line_value, int) and line_value > 0:
                    location = f"{file_path}:{line_value}"
                decision_mode = str(entry.get("decision_mode") or "").strip()
                decision_suffix = (
                    f" [decision_mode={decision_mode}]"
                    if decision_mode and decision_mode != "recommend_only"
                    else ""
                )
                guidance_lines.append(
                    f"- {entry.get('ai_instruction') or ''} ({probe} on {location}){decision_suffix}"
                )
        draft = "\n".join(
            [
                "Loop feedback packet:",
                *context,
                *guidance_lines,
                "",
                "Task: propose the next bounded remediation step with guardrails and verification.",
                "If probe guidance is attached above, treat it as the default repair plan unless you can justify waiving it.",
                (
                    "If any attached guidance shows `decision_mode=approval_required`, "
                    "do not auto-apply that change; explain the proposed repair and request approval first."
                ),
            ]
        )
        if context_packet is not None:
            draft += "\n\n" + context_packet.markdown
        return risk, draft, actions, context_packet, probe_guidance
    if source_command == "mutation-loop":
        score = payload.get("last_score")
        threshold = payload.get("threshold")
        reason = str(payload.get("reason") or "unknown")
        branch = str(payload.get("branch") or "unknown")
        score_text = "n/a" if score is None else f"{float(score):.2%}"
        threshold_text = "n/a" if threshold is None else f"{float(threshold):.2%}"
        below_threshold = (
            isinstance(score, int | float) and isinstance(threshold, int | float) and float(score) < float(threshold)
        )
        risk = "high" if below_threshold else "low"
        hotspots = payload.get("last_hotspots") if isinstance(payload.get("last_hotspots"), list) else []
        hotspot_items: list[str] = []
        for row in hotspots[:3]:
            if not isinstance(row, dict):
                continue
            module = str(row.get("module") or row.get("target") or row.get("path") or "unknown")
            missed = row.get("missed")
            if isinstance(missed, int):
                hotspot_items.append(f"{module} (missed={missed})")
            else:
                hotspot_items.append(module)

        actions = []
        if below_threshold:
            actions.append("Prioritize mutation hotspots and add focused tests before enabling fix mode.")
        else:
            actions.append("Mutation score meets threshold. Keep report-only monitoring active.")
        if hotspot_items:
            actions.append("Top hotspots: " + ", ".join(hotspot_items))

        lines = [
            "Loop feedback packet:",
            f"Mutation loop snapshot for branch `{branch}`.",
            f"Reason: `{reason}`.",
            f"Score `{score_text}` vs threshold `{threshold_text}`.",
            "",
            "Task: propose the smallest safe test/code change sequence to improve confidence.",
        ]
        draft = "\n".join(lines)
        if context_packet is not None:
            draft += "\n\n" + context_packet.markdown
        return risk, draft, actions, context_packet, []

    rollup = payload.get("rollup") if isinstance(payload.get("rollup"), dict) else {}
    total = int(rollup.get("total") or 0)
    by_severity = rollup.get("by_severity") if isinstance(rollup.get("by_severity"), dict) else {}
    high = int(by_severity.get("high") or 0)
    medium = int(by_severity.get("medium") or 0)
    if high > 0:
        risk = "high"
    elif medium > 0:
        risk = "medium"
    else:
        risk = "low"
    next_actions = payload.get("next_actions")
    actions = [str(row).strip() for row in next_actions] if isinstance(next_actions, list) else []
    actions = [row for row in actions if row]
    if not actions:
        actions = ["No explicit next actions found; review triage snapshot and owners."]
    lines = [
        "Loop feedback packet:",
        "Triage snapshot from local control-plane signals.",
        f"Issue rollup: total={total}, high={high}, medium={medium}.",
        "",
        "Task: convert this triage snapshot into an ordered, guarded execution plan.",
    ]
    draft = "\n".join(lines)
    if context_packet is not None:
        draft += "\n\n" + context_packet.markdown
    return risk, draft, actions, context_packet, []


def _guidance_decision_modes(probe_guidance: list[dict[str, object]]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for entry in probe_guidance:
        mode = str(entry.get("decision_mode") or "recommend_only").strip() or "recommend_only"
        if mode in seen:
            continue
        seen.add(mode)
        ordered.append(mode)
    return tuple(ordered)


def _guidance_requires_approval(probe_guidance: list[dict[str, object]]) -> bool:
    return "approval_required" in _guidance_decision_modes(probe_guidance)


def _auto_send_eligible(
    source_command: str,
    payload: dict[str, Any],
    risk: str,
    *,
    probe_guidance: list[dict[str, object]] | None = None,
) -> bool:
    if probe_guidance and _guidance_requires_approval(probe_guidance):
        return False
    if risk != "low":
        return False
    selected_source = LoopPacketSourceCommand.parse(source_command)
    if selected_source is LoopPacketSourceCommand.TRIAGE_LOOP:
        unresolved = int(payload.get("unresolved_count") or 0)
        return unresolved == 0 and str(payload.get("reason") or "") == "resolved"
    if selected_source is LoopPacketSourceCommand.MUTATION_LOOP:
        return str(payload.get("reason") or "") == "threshold_met"
    if selected_source is LoopPacketSourceCommand.TRIAGE:
        rollup = payload.get("rollup") if isinstance(payload.get("rollup"), dict) else {}
        return int(rollup.get("total") or 0) == 0
    return False
