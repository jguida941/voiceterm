"""Markdown renderers for system-picture artifacts and proof-ledger projections."""

from __future__ import annotations

from .system_picture_models import SystemPictureSection, SystemPictureSnapshot
from .system_picture_render_ledger import (
    render_claim_boundary_and_matrix,
    render_evidence_sections,
    render_ledger_header,
    render_market_and_proof_log,
    render_proof_snapshot,
)


def render_system_picture_markdown(snapshot: SystemPictureSnapshot) -> str:
    """Render the bounded system-picture artifact for repo-owned consumers."""
    lines = ["# devctl system-picture", ""]
    lines.append(f"- snapshot_id: {snapshot.snapshot_id}")
    lines.append(f"- generated_at_utc: {snapshot.generated_at_utc}")
    lines.append(f"- repo_name: {snapshot.repo_name}")
    lines.append(f"- current_branch: {snapshot.current_branch or '(unknown)'}")
    lines.append(f"- head_commit_sha: {snapshot.head_commit_sha or '(unknown)'}")
    lines.append(f"- tree_hash: {snapshot.tree_hash or '(unknown)'}")
    lines.append(f"- current_section_count: {snapshot.current_section_count}")
    lines.append(f"- stale_section_count: {snapshot.stale_section_count}")
    lines.append(f"- missing_section_count: {snapshot.missing_section_count}")
    lines.append("")
    lines.append("## Sections")
    lines.append("")
    lines.append("| Section | Status | Source Path | Source Command |")
    lines.append("|---|---|---|---|")
    for section in snapshot.sections:
        lines.append(
            "| {title} | {status} | `{source_path}` | `{source_command}` |".format(
                title=section.title,
                status=section.status,
                source_path=section.source_path or "-",
                source_command=section.source_command or "-",
            )
        )
    lines.append("")
    for section in snapshot.sections:
        lines.extend(_render_section_detail(section))
    return "\n".join(lines)


def render_system_picture_ledger_markdown(snapshot: SystemPictureSnapshot) -> str:
    """Render the tracked proof-ledger projection from the current snapshot."""
    date = _snapshot_date(snapshot)
    startup = _section(snapshot, "startup")
    graph = _section(snapshot, "graph")
    review_runtime = _section(snapshot, "review_runtime")
    governance_review = _section(snapshot, "governance_review")
    external_findings = _section(snapshot, "external_findings")
    data_science = _section(snapshot, "data_science")

    startup_summary = startup.summary if startup is not None else {}
    graph_summary = graph.summary if graph is not None else {}
    review_summary = review_runtime.summary if review_runtime is not None else {}
    governance_summary = governance_review.summary if governance_review is not None else {}
    external_summary = external_findings.summary if external_findings is not None else {}
    data_science_summary = data_science.summary if data_science is not None else {}

    lines: list[str] = []
    lines.extend(render_ledger_header(date))
    lines.extend(render_claim_boundary_and_matrix())
    lines.extend(render_proof_snapshot(
        snapshot=snapshot,
        date=date,
        startup_summary=startup_summary,
        graph_summary=graph_summary,
        review_summary=review_summary,
        governance_summary=governance_summary,
        external_summary=external_summary,
        data_science_summary=data_science_summary,
    ))
    lines.extend(render_evidence_sections())
    lines.extend(render_market_and_proof_log(
        date=date,
        snapshot=snapshot,
        startup=startup,
        graph=graph,
        review_runtime=review_runtime,
    ))
    lines.extend(_render_proof_commands_and_footer())
    return "\n".join(lines) + "\n"


def _render_proof_commands_and_footer() -> list[str]:
    """Render the proof-commands block and ongoing-append rule."""
    return [
        "## Current Proof Commands",
        "",
        "```bash",
        "python3 dev/scripts/devctl.py system-picture --format md",
        "python3 dev/scripts/devctl.py system-picture --format json",
        "python3 dev/scripts/devctl.py system-picture --write-ledger --format md",
        "python3 dev/scripts/devctl.py startup-context --format summary",
        "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
        "python3 dev/scripts/devctl.py governance-review --format md",
        "python3 dev/scripts/devctl.py data-science --format md",
        "python3 dev/scripts/devctl.py probe-report --format md",
        "```",
        "",
        "For cross-repo proof, keep using the policy/adoption surfaces documented in",
        "`dev/scripts/README.md`, especially:",
        "",
        "```bash",
        "python3 dev/scripts/devctl.py governance-bootstrap --target-repo /tmp/copied-repo --format md",
        "python3 dev/scripts/devctl.py check --profile ci --repo-path /tmp/copied-repo --adoption-scan --format md",
        "python3 dev/scripts/devctl.py probe-report --repo-path /tmp/copied-repo --adoption-scan --format md",
        "```",
        "",
        "## Ongoing Append Rule",
        "",
        "When new proof lands, refresh `system-picture`, keep the generated",
        "`history/snapshots.jsonl` chain intact, and add the owner-plan progress",
        "note in the same change so the evidence stays machine-backed and",
        "repo-visible.",
        "",
        "Each proof update should keep these pieces aligned:",
        "",
        "- the generated `dev/reports/system_picture/latest/summary.{json,md}`",
        "- the tracked projection at `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md`",
        "- the owner-plan progress/audit notes in `dev/active/ai_governance_platform.md`",
        "- the owner-plan progress/audit notes in `dev/active/platform_authority_loop.md`",
        "",
        "Prefer appending evidence through typed artifacts, commands, receipts,",
        "tests, and plan-log updates. Do not turn this file back into a hand-kept",
        "second authority source.",
    ]


def _render_section_detail(section: SystemPictureSection) -> list[str]:
    lines = [f"## {section.title}", ""]
    lines.append(f"- section_id: {section.section_id}")
    lines.append(f"- status: {section.status}")
    lines.append(f"- source_path: {section.source_path or '(none)'}")
    lines.append(f"- source_command: {section.source_command or '(none)'}")
    lines.append(f"- generated_at_utc: {section.generated_at_utc or '(unknown)'}")
    lines.append(f"- section_hash: {section.section_hash}")
    if section.notes:
        lines.append("- notes:")
        for note in section.notes:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    for key, value in section.summary.items():
        lines.append(f"- {key}: `{value}`")
    if not section.summary:
        lines.append("- none")
    lines.append("")
    return lines


def _section(
    snapshot: SystemPictureSnapshot,
    section_id: str,
) -> SystemPictureSection | None:
    for section in snapshot.sections:
        if section.section_id == section_id:
            return section
    return None


def _snapshot_date(snapshot: SystemPictureSnapshot) -> str:
    generated = snapshot.generated_at_utc.strip()
    return generated.split("T", 1)[0] if "T" in generated else generated or "unknown"
