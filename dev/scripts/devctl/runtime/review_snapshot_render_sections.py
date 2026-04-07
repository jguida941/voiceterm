"""Section renderers for ReviewSnapshot markdown output.

Split out of ``review_snapshot_render`` so both files stay under the
code-shape soft limit. The main ``render_review_snapshot_markdown``
function in ``review_snapshot_render`` dispatches to these helpers for the
delta, quality, architecture, reviewer-hints, reasoning, and known-gaps
sections.
"""

from __future__ import annotations

from .review_snapshot_models import CommitRow, FileStatRow, ReviewSnapshot, WhyRecord


_COMMIT_BULLET_LIMIT = 25
_FILE_BULLET_LIMIT = 40


def render_delta(lines: list[str], snapshot: ReviewSnapshot) -> None:
    delta = snapshot.delta
    lines.append("## 3. Delta — what changed since the previous snapshot")
    lines.append("")
    if delta.from_sha:
        lines.append(f"Range: `{delta.from_sha[:12]}..{delta.to_sha[:12]}`")
    else:
        lines.append(
            f"Range: last {delta.commit_count} commits ending at `{delta.to_sha[:12]}`"
        )
    lines.append("")
    lines.append(f"- commits: {delta.commit_count}")
    lines.append(f"- files changed: {delta.files_changed_count}")
    lines.append(f"- insertions: +{delta.total_insertions}")
    lines.append(f"- deletions: -{delta.total_deletions}")
    if delta.bundle_classes_touched:
        lines.append(
            f"- bundle classes touched: {', '.join(delta.bundle_classes_touched)}"
        )
    if delta.risk_addons_triggered:
        lines.append(
            f"- risk add-ons triggered: {', '.join(delta.risk_addons_triggered)}"
        )
    if delta.authority_surfaces_touched:
        lines.append(
            f"- authority surfaces touched: {len(delta.authority_surfaces_touched)} file(s)"
        )
    lines.append("")
    if delta.commits:
        lines.append("### Commits")
        lines.append("")
        lines.append("| # | SHA | Subject | Files | +/- | Bundle | Risk |")
        lines.append("|---|---|---|---|---|---|---|")
        for idx, commit in enumerate(delta.commits[:_COMMIT_BULLET_LIMIT], start=1):
            lines.append(_commit_row(idx, commit))
        if len(delta.commits) > _COMMIT_BULLET_LIMIT:
            lines.append(
                f"| … | | _{len(delta.commits) - _COMMIT_BULLET_LIMIT} more commits trimmed_ | | | | |"
            )
        lines.append("")
    if delta.files:
        lines.append("### Files")
        lines.append("")
        lines.append("| Path | Bundle | +/- |")
        lines.append("|---|---|---|")
        for row in delta.files[:_FILE_BULLET_LIMIT]:
            lines.append(_file_row(row))
        if len(delta.files) > _FILE_BULLET_LIMIT:
            lines.append(
                f"| _{len(delta.files) - _FILE_BULLET_LIMIT} more files trimmed_ | | |"
            )
        lines.append("")


def render_quality(lines: list[str], snapshot: ReviewSnapshot) -> None:
    quality = snapshot.quality
    lines.append("## 4. Quality signals")
    lines.append("")
    lines.append("### Governance review")
    lines.append(f"- total findings: {quality.governance_total_findings}")
    lines.append(f"- open: {quality.governance_open_findings}")
    lines.append(f"- fixed: {quality.governance_fixed_count}")
    lines.append(f"- false positives: {quality.governance_false_positive_count}")
    if quality.governance_recent_findings:
        lines.append("")
        lines.append("Recent findings:")
        for row in quality.governance_recent_findings[:10]:
            lines.append(
                f"- `{row.check_id}` — `{row.file_path}` "
                f"({row.severity or 'n/a'}, verdict=`{row.verdict or 'n/a'}`)"
            )
    lines.append("")
    lines.append("### Probe report")
    lines.append(f"- files scanned: {quality.probe_files_scanned}")
    lines.append(f"- total hints: {quality.probe_hints_total}")
    if quality.probe_hints_by_severity:
        severity_parts = ", ".join(
            f"{k}={v}" for k, v in sorted(quality.probe_hints_by_severity.items())
        )
        lines.append(f"- by severity: {severity_parts}")
    if quality.probe_top_findings:
        lines.append("")
        lines.append("Top probe findings:")
        for row in quality.probe_top_findings[:10]:
            location = row.file
            if row.line:
                location = f"{location}:{row.line}"
            lines.append(
                f"- `{row.probe}` [{row.severity or 'n/a'}] `{location}` — "
                f"{row.summary or row.rule_id}"
            )
    lines.append("")
    if quality.ci_blocking_failures:
        lines.append("### CI blocking failures")
        lines.append("")
        for row in quality.ci_blocking_failures:
            lines.append(
                f"- `{row.name}` — exit {row.exit_code}: {row.summary or 'no summary'}"
            )
        lines.append("")


