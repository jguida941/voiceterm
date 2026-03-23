"""Prompt-building helpers for Ralph remediation routes."""

from __future__ import annotations

from dev.scripts.devctl.context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
)

from .ralph_guidance_contract import GUIDANCE_SUMMARY_END, GUIDANCE_SUMMARY_START


def _build_standards_context(items: list[dict], guardrails_config: dict) -> str:
    """Build a standards reference block from guardrails config for the prompt."""
    standards = guardrails_config.get("standards", {})
    if not standards:
        return ""
    categories = {str(item.get("category", "")).lower() for item in items}
    relevant: list[str] = []
    for key, std in standards.items():
        if key in categories or any(cat in key for cat in categories):
            relevant.append(
                f"  - {key}: {std.get('description', '')} "
                f"(ref: {std.get('agents_md_section', 'AGENTS.md')})"
            )
    if not relevant:
        return ""
    return "## Applicable Standards\n\n" + "\n".join(relevant)


def build_backlog_context_packet(
    items: list[dict],
    *,
    collect_query_terms_fn=collect_query_terms,
    build_context_packet_fn=build_context_escalation_packet,
) -> ContextEscalationPacket | None:
    """Build a bounded context packet from backlog findings."""
    values: list[object] = []
    for item in items[:6]:
        if not isinstance(item, dict):
            continue
        values.append(item)
        values.extend(
            [
                item.get("summary"),
                item.get("path"),
                item.get("file"),
                item.get("module"),
                item.get("target"),
            ]
        )
    query_terms = collect_query_terms_fn(values, max_terms=4)
    return build_context_packet_fn(
        trigger="ralph-backlog",
        query_terms=query_terms,
        options={"max_chars": 900},
    )


def build_prompt(
    items: list[dict],
    attempt: int,
    guardrails_config: dict | None = None,
    context_packet: ContextEscalationPacket | None = None,
) -> str:
    """Build a Claude Code prompt from backlog items with optional standards context."""
    finding_lines: list[str] = []
    for index, item in enumerate(items):
        line = (
            f"  {index + 1}. [{item.get('severity', 'unknown')}] "
            f"({item.get('category', 'unknown')}) {item.get('summary', 'no summary')}"
        )
        item_guidance = item.get("probe_guidance")
        if isinstance(item_guidance, list):
            for entry in item_guidance[:2]:
                if not isinstance(entry, dict):
                    continue
                line += (
                    "\n     Probe guidance: "
                    f"{entry.get('ai_instruction') or ''} "
                    f"({entry.get('probe') or 'probe'} on "
                    f"{entry.get('file_path') or entry.get('symbol') or 'matched file'})"
                )
        finding_lines.append(line)
    findings_text = "\n".join(finding_lines)

    standards_block = ""
    if guardrails_config:
        standards_block = _build_standards_context(items, guardrails_config)
    standards_section = f"\n\n{standards_block}" if standards_block else ""
    context_section = ""
    if context_packet is not None:
        context_section = (
            "\n\n## Preloaded Context Recovery\n\n"
            f"{context_packet.markdown}"
        )
    guidance_output_contract = f"""

## Required Output

After your normal explanation, emit one JSON array between these exact markers:
`{GUIDANCE_SUMMARY_START}`
`{GUIDANCE_SUMMARY_END}`

Each array row must use the exact finding summary text and this shape:
{{"summary":"<exact summary>","guidance_disposition":"used|waived|not_applicable","waiver_reason":"<required only when waived>"}}

- If a finding includes `Probe guidance:`, treat that guidance as the default repair plan.
- Do not invent a different refactoring approach unless the attached guidance is clearly wrong for the current code.
- If you do waive attached guidance, set `guidance_disposition` to `waived` and give a concrete `waiver_reason`.
- If no probe guidance is attached for a finding, use `not_applicable`.
"""

    return f"""You are fixing CodeRabbit findings in the codex-voice repository.
This is Ralph loop attempt {attempt}.

## Probe Guidance Policy

If a finding carries `Probe guidance:`, use the probe's recommended approach
as your default fix plan. Do not invent a different repair strategy unless the
guidance is clearly wrong for the current code, and explain any waiver in the
required output contract below.

## Findings to evaluate

{findings_text}{standards_section}

## Instructions

For EACH finding above:
1. Evaluate whether the finding is a genuine issue or a false positive.
   - If the finding references code that doesn't exist, skip it.
   - If the finding suggests a change that would break existing behavior, skip it.
   - If the finding is stylistic and conflicts with project conventions, skip it.
2. If the finding IS valid, fix it directly in the codebase.
3. After fixing, verify the fix doesn't break anything by reading surrounding code.
4. If a finding points at a file, guard, or subsystem you have not read yet,
   run `python3 dev/scripts/devctl.py context-graph --query '<term>' --format md`
   before widening scope.{context_section}

## Rules
- Follow existing code style and conventions (read AGENTS.md for policy).
- Do not add unnecessary comments or docstrings.
- Do not refactor unrelated code.
- Keep fixes minimal and focused.
- If you skip a finding as a false positive, note why briefly in your output.

Fix all valid findings now.{guidance_output_contract}"""
