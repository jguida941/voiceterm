#!/usr/bin/env python3
"""Ralph AI fix wrapper for CodeRabbit backlog remediation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.approval_mode import DEFAULT_APPROVAL_MODE, normalize_approval_mode
from dev.scripts.devctl.context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
)
from dev.scripts.devctl.ralph_guardrail_report import (
    build_guardrail_report,
    load_guardrails_config,
    render_report_json,
)

ARCH_CHECKS: dict[str, list[list[str]]] = {
    "rust": [
        ["cargo", "check", "--workspace", "--all-features"],
        ["cargo", "test", "--bin", "voiceterm", "--", "--test-threads=1"],
    ],
    "python-devctl": [["python3", "-m", "pytest", "dev/scripts/devctl/tests/", "-q", "--tb=short"]],
    "python-operator-console": [["python3", "-m", "pytest", "app/operator_console/tests/", "-q", "--tb=short"]],
    "ios": [["python3", "dev/scripts/devctl.py", "mobile-status", "--format", "json"]],
}

_FALLBACK_CATEGORY_TO_ARCH: dict[str, str] = {
    "rust": "rust",
    "performance": "rust",
    "security": "rust",
    "python": "python-devctl",
    "tooling": "python-devctl",
    "quality": "python-devctl",
    "operator-console": "python-operator-console",
    "ui": "python-operator-console",
    "ios": "ios",
    "mobile": "ios",
    "docs": "python-devctl",
    "ci": "python-devctl",
    "infra": "python-devctl",
}


def load_backlog(backlog_dir: str) -> list[dict]:
    """Load and return items from backlog-medium.json."""
    backlog_path = Path(backlog_dir) / "backlog-medium.json"
    if not backlog_path.exists():
        print(f"[ralph-ai-fix] backlog not found: {backlog_path}", file=sys.stderr)
        return []
    with open(backlog_path) as handle:
        data = json.load(handle)
    items = data.get("items", [])
    print(f"[ralph-ai-fix] loaded {len(items)} backlog items")
    return items


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
    query_terms = collect_query_terms(values, max_terms=4)
    return build_context_escalation_packet(
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
    findings_text = "\n".join(
        f"  {index + 1}. [{item.get('severity', 'unknown')}] "
        f"({item.get('category', 'unknown')}) {item.get('summary', 'no summary')}"
        for index, item in enumerate(items)
    )

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

    return f"""You are fixing CodeRabbit findings in the codex-voice repository.
This is Ralph loop attempt {attempt}.

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