def render_architecture(lines: list[str], snapshot: ReviewSnapshot) -> None:
    arch = snapshot.architecture
    lines.append("## 5. Architecture surface")
    lines.append("")
    if arch.contract_ownership_map:
        lines.append("### Contract ownership map")
        lines.append("")
        lines.append("| Contract | Owner layer | Runtime model | Tokens |")
        lines.append("|---|---|---|---|")
        for row in arch.contract_ownership_map:
            tokens = ", ".join(row.startup_surface_tokens[:3]) or "—"
            lines.append(
                f"| `{row.contract_id}` | `{row.owner_layer or 'n/a'}` | "
                f"`{row.runtime_model or 'n/a'}` | {tokens} |"
            )
        lines.append("")
    if arch.hotspots:
        lines.append("### Hotspots (from context-graph bootstrap)")
        lines.append("")
        for row in arch.hotspots:
            reasons = ", ".join(row.reasons) if row.reasons else ""
            suffix = f" — {reasons}" if reasons else ""
            lines.append(f"- `{row.path}` ({row.risk_level or 'n/a'}){suffix}")
        lines.append("")
    if arch.active_plans:
        lines.append("### Active plans")
        lines.append("")
        for plan in arch.active_plans:
            lines.append(f"- {plan}")
        lines.append("")
    if arch.graph_node_count or arch.graph_edge_count:
        lines.append(
            f"Graph metrics: {arch.graph_node_count} nodes, "
            f"{arch.graph_edge_count} edges (source mode: {arch.graph_source_mode or 'n/a'})"
        )
        lines.append("")
    if arch.key_doc_paths:
        lines.append("### Key documents")
        lines.append("")
        for path in arch.key_doc_paths:
            lines.append(f"- `{path}`")
        lines.append("")


def render_reviewer_hints(lines: list[str], snapshot: ReviewSnapshot) -> None:
    hints = snapshot.reviewer_hints
    lines.append("## 6. Reviewer hints — please verify")
    lines.append("")
    if not hints.hints and not hints.suggested_commands:
        lines.append("_No specific reviewer hints derived for this delta._")
        lines.append("")
        return
    if hints.hints:
        lines.append("### Targeted hints")
        lines.append("")
        for hint in hints.hints:
            ref = f" (`{hint.reference}`)" if hint.reference else ""
            lines.append(f"- **{hint.kind}**: {hint.label}{ref} — {hint.detail}")
        lines.append("")
    if hints.suggested_commands:
        lines.append("### Suggested verification commands")
        lines.append("")
        for command in hints.suggested_commands:
            lines.append(f"- `{command}`")
        lines.append("")


def render_reasoning(lines: list[str], snapshot: ReviewSnapshot) -> None:
    reasoning = snapshot.reasoning
    lines.append("## 7. Reasoning — why these changes landed")
    lines.append("")
    if reasoning.commit_why_records:
        lines.append("### Per-commit rationale")
        lines.append("")
        for record in reasoning.commit_why_records[:_COMMIT_BULLET_LIMIT]:
            _render_why_record(lines, record)
    if reasoning.active_mp_summaries:
        lines.append("### Active MP scope (from MASTER_PLAN.md)")
        lines.append("")
        for summary in reasoning.active_mp_summaries:
            lines.append(f"- {summary}")
        lines.append("")


def render_known_gaps(lines: list[str], snapshot: ReviewSnapshot) -> None:
    gaps = snapshot.known_gaps
    lines.append("## 8. Known gaps and open items")
    lines.append("")
    lines.append(f"- open governance findings: {gaps.open_governance_findings}")
    if gaps.startup_action_advisories:
        lines.append("")
        lines.append("### Startup advisories")
        for advisory in gaps.startup_action_advisories:
            lines.append(f"- {advisory}")
    if gaps.stale_warnings:
        lines.append("")
        lines.append("### Stale warnings")
        for warning in gaps.stale_warnings:
            lines.append(f"- {warning}")
    if gaps.gaps:
        lines.append("")
        lines.append("### Open gap rows")
        for row in gaps.gaps:
            ref = f" (`{row.reference}`)" if row.reference else ""
            lines.append(f"- **{row.kind}**{ref}: {row.summary}")
    lines.append("")


def _render_why_record(lines: list[str], record: WhyRecord) -> None:
    header_parts = [f"`{record.commit_sha_short or 'n/a'}`"]
    if record.mp_refs:
        header_parts.append(f"MPs: {', '.join(record.mp_refs)}")
    if record.checkpoint_markers:
        header_parts.append(f"markers: {', '.join(record.checkpoint_markers)}")
    lines.append(f"- **{' | '.join(header_parts)}** — {record.subject or ''}")
    if record.body_excerpt:
        for body_line in record.body_excerpt.splitlines()[:3]:
            lines.append(f"  - {body_line}")
    if record.linked_plan_docs:
        for doc in record.linked_plan_docs:
            lines.append(f"  - plan: `{doc}`")
    if record.evolution_rationale:
        snippet = record.evolution_rationale
        if len(snippet) > 220:
            snippet = snippet[:219] + "…"
        lines.append(f"  - evolution: {snippet}")


def _commit_row(idx: int, commit: CommitRow) -> str:
    subject = _truncate(commit.subject, 60)
    risk = ", ".join(commit.risk_addons) if commit.risk_addons else ""
    return (
        f"| {idx} | `{commit.sha_short}` | {subject} | {commit.files_changed} | "
        f"+{commit.insertions}/-{commit.deletions} | {commit.bundle_class} | {risk} |"
    )


def _file_row(row: FileStatRow) -> str:
    return f"| `{row.path}` | {row.bundle_class} | +{row.insertions}/-{row.deletions} |"


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


__all__ = [
    "render_architecture",
    "render_delta",
    "render_known_gaps",
    "render_quality",
    "render_reasoning",
    "render_reviewer_hints",
]
