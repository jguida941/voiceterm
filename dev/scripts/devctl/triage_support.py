"""Shared triage helpers for `devctl triage`.

This module keeps classification/rendering/artifact logic separate from command
orchestration so `commands/triage.py` stays small and focused.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .config import REPO_ROOT
from .status_report import render_project_markdown

FAILURE_CONCLUSIONS = {
    "failure",
    "timed_out",
    "cancelled",
    "action_required",
    "startup_failure",
}


def resolve_emit_dir(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _score_to_percent(score: Any) -> float | None:
    if not isinstance(score, (int, float)):
        return None
    value = float(score)
    if 0.0 <= value <= 1.0:
        value *= 100.0
    return value


def classify_issues(project_report: dict) -> List[dict]:
    """Create lightweight triage classifications from project status fields."""
    issues: List[dict] = []
    ci_info = project_report.get("ci", {})
    if isinstance(ci_info, dict):
        if ci_info.get("error"):
            issues.append(
                {
                    "category": "infra",
                    "severity": "high",
                    "source": "devctl.status.ci",
                    "summary": f"CI fetch failed: {ci_info['error']}",
                }
            )
        for run in ci_info.get("runs", []):
            if not isinstance(run, dict):
                continue
            conclusion = str(run.get("conclusion") or "").strip().lower()
            status = str(run.get("status") or "").strip().lower()
            if conclusion in FAILURE_CONCLUSIONS:
                title = str(run.get("displayTitle") or "unknown")
                issues.append(
                    {
                        "category": "ci",
                        "severity": "high" if conclusion == "failure" else "medium",
                        "source": "devctl.status.ci",
                        "summary": f"{title}: {status}/{conclusion}",
                    }
                )

    mutants_info = project_report.get("mutants", {})
    if isinstance(mutants_info, dict):
        if mutants_info.get("error"):
            issues.append(
                {
                    "category": "quality",
                    "severity": "medium",
                    "source": "devctl.status.mutants",
                    "summary": f"Mutation summary unavailable: {mutants_info['error']}",
                }
            )
        else:
            results = mutants_info.get("results", {})
            if isinstance(results, dict):
                score_pct = _score_to_percent(results.get("score"))
                if score_pct is not None and score_pct < 80.0:
                    issues.append(
                        {
                            "category": "quality",
                            "severity": "medium",
                            "source": "devctl.status.mutants",
                            "summary": f"Mutation score below target: {score_pct:.2f}%",
                        }
                    )

    git_info = project_report.get("git", {})
    if isinstance(git_info, dict):
        changes = git_info.get("changes", [])
        if isinstance(changes, list) and changes:
            if git_info.get("changelog_updated") is False:
                issues.append(
                    {
                        "category": "docs",
                        "severity": "low",
                        "source": "devctl.status.git",
                        "summary": "Working tree has changes but dev/CHANGELOG.md was not updated.",
                    }
                )
            if git_info.get("master_plan_updated") is False:
                issues.append(
                    {
                        "category": "governance",
                        "severity": "low",
                        "source": "devctl.status.git",
                        "summary": "Working tree has changes but dev/active/MASTER_PLAN.md was not updated.",
                    }
                )
    return issues


def build_next_actions(issues: List[dict]) -> List[str]:
    if not issues:
        return ["No urgent triage actions detected from current signals."]

    actions: List[str] = []
    categories = {str(issue.get("category", "")) for issue in issues}
    if "ci" in categories or "infra" in categories:
        actions.append("Run `python3 dev/scripts/devctl.py status --ci --require-ci --format md` and inspect failing workflow runs.")
    if "quality" in categories:
        actions.append("Run `python3 dev/scripts/devctl.py check --profile ci` and `python3 dev/scripts/devctl.py mutation-score` to confirm quality gates.")
    if "docs" in categories or "governance" in categories:
        actions.append("Run `python3 dev/scripts/devctl.py docs-check --strict-tooling` and link updates in `dev/active/MASTER_PLAN.md`.")
    if not actions:
        actions.append("Review triage issues and resolve highest-severity items first.")
    return actions


def _load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON ({exc})"
    if not isinstance(payload, dict):
        return None, "expected top-level JSON object"
    return payload, None


def ingest_cihub_artifacts(emit_dir: Path) -> dict:
    """Read cihub triage outputs when present."""
    payload: Dict[str, Any] = {"emit_dir": str(emit_dir), "artifacts": {}}
    triage_json_path = emit_dir / "triage.json"
    priority_json_path = emit_dir / "priority.json"
    triage_md_path = emit_dir / "triage.md"

    if triage_json_path.exists():
        triage_json, err = _load_json(triage_json_path)
        payload["artifacts"]["triage_json_path"] = str(triage_json_path)
        if err:
            payload["artifacts"]["triage_json_error"] = err
        else:
            payload["artifacts"]["triage_json"] = triage_json

    if priority_json_path.exists():
        priority_json, err = _load_json(priority_json_path)
        payload["artifacts"]["priority_json_path"] = str(priority_json_path)
        if err:
            payload["artifacts"]["priority_json_error"] = err
        else:
            payload["artifacts"]["priority_json"] = priority_json

    if triage_md_path.exists():
        try:
            text = triage_md_path.read_text(encoding="utf-8")
        except OSError as exc:
            payload["artifacts"]["triage_markdown_error"] = str(exc)
        else:
            payload["artifacts"]["triage_markdown_path"] = str(triage_md_path)
            payload["artifacts"]["triage_markdown_preview"] = "\n".join(text.splitlines()[:40])

    return payload


def render_triage_markdown(report: dict) -> str:
    """Render compact markdown suitable for humans."""
    lines = ["# devctl triage", ""]
    lines.append(f"- timestamp: {report.get('timestamp')}")
    lines.append(f"- issues: {len(report.get('issues', []))}")
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append(f"- warnings: {len(warnings)}")
    lines.append("")

    rollup = report.get("rollup", {})
    if isinstance(rollup, dict) and rollup:
        lines.append("## Rollup")
        lines.append("")
        lines.append(f"- total: {rollup.get('total', 0)}")
        by_severity = rollup.get("by_severity", {})
        if isinstance(by_severity, dict) and by_severity:
            lines.append("- by_severity: " + ", ".join(f"{k}={v}" for k, v in by_severity.items()))
        by_category = rollup.get("by_category", {})
        if isinstance(by_category, dict) and by_category:
            lines.append("- by_category: " + ", ".join(f"{k}={v}" for k, v in by_category.items()))
        by_owner = rollup.get("by_owner", {})
        if isinstance(by_owner, dict) and by_owner:
            lines.append("- by_owner: " + ", ".join(f"{k}={v}" for k, v in by_owner.items()))
        lines.append("")

    lines.append("## Project Snapshot")
    lines.append("")
    project = report.get("project", {})
    if isinstance(project, dict):
        lines.append(
            render_project_markdown(
                project,
                title="triage snapshot",
                include_ci_details=True,
                ci_details_limit=5,
            )
        )
    else:
        lines.append("- unavailable")
    lines.append("")

    lines.append("## Issues")
    lines.append("")
    issues = report.get("issues", [])
    if not issues:
        lines.append("- none")
    else:
        for issue in issues:
            owner = issue.get("owner", "unassigned")
            lines.append(
                "- "
                + f"[{issue.get('severity', 'unknown')}] "
                + f"{issue.get('category', 'unknown')} -> {owner}: "
                + f"{issue.get('summary', 'no summary')}"
            )
    lines.append("")

    lines.append("## Next Actions")
    lines.append("")
    for action in report.get("next_actions", []):
        lines.append(f"- {action}")
    lines.append("")

    cihub = report.get("cihub", {})
    if isinstance(cihub, dict):
        lines.append("## CIHub")
        lines.append("")
        lines.append(f"- enabled: {cihub.get('enabled')}")
        if cihub.get("warning"):
            lines.append(f"- warning: {cihub['warning']}")
        step = cihub.get("step")
        if isinstance(step, dict):
            lines.append(f"- command exit: {step.get('returncode')}")
        artifacts = cihub.get("artifacts", {})
        if isinstance(artifacts, dict):
            if artifacts.get("triage_json_path"):
                lines.append(f"- triage_json: {artifacts['triage_json_path']}")
            if artifacts.get("priority_json_path"):
                lines.append(f"- priority_json: {artifacts['priority_json_path']}")
            if artifacts.get("triage_markdown_path"):
                lines.append(f"- triage_markdown: {artifacts['triage_markdown_path']}")
        lines.append("")

    bundle = report.get("bundle", {})
    if isinstance(bundle, dict) and bundle.get("written"):
        lines.append("## Bundle")
        lines.append("")
        lines.append(f"- markdown: {bundle.get('markdown_path')}")
        lines.append(f"- ai_json: {bundle.get('ai_json_path')}")
        lines.append("")

    return "\n".join(lines)


def write_bundle(report: dict, emit_dir: Path, prefix: str) -> dict:
    emit_dir.mkdir(parents=True, exist_ok=True)
    base = emit_dir / prefix
    md_path = base.with_suffix(".md")
    ai_path = base.with_suffix(".ai.json")
    md_path.write_text(render_triage_markdown(report), encoding="utf-8")
    ai_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "written": True,
        "markdown_path": str(md_path),
        "ai_json_path": str(ai_path),
    }