Fix all valid findings now."""


def invoke_claude(prompt: str) -> int:
    """Invoke Claude Code CLI to evaluate and fix findings."""
    approval_mode = normalize_approval_mode(os.environ.get("RALPH_APPROVAL_MODE", DEFAULT_APPROVAL_MODE))
    cmd = ["claude", "--print", "--max-turns", "30"]
    if approval_mode == "trusted":
        cmd.append("--dangerously-skip-permissions")
    else:
        cmd.extend(["--permission-mode", "auto"])
    cmd.append(prompt)
    print(f"[ralph-ai-fix] invoking Claude Code ({len(prompt)} chars)")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False, timeout=600)
    return result.returncode


def detect_architectures(items: list[dict], guardrails_config: dict | None = None) -> set[str]:
    """Determine which architectures are affected by the findings."""
    cat_map = _FALLBACK_CATEGORY_TO_ARCH
    if guardrails_config:
        cat_map = guardrails_config.get("category_to_architecture", cat_map)
    archs = set()
    for item in items:
        category = item.get("category", "").lower()
        arch = cat_map.get(category, "python-devctl")
        archs.add(arch)
    return archs


def run_arch_checks(architectures: set[str]) -> bool:
    """Run architecture-specific validation checks. Returns True if all pass."""
    all_passed = True
    for arch in sorted(architectures):
        checks = ARCH_CHECKS.get(arch, [])
        for cmd in checks:
            print(f"[ralph-ai-fix] running {arch} check: {' '.join(cmd)}")
            cwd = str(REPO_ROOT / "rust") if arch == "rust" and cmd[0] == "cargo" else str(REPO_ROOT)
            result = subprocess.run(cmd, cwd=cwd, check=False)
            if result.returncode != 0:
                print(f"[ralph-ai-fix] {arch} check failed: {' '.join(cmd)}", file=sys.stderr)
                all_passed = False
    return all_passed


def has_changes() -> bool:
    """Check if there are uncommitted changes in the working tree."""
    result = subprocess.run(["git", "diff", "--quiet"], cwd=str(REPO_ROOT), check=False)
    return result.returncode != 0


def commit_and_push(branch: str, attempt: int, item_count: int) -> bool:
    """Stage, commit, and push changes from the AI fix."""
    msg = f"fix: ralph loop attempt {attempt} - remediate {item_count} CodeRabbit findings"
    subprocess.run(["git", "add", "-u"], cwd=str(REPO_ROOT), check=True)

    result = subprocess.run(["git", "commit", "-m", msg], cwd=str(REPO_ROOT), check=False)
    if result.returncode != 0:
        print("[ralph-ai-fix] commit failed", file=sys.stderr)
        return False

    result = subprocess.run(["git", "push", "origin", branch], cwd=str(REPO_ROOT), check=False)
    if result.returncode != 0:
        print("[ralph-ai-fix] push failed", file=sys.stderr)
        return False

    print(f"[ralph-ai-fix] committed and pushed to {branch}")
    return True


def _build_fix_results(items: list[dict], changes_made: bool, checks_passed: bool) -> list[dict]:
    """Build per-finding fix status entries based on outcome."""
    if not changes_made:
        status = "false-positive"
    elif checks_passed:
        status = "fixed"
    else:
        status = "pending"
    return [{"summary": str(it.get("summary", "")), "status": status, "fix_skill": ""} for it in items]


def _emit_report(report: dict, backlog_dir: str) -> str:
    """Write ralph-report.json to the backlog dir (or /tmp fallback)."""
    output_dir = Path(backlog_dir) if backlog_dir else Path(tempfile.gettempdir())
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "ralph-report.json"
    report_path.write_text(render_report_json(report), encoding="utf-8")
    print(f"[ralph-ai-fix] report written to {report_path}")
    return str(report_path)


def main() -> int:
    attempt = int(os.environ.get("RALPH_ATTEMPT", "1"))
    repo = os.environ.get("RALPH_REPO", "")
    branch = os.environ.get("RALPH_BRANCH", "")
    backlog_dir = os.environ.get("RALPH_BACKLOG_DIR", "")
    backlog_count = int(os.environ.get("RALPH_BACKLOG_COUNT", "0"))

    if not backlog_dir:
        print("[ralph-ai-fix] RALPH_BACKLOG_DIR not set", file=sys.stderr)
        return 2

    print(f"[ralph-ai-fix] attempt={attempt} repo={repo} branch={branch} backlog_count={backlog_count}")

    guardrails_config = load_guardrails_config()
    print(f"[ralph-ai-fix] loaded {len(guardrails_config.get('standards', {}))} guardrail standards")

    items = load_backlog(backlog_dir)
    if not items:
        print("[ralph-ai-fix] no backlog items - nothing to fix")
        return 0

    context_packet = build_backlog_context_packet(items)
    prompt = build_prompt(
        items,
        attempt,
        guardrails_config,
        context_packet=context_packet,
    )
    rc = invoke_claude(prompt)
    if rc != 0:
        print(f"[ralph-ai-fix] Claude Code exited with {rc}", file=sys.stderr)
        return 1

    changes_made = has_changes()
    if not changes_made:
        print("[ralph-ai-fix] AI made no changes (all findings may be false positives)")
        fix_results = _build_fix_results(items, False, False)
        report = build_guardrail_report(items, fix_results, guardrails_config, attempt, repo, branch)
        _emit_report(report, backlog_dir)
        return 0

    archs = detect_architectures(items, guardrails_config)
    print(f"[ralph-ai-fix] validating architectures: {', '.join(sorted(archs))}")
    checks_passed = run_arch_checks(archs)

    fix_results = _build_fix_results(items, True, checks_passed)
    report = build_guardrail_report(items, fix_results, guardrails_config, attempt, repo, branch)
    _emit_report(report, backlog_dir)

    if not checks_passed:
        print("[ralph-ai-fix] post-fix validation failed - reverting", file=sys.stderr)
        subprocess.run(["git", "checkout", "."], cwd=str(REPO_ROOT), check=False)
        return 1

    if not branch:
        print("[ralph-ai-fix] RALPH_BRANCH not set - cannot push", file=sys.stderr)
        return 2

    if not commit_and_push(branch, attempt, len(items)):
        return 1

    print("[ralph-ai-fix] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
