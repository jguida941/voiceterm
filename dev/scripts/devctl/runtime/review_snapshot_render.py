"""Markdown renderer for ReviewSnapshot — deterministic, GitHub-readable output.

Owns the header, quick-status, identity, and governance-state sections plus
the top-level dispatcher. The delta, quality, architecture, reviewer-hints,
reasoning, and known-gaps sections live in ``review_snapshot_render_sections``
so each file stays under the code-shape soft limit.
"""

from __future__ import annotations

from .review_snapshot_models import ReviewSnapshot
from .review_snapshot_render_sections import (
    render_architecture,
    render_delta,
    render_known_gaps,
    render_quality,
    render_reasoning,
    render_reviewer_hints,
)


def render_review_snapshot_markdown(snapshot: ReviewSnapshot) -> str:
    """Return the full markdown projection of ``snapshot``."""
    lines: list[str] = []
    _render_header(lines, snapshot)
    _render_quick_status(lines, snapshot)
    _render_identity(lines, snapshot)
    _render_governance_state(lines, snapshot)
    render_delta(lines, snapshot)
    render_quality(lines, snapshot)
    render_architecture(lines, snapshot)
    render_reviewer_hints(lines, snapshot)
    render_reasoning(lines, snapshot)
    render_known_gaps(lines, snapshot)
    _render_footer(lines, snapshot)
    return "\n".join(lines) + "\n"


def _render_header(lines: list[str], snapshot: ReviewSnapshot) -> None:
    identity = snapshot.identity
    title = identity.repo_name or "Repository"
    lines.append(f"# {title} — Review Snapshot")
    lines.append("")
    lines.append(
        "> Deterministically generated from typed governance state. "
        "Do not edit by hand — rerun `devctl review-snapshot --write`."
    )
    lines.append("")


def _render_quick_status(lines: list[str], snapshot: ReviewSnapshot) -> None:
    identity = snapshot.identity
    state = snapshot.governance_state
    quality = snapshot.quality
    delta = snapshot.delta
    lines.append("## Quick status")
    lines.append("")
    lines.append(f"- Branch: `{identity.branch or 'n/a'}`")
    lines.append(
        f"- HEAD: `{identity.head_sha_short or 'n/a'}` — {identity.head_subject or ''}"
    )
    lines.append(f"- Tree hash: `{identity.tree_hash[:12] or 'n/a'}`")
    lines.append(f"- Generation stamp: `{identity.generation_stamp or 'n/a'}`")
    lines.append(f"- Generated at (UTC): {identity.generated_at_utc or 'n/a'}")
    lines.append(
        f"- Push decision: `{state.push_action or 'n/a'}` — {state.push_reason or ''}"
    )
    lines.append(
        f"- Reviewer mode: `{state.reviewer_mode or 'n/a'}` "
        f"(interaction: `{state.interaction_mode}`)"
    )
    lines.append(
        f"- Pipeline state: `{state.pipeline_state or 'n/a'}` "
        f"(approval: `{state.pipeline_approval_state or 'n/a'}`)"
    )
    lines.append(
        f"- Delta since last snapshot: "
        f"{delta.commit_count} commits, {delta.files_changed_count} files, "
        f"+{delta.total_insertions}/-{delta.total_deletions}"
    )
    lines.append(
        f"- Governance findings: {quality.governance_open_findings} open "
        f"/ {quality.governance_fixed_count} fixed "
        f"/ {quality.governance_total_findings} total"
    )
    lines.append(
        f"- Probe hints: {quality.probe_hints_total} total across "
        f"{quality.probe_files_scanned} files scanned"
    )
    lines.append("")


def _render_identity(lines: list[str], snapshot: ReviewSnapshot) -> None:
    identity = snapshot.identity
    lines.append("## 1. Identity")
    lines.append("")
    lines.append(f"- Repository: **{identity.repo_name or 'unknown'}**")
    if identity.repo_description:
        lines.append(f"- Description: {identity.repo_description}")
    if identity.product_thesis:
        lines.append(f"- Product thesis: {identity.product_thesis}")
    if identity.remote_url:
        lines.append(f"- Remote: `{identity.remote_url}`")
    if identity.default_branch:
        lines.append(f"- Default branch: `{identity.default_branch}`")
    lines.append(f"- Current branch: `{identity.branch or 'n/a'}`")
    lines.append(f"- HEAD SHA: `{identity.head_sha or 'n/a'}`")
    lines.append(f"- HEAD author: {identity.head_author or 'n/a'}")
    lines.append(f"- HEAD timestamp (UTC): {identity.head_timestamp_utc or 'n/a'}")
    if identity.previous_snapshot_head_sha:
        lines.append(
            f"- Previous snapshot HEAD: `{identity.previous_snapshot_head_sha}`"
        )
        lines.append(f"- Commits since previous: {identity.commits_since_previous}")
    lines.append("")


def _render_governance_state(lines: list[str], snapshot: ReviewSnapshot) -> None:
    state = snapshot.governance_state
    lines.append("## 2. Governance state")
    lines.append("")
    lines.append("### Push decision")
    lines.append(f"- action: `{state.push_action or 'n/a'}`")
    lines.append(f"- reason: {state.push_reason or 'n/a'}")
    lines.append(f"- push_eligible_now: {state.push_eligible_now}")
    lines.append(f"- worktree_clean: {state.worktree_clean}")
    lines.append(f"- next_step_command: `{state.next_step_command or 'n/a'}`")
    if state.publication_backlog_state:
        lines.append(f"- publication_backlog: {state.publication_backlog_state}")
    if state.publication_guidance:
        lines.append(f"- publication_guidance: {state.publication_guidance}")
    lines.append("")
    lines.append("### Reviewer runtime")
    lines.append(f"- reviewer_mode: `{state.reviewer_mode or 'n/a'}`")
    lines.append(f"- reviewer_freshness: {state.reviewer_freshness}")
    lines.append(f"- reviewer_publish_clear: {state.reviewer_publish_clear}")
    lines.append(f"- interaction_mode: `{state.interaction_mode}`")
    if state.reviewer_implementation_blocked:
        lines.append(
            f"- implementation_blocked: yes — {state.reviewer_block_reason or 'unspecified'}"
        )
    lines.append("")
    lines.append("### Remote commit pipeline")
    lines.append(f"- state: `{state.pipeline_state or 'n/a'}`")
    lines.append(f"- approval_state: `{state.pipeline_approval_state or 'n/a'}`")
    if state.pipeline_blocked_reason:
        lines.append(f"- blocked_reason: {state.pipeline_blocked_reason}")
    lines.append("")
    lines.append("### Work intake")
    if state.active_plan_title:
        lines.append(f"- active plan: **{state.active_plan_title}**")
    if state.active_plan_path:
        lines.append(f"- plan path: `{state.active_plan_path}`")
    if state.active_mp_scope:
        lines.append(f"- active MP scope: {', '.join(state.active_mp_scope)}")
    if state.advisory_action:
        lines.append(
            f"- advisory: `{state.advisory_action}` — {state.advisory_reason or ''}"
        )
    if state.checkpoint_required:
        lines.append("- checkpoint_required: **yes**")
    lines.append("")


def _render_footer(lines: list[str], snapshot: ReviewSnapshot) -> None:
    identity = snapshot.identity
    lines.append("---")
    lines.append("")
    lines.append(
        "Projection produced by `devctl review-snapshot`. "
        f"Generation stamp `{identity.generation_stamp}` binds this file to "
        f"HEAD `{identity.head_sha_short}`; if they drift, the freshness guard will fail CI."
    )


__all__ = ["render_review_snapshot_markdown"]
