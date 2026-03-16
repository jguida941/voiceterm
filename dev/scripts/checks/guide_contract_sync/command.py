"""Validate repo-policy-owned guide contracts against durable docs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, import_repo_module
except ModuleNotFoundError:  # pragma: no cover - package execution fallback
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        import_repo_module,
    )

_common_io = import_repo_module("dev.scripts.devctl.common_io", repo_root=REPO_ROOT)
_repo_policy = import_repo_module(
    "dev.scripts.devctl.repo_policy",
    repo_root=REPO_ROOT,
)
_markdown_sections = import_repo_module(
    "dev.scripts.devctl.markdown_sections",
    repo_root=REPO_ROOT,
)
display_path = _common_io.display_path
load_repo_governance_section = _repo_policy.load_repo_governance_section
parse_markdown_sections = _markdown_sections.parse_markdown_sections


@dataclass(frozen=True, slots=True)
class GuideSectionRule:
    """One section-scoped coverage requirement inside a guide contract."""

    heading: str
    required_contains: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GuideContractRule:
    """One policy-owned guide contract."""

    rule_id: str
    doc_path: str
    required_contains: tuple[str, ...]
    required_sections: tuple[GuideSectionRule, ...]


def _coerce_section_rules(payload: object) -> tuple[GuideSectionRule, ...]:
    if not isinstance(payload, list):
        return ()
    rules: list[GuideSectionRule] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        heading = str(entry.get("heading") or "").strip()
        raw_required = entry.get("required_contains")
        if not isinstance(raw_required, list):
            continue
        required_contains = tuple(
            text for item in raw_required if (text := str(item).strip())
        )
        if heading and required_contains:
            rules.append(
                GuideSectionRule(
                    heading=heading,
                    required_contains=required_contains,
                )
            )
    return tuple(rules)


def _coerce_rules(payload: object) -> tuple[GuideContractRule, ...]:
    if not isinstance(payload, list):
        return ()
    rules: list[GuideContractRule] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        rule_id = str(entry.get("id") or "").strip()
        doc_path = str(entry.get("doc_path") or "").strip()
        raw_required = entry.get("required_contains")
        if not isinstance(raw_required, list):
            continue
        required_contains = tuple(
            text for item in raw_required if (text := str(item).strip())
        )
        required_sections = _coerce_section_rules(entry.get("required_sections"))
        if rule_id and doc_path and (required_contains or required_sections):
            rules.append(
                GuideContractRule(
                    rule_id=rule_id,
                    doc_path=doc_path,
                    required_contains=required_contains,
                    required_sections=required_sections,
                )
            )
    return tuple(rules)


def build_report(*, policy_path: str | None = None) -> dict[str, object]:
    """Build the guide-contract sync report."""
    section, warnings, resolved_path = load_repo_governance_section(
        "docs_check",
        repo_root=REPO_ROOT,
        policy_path=policy_path,
    )
    rules = _coerce_rules(section.get("guide_contract_rules"))
    checked_rules: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []
    for rule in rules:
        target = REPO_ROOT / rule.doc_path
        if not target.exists():
            violation = {
                "rule_id": rule.rule_id,
                "doc_path": rule.doc_path,
                "missing_contains": list(rule.required_contains),
                "section_violations": [
                    {
                        "heading": section_rule.heading,
                        "missing_contains": list(section_rule.required_contains),
                        "error": "missing file",
                    }
                    for section_rule in rule.required_sections
                ],
                "error": "missing file",
                "ok": False,
            }
            checked_rules.append(violation)
            violations.append(violation)
            continue
        text = target.read_text(encoding="utf-8")
        sections = parse_markdown_sections(text)
        missing_contains = [
            token for token in rule.required_contains if token not in text
        ]
        section_violations: list[dict[str, object]] = []
        for section_rule in rule.required_sections:
            section_text = sections.get(section_rule.heading)
            if section_text is None:
                section_violations.append(
                    {
                        "heading": section_rule.heading,
                        "missing_contains": list(section_rule.required_contains),
                        "error": "missing heading",
                    }
                )
                continue
            missing_section_tokens = [
                token
                for token in section_rule.required_contains
                if token not in section_text
            ]
            if missing_section_tokens:
                section_violations.append(
                    {
                        "heading": section_rule.heading,
                        "missing_contains": missing_section_tokens,
                        "error": None,
                    }
                )
        entry = {
            "rule_id": rule.rule_id,
            "doc_path": rule.doc_path,
            "missing_contains": missing_contains,
            "section_violations": section_violations,
            "ok": not missing_contains and not section_violations,
        }
        checked_rules.append(entry)
        if missing_contains or section_violations:
            violations.append(entry)
    return {
        "command": "check_guide_contract_sync",
        "ok": not violations,
        "policy_path": display_path(resolved_path, repo_root=REPO_ROOT),
        "warnings": list(warnings),
        "checked_rule_count": len(checked_rules),
        "checked_rules": checked_rules,
        "violations": violations,
    }


def render_md(report: dict[str, object]) -> str:
    """Render the report in markdown form."""
    lines = [
        "# check_guide_contract_sync",
        "",
        f"- ok: {report.get('ok')}",
        f"- policy_path: {report.get('policy_path')}",
        f"- checked_rule_count: {report.get('checked_rule_count')}",
    ]
    warnings = report.get("warnings") or []
    if warnings:
        lines.append(f"- warnings: {', '.join(str(item) for item in warnings)}")
    violations = report.get("violations") or []
    if not violations:
        lines.extend(["", "## Guide Contracts", "- all configured rules are in sync"])
        return "\n".join(lines)
    lines.extend(["", "## Violations"])
    for violation in violations:
        lines.append(
            "- {rule_id}: {doc_path}".format(
                rule_id=violation.get("rule_id"),
                doc_path=violation.get("doc_path"),
            )
        )
        if violation.get("error"):
            lines.append(f"  - error: {violation.get('error')}")
        missing = violation.get("missing_contains") or []
        if missing:
            lines.append("  - missing_contains: " + " | ".join(str(item) for item in missing))
        for section_violation in violation.get("section_violations") or []:
            lines.append(
                "  - section `{heading}`".format(
                    heading=section_violation.get("heading"),
                )
            )
            if section_violation.get("error"):
                lines.append(f"    - error: {section_violation.get('error')}")
            section_missing = section_violation.get("missing_contains") or []
            if section_missing:
                lines.append(
                    "    - missing_contains: "
                    + " | ".join(str(item) for item in section_missing)
                )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality-policy", help="Optional repo policy JSON file to resolve.")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    try:
        report = build_report(policy_path=args.quality_policy)
    # broad-except: allow reason=guard entrypoints must return a structured runtime error instead of a traceback fallback=structured-runtime-error
    except Exception as exc:  # pragma: no cover - runtime safety
        return emit_runtime_error("check_guide_contract_sync", args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_md(report))
    return 0 if report.get("ok", False) else 1
