"""Bounded AI-assist draft builders for the Operator Console Activity tab."""

from __future__ import annotations

from dataclasses import dataclass

from .activity_reports import build_activity_report
from .models import AgentLaneData, OperatorConsoleSnapshot
from .readability import audience_mode_label


@dataclass(frozen=True)
class AssistDraft:
    """A staged operator-facing draft generated from the current snapshot."""

    mode: str
    title: str
    summary: str
    provenance: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class SummaryDraftTarget:
    """Selectable provider target for staged AI summary prompts."""

    provider_id: str
    label: str
    description: str


SUMMARY_DRAFT_TARGETS: tuple[SummaryDraftTarget, ...] = (
    SummaryDraftTarget("codex", "Codex Draft", "Draft a review-oriented summary prompt for Codex."),
    SummaryDraftTarget("claude", "Claude Draft", "Draft an implementation-oriented summary prompt for Claude."),
)


def available_summary_draft_targets() -> tuple[SummaryDraftTarget, ...]:
    """Return the provider targets available in the Activity tab."""
    return SUMMARY_DRAFT_TARGETS


def build_assist_draft(
    snapshot: OperatorConsoleSnapshot,
    *,
    mode: str,
) -> AssistDraft:
    """Return a bounded Activity-tab AI-assist draft."""
    normalized_mode = mode.strip().lower()
    if normalized_mode == "audit":
        return _build_audit_draft(snapshot)
    if normalized_mode == "help":
        return _build_help_draft(snapshot)
    raise ValueError(f"Unsupported assist draft mode: {mode}")


def build_summary_draft(
    snapshot: OperatorConsoleSnapshot,
    *,
    report_id: str,
    provider_id: str,
    audience_mode: str = "simple",
) -> AssistDraft:
    """Return a provider-targeted AI summary draft for the selected report."""
    report = build_activity_report(
        snapshot,
        report_id=report_id,
        audience_mode=audience_mode,
    )
    provider = _resolve_provider(provider_id)
    provider_focus = {
        "codex": "Focus on blocker clarity, review risk, and the safest next operator action.",
        "claude": "Focus on implementation state, unblock steps, and what the operator should ask the implementer to do next.",
    }[provider.provider_id]

    body = "\n".join(
        [
            f"{provider.label}",
            "=" * len(provider.label),
            "",
            "Staged prompt only. This does not execute Codex or Claude automatically.",
            "",
            f"Selected report: {report.title}",
            f"Report summary: {report.summary}",
            "",
            "Human-readable source report:",
            report.body,
            "",
            "Request:",
            "1. Rewrite this into a short operator-readable summary.",
            "2. Keep the answer grounded only in the visible report and snapshot facts.",
            "3. Call out blockers, confidence, and the single best next step.",
            f"4. {provider_focus}",
        ]
    )
    return AssistDraft(
        mode="summary",
        title=provider.label,
        summary=f"Provider-targeted AI draft for the {report.title.lower()}.",
        provenance=(
            f"Target provider: {provider.label}",
            f"Selected report: {report.title}",
            f"Read mode: {audience_mode_label(audience_mode)}",
            "Staged only; not executed automatically.",
        ),
        body=body,
    )


def _build_audit_draft(snapshot: OperatorConsoleSnapshot) -> AssistDraft:
    status_lines = _status_lines(snapshot)
    request_lines = [
        "Audit the current review-channel state and identify live blockers only.",
        "Call out which lane is stale, noisy, or missing evidence.",
        "Recommend the next safe typed operator action or devctl command.",
        "Keep the response grounded in the listed signals; do not invent extra state.",
    ]
    return AssistDraft(
        mode="audit",
        title="AI Audit Draft",
        summary="Staged audit prompt generated from the current bridge snapshot.",
        provenance=_default_provenance(snapshot),
        body=_render_draft(
            title="AI Audit Draft",
            lead=(
                "Advisory only. Use this prompt with Codex or Claude; real execution "
                "still routes through typed repo-owned commands."
            ),
            status_lines=status_lines,
            request_lines=request_lines,
        ),
    )


