"""Detect repo-specific literals in portable governance substrates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.repo_portability import (  # noqa: E402
    RepoPortabilityCheck,
    load_repo_portability_policy,
    portability_allowed_literals,
    portability_ignore_paths,
    portability_operator_identity_literals,
    portability_project_name_literals,
    portability_target_paths,
)

COMMAND = "check_substrate_is_repo_portable"

_STATIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("packet_id_literal", re.compile(r"(?<![A-Za-z0-9_])rev_pkt_\d+(?![A-Za-z0-9_])")),
    (
        "plan_id_literal",
        re.compile(r"(?<![A-Za-z0-9_])MP-\d{3}(?:-[A-Za-z0-9_.]+)*(?![A-Za-z0-9_.-])"),
    ),
    (
        "absolute_path_literal",
        re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home|var/folders|tmp)/[^'\"`\s),]+"),
    ),
    (
        "session_timestamp_literal",
        re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z"),
    ),
)


@dataclass(frozen=True, slots=True)
class LiteralFinding:
    """One hardcoded literal found in a substrate file."""

    path: str
    line_number: int
    category: str
    literal: str
    proposed_lift: str
    policy_key_needed: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
    target_paths: tuple[str, ...] = (),
) -> dict[str, object]:
    """Return repo-portability scan results for configured substrate paths."""
    policy, warnings, resolved_policy_path = load_repo_portability_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    configured_targets = target_paths or portability_target_paths(policy)
    ignore_paths = portability_ignore_paths(policy)
    allowed = portability_allowed_literals(policy)
    source_paths, target_errors = _resolve_source_paths(
        repo_root=repo_root,
        target_paths=configured_targets,
        ignore_paths=ignore_paths,
    )
    dynamic_literals = _dynamic_literal_patterns(policy)
    findings: list[LiteralFinding] = []
    for source_path in source_paths:
        findings.extend(
            _scan_path(
                source_path,
                repo_root=repo_root,
                dynamic_literals=dynamic_literals,
                allowed_literals=allowed,
            )
        )

    checks = _checks_from_findings(findings)
    errors = list(warnings) + target_errors
    if not configured_targets:
        errors.append("repo_portability_policy_missing_target_paths")
    human_summary = _human_summary(findings=findings, errors=errors)
    return {
        "command": COMMAND,
        "schema_version": 1,
        "ok": not findings and not errors,
        "policy_path": _display_path(resolved_policy_path, repo_root=repo_root),
        "target_paths": list(configured_targets),
        "ignore_paths": list(ignore_paths),
        "source_file_count": len(source_paths),
        "finding_count": len(findings),
        "category_counts": _category_counts(findings),
        "findings": [finding.to_dict() for finding in findings],
        "checks": [check.to_dict() for check in checks],
        "errors": errors,
        "human_summary": human_summary,
    }


def _resolve_source_paths(
    *,
    repo_root: Path,
    target_paths: tuple[str, ...],
    ignore_paths: tuple[str, ...],
) -> tuple[tuple[Path, ...], list[str]]:
    source_paths: list[Path] = []
    errors: list[str] = []
    for raw_target in target_paths:
        target = (repo_root / raw_target).resolve(strict=False)
        if not target.exists():
            errors.append(f"target_path_missing:{raw_target}")
            continue
        candidates = [target] if target.is_file() else sorted(target.rglob("*.py"))
        for candidate in candidates:
            relative = _display_path(candidate, repo_root=repo_root)
            if _path_ignored(relative, ignore_paths=ignore_paths):
                continue
            source_paths.append(candidate)
    return tuple(dict.fromkeys(source_paths)), errors


def _path_ignored(path: str, *, ignore_paths: tuple[str, ...]) -> bool:
    return any(
        path == ignored
        or path.startswith(f"{ignored.rstrip('/')}/")
        or ignored in path
        for ignored in ignore_paths
    )


def _dynamic_literal_patterns(policy: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    project_names = portability_project_name_literals(policy)
    operator_ids = portability_operator_identity_literals(policy)
    patterns: list[tuple[str, str]] = []
    patterns.extend(("project_name_literal", literal) for literal in project_names)
    patterns.extend(("operator_identity_literal", literal) for literal in operator_ids)
    return tuple(patterns)


def _scan_path(
    path: Path,
    *,
    repo_root: Path,
    dynamic_literals: tuple[tuple[str, str], ...],
    allowed_literals: dict[str, tuple[str, ...]],
) -> tuple[LiteralFinding, ...]:
    findings: list[LiteralFinding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return (
            LiteralFinding(
                path=_display_path(path, repo_root=repo_root),
                line_number=0,
                category="read_error",
                literal=exc.__class__.__name__,
                proposed_lift="Make the configured target readable or remove it from repo policy.",
                policy_key_needed="repo_governance.repo_portability.target_paths",
            ),
        )
    relative = _display_path(path, repo_root=repo_root)
    for line_number, line in enumerate(lines, start=1):
        for category, pattern in _STATIC_PATTERNS:
            for match in pattern.finditer(line):
                literal = match.group(0)
                if _literal_allowed(category, literal, allowed_literals):
                    continue
                findings.append(
                    _finding(
                        path=relative,
                        line_number=line_number,
                        category=category,
                        literal=literal,
                    )
                )
        for category, literal in dynamic_literals:
            if not literal or literal not in line:
                continue
            if _literal_allowed(category, literal, allowed_literals):
                continue
            findings.append(
                _finding(
                    path=relative,
                    line_number=line_number,
                    category=category,
                    literal=literal,
                )
            )
    return tuple(findings)


def _literal_allowed(
    category: str,
    literal: str,
    allowed_literals: dict[str, tuple[str, ...]],
) -> bool:
    return literal in allowed_literals.get(category, ())


def _finding(
    *,
    path: str,
    line_number: int,
    category: str,
    literal: str,
) -> LiteralFinding:
    policy_key = _policy_key_for(category)
    return LiteralFinding(
        path=path,
        line_number=line_number,
        category=category,
        literal=literal,
        proposed_lift=f"Move `{literal}` to `{policy_key}` or another typed repo-pack policy key.",
        policy_key_needed=policy_key,
    )


def _policy_key_for(category: str) -> str:
    return {
        "packet_id_literal": "repo_governance.guard_mandates.<check>.mandate_packet_id",
        "plan_id_literal": "repo_governance.guard_mandates.<check>.enforced_row_prefixes",
        "project_name_literal": "repo_governance.repo_portability.project_name_literals",
        "absolute_path_literal": "ProjectGovernance.path_roots or repo-pack path config",
        "session_timestamp_literal": "repo_governance.guard_mandates.<check>.observed_at_utc",
        "operator_identity_literal": "repo_governance.repo_portability.operator_identity_literals",
    }.get(category, "repo_governance.repo_portability")


def _checks_from_findings(findings: list[LiteralFinding]) -> tuple[RepoPortabilityCheck, ...]:
    by_path: dict[str, list[LiteralFinding]] = {}
    for finding in findings:
        by_path.setdefault(finding.path, []).append(finding)
    checks: list[RepoPortabilityCheck] = []
    for path, path_findings in sorted(by_path.items()):
        categories = tuple(sorted({finding.category for finding in path_findings}))
        checks.append(
            RepoPortabilityCheck(
                check_id=COMMAND,
                target_substrate_path=path,
                hardcoded_literal_count=len(path_findings),
                hardcoded_categories=categories,
                proposed_lifts=tuple(finding.proposed_lift for finding in path_findings),
                repo_pack_policy_keys_needed=tuple(
                    sorted({finding.policy_key_needed for finding in path_findings})
                ),
            )
        )
    return tuple(checks)


def _category_counts(findings: list[LiteralFinding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.category] = counts.get(finding.category, 0) + 1
    return counts


def _human_summary(
    *,
    findings: list[LiteralFinding],
    errors: list[str],
) -> dict[str, object]:
    if errors:
        headline = f"ERROR - repo-portability scan has {len(errors)} setup error(s)."
    elif findings:
        headline = f"FAIL - {len(findings)} repo-specific literal(s) found in portable substrates."
    else:
        headline = "PASS - configured substrates have no repo-specific literals."
    return {
        "contract_id": "TypedOutputHumanSummary",
        "schema_version": 1,
        "headline": headline,
        "items_processed": len(findings),
        "conclusions": [
            f"Finding count: {len(findings)}.",
            f"Error count: {len(errors)}.",
        ],
        "evaluable_scopes": {
            "configured_substrate_paths": True,
        },
        "blind_pass_warning": (
            "No repo-portability target paths were configured."
            if errors and "repo_portability_policy_missing_target_paths" in errors
            else ""
        ),
        "recommendations": (
            ["Move flagged literals into repo-pack policy or typed contract fields."]
            if findings
            else []
        ),
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = ["# check_substrate_is_repo_portable", ""]
    for key in (
        "ok",
        "policy_path",
        "source_file_count",
        "finding_count",
    ):
        lines.append(f"- {key}: {report[key]}")
    category_counts = report.get("category_counts") or {}
    if category_counts:
        lines.extend(["", "## Categories"])
        for category, count in sorted(category_counts.items()):
            lines.append(f"- {category}: {count}")
    errors = report.get("errors") or []
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in errors)
    findings = report.get("findings") or []
    if findings:
        lines.extend(["", "## Findings"])
        for finding in findings:
            lines.append(
                f"- {finding['path']}:{finding['line_number']} "
                f"{finding['category']} `{finding['literal']}` -> "
                f"{finding['policy_key_needed']}"
            )
    return "\n".join(lines) + "\n"


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--policy-path", help="Override the repo policy JSON path")
    parser.add_argument(
        "--target-path",
        action="append",
        default=[],
        help="Repo-relative file or directory to scan instead of policy targets.",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report(
            repo_root=REPO_ROOT,
            policy_path=args.policy_path,
            target_paths=tuple(args.target_path or ()),
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