def _build_help_draft(snapshot: OperatorConsoleSnapshot) -> AssistDraft:
    status_lines = _status_lines(snapshot)
    request_lines = [
        "Explain what changed, what is blocked, and what the operator should do next.",
        "Draft a concise note I can send back to Codex or Claude.",
        "Prefer typed follow-up actions and explicit repo-visible artifacts over vague advice.",
        "If data is missing, say exactly which artifact or command would clarify it.",
    ]
    return AssistDraft(
        mode="help",
        title="AI Help Draft",
        summary="Staged operator-help prompt generated from the current bridge snapshot.",
        provenance=_default_provenance(snapshot),
        body=_render_draft(
            title="AI Help Draft",
            lead=(
                "Advisory only. This is a staged operator-help prompt derived "
                "from current visible state."
            ),
            status_lines=status_lines,
            request_lines=request_lines,
        ),
    )


def _render_draft(
    *,
    title: str,
    lead: str,
    status_lines: list[str],
    request_lines: list[str],
) -> str:
    lines = [
        title,
        "=" * len(title),
        "",
        lead,
        "",
        "Observed state:",
    ]
    lines.extend(f"- {line}" for line in status_lines)
    lines.extend(["", "Request:", ""])
    lines.extend(
        f"{index}. {line}" for index, line in enumerate(request_lines, start=1)
    )
    return "\n".join(lines)


def _status_lines(snapshot: OperatorConsoleSnapshot) -> list[str]:
    lines = [
        f"Review mode: {snapshot.review_mode or 'markdown-only'}",
        f"Last Codex poll: {snapshot.last_codex_poll or 'unknown'}",
        f"Worktree hash: {snapshot.last_worktree_hash or 'unknown'}",
        f"Pending approvals: {len(snapshot.pending_approvals)}",
    ]

    for lane in (snapshot.codex_lane, snapshot.claude_lane, snapshot.operator_lane):
        if lane is not None:
            lines.append(_lane_summary(lane))

    if snapshot.warnings:
        lines.append(f"Warnings: {' | '.join(snapshot.warnings[:3])}")
    else:
        lines.append("Warnings: none")

    if snapshot.review_state_path:
        lines.append(f"Structured review_state: {snapshot.review_state_path}")
    else:
        lines.append("Structured review_state: unavailable (markdown bridge only)")
    return lines


def _lane_summary(lane: AgentLaneData) -> str:
    bits = [
        f"{lane.provider_name} ({lane.role_label})",
        f"status={lane.status_hint}",
        f"state={lane.state_label}",
    ]
    if lane.risk_label:
        bits.append(f"risk={lane.risk_label}")
    if lane.confidence_label:
        bits.append(f"confidence={lane.confidence_label}")
    preview = _preview_rows(lane.rows)
    if preview:
        bits.append(preview)
    return " | ".join(bits)


def _preview_rows(rows: tuple[tuple[str, str], ...], limit: int = 2) -> str:
    parts: list[str] = []
    for key, value in rows:
        clean = " ".join(value.split())
        if not clean or clean in {"(missing)", "(unknown)"}:
            continue
        parts.append(f"{key}: {clean[:72]}")
        if len(parts) >= limit:
            break
    return " | ".join(parts)


def _default_provenance(snapshot: OperatorConsoleSnapshot) -> tuple[str, ...]:
    source_lines = ["Generated from the current Operator Console snapshot."]
    if snapshot.review_state_path:
        source_lines.append(f"Structured source: {snapshot.review_state_path}")
    else:
        source_lines.append("Structured source unavailable; markdown bridge only.")
    source_lines.append("Advisory only; use typed repo-owned commands for real execution.")
    return tuple(source_lines)


def _resolve_provider(provider_id: str) -> SummaryDraftTarget:
    normalized = provider_id.strip().lower()
    for provider in SUMMARY_DRAFT_TARGETS:
        if provider.provider_id == normalized:
            return provider
    return SUMMARY_DRAFT_TARGETS[0]
