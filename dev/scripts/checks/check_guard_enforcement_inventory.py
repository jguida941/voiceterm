#!/usr/bin/env python3
"""Guard against registered check scripts drifting out of real enforcement lanes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from check_bootstrap import emit_runtime_error, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - package-style fallback for tests
    from dev.scripts.checks.check_bootstrap import emit_runtime_error, utc_timestamp

from dev.scripts.devctl.bundle_registry import BUNDLE_REGISTRY
from dev.scripts.devctl.quality_policy import (
    resolve_ai_guard_checks,
    resolve_review_probe_checks,
)
from dev.scripts.devctl.script_catalog import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)

WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
DEVCTL_COMMAND_RE = re.compile(
    r"\bpython3\s+dev/scripts/devctl\.py\s+(?P<command>[a-z0-9][a-z0-9-]*)\b"
)

ENFORCEMENT_EXEMPTIONS = {
    "bootstrap": {
        "kind": "helper",
        "reason": "shared bootstrap helper imported by other checks, not a lane-owned guard",
    },
    "duplication_audit_support": {
        "kind": "helper",
        "reason": "support module for duplication audit heuristics, not a standalone guard entrypoint",
    },
    "duplication_audit": {
        "kind": "advisory",
        "reason": "local/reporting duplication audit surface; keep explicit until jscpd-backed policy graduates to a default lane",
    },
    "mutation_score": {
        "kind": "manual",
        "reason": "manual mutation-score command wrapper, not a default bundle/workflow gate",
    },
    "rustsec_policy": {
        "kind": "manual",
        "reason": "manual fallback policy gate owned by `devctl security`, not a default bundle/workflow lane",
    },
    "test_coverage_parity": {
        "kind": "advisory-backlog",
        "reason": "current repo still has untested check-script debt; promote once that backlog is burned down",
    },
}

INDIRECT_DEVCTL_COMMAND_SCRIPT_IDS = {
    "check": frozenset(
        {
            script_id
            for _step_name, script_id, _extra_args in (
                resolve_ai_guard_checks() + resolve_review_probe_checks()
            )
        }
    ),
    "probe-report": frozenset(
        {
            script_id
            for _step_name, script_id, _extra_args in resolve_review_probe_checks()
        }
    ),
    "docs-check": frozenset(
        {
            "active_plan_sync",
            "agents_bundle_render",
            "bundle_workflow_parity",
            "markdown_metadata_header",
            "multi_agent_sync",
            "workflow_shell_hygiene",
        }
    ),
}


def _workflow_texts(repo_root: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    workflows_dir = repo_root / ".github" / "workflows"
    for path in sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml")):
        if not path.is_file():
            continue
        texts[path.relative_to(repo_root).as_posix()] = path.read_text(encoding="utf-8")
    return texts


def _collect_devctl_commands(text: str) -> set[str]:
    return {match.group("command") for match in DEVCTL_COMMAND_RE.finditer(text)}


def _collect_direct_bundle_refs(relative_path: str) -> list[str]:
    refs: list[str] = []
    for bundle_name, commands in BUNDLE_REGISTRY.items():
        if any(relative_path in command for command in commands):
            refs.append(bundle_name)
    return refs


def _collect_direct_workflow_refs(
    relative_path: str,
    workflow_texts: dict[str, str],
) -> list[str]:
    return [
        workflow_path
        for workflow_path, text in workflow_texts.items()
        if relative_path in text
    ]


def _collect_indirect_bundle_refs(script_id: str) -> list[str]:
    refs: list[str] = []
    for bundle_name, commands in BUNDLE_REGISTRY.items():
        devctl_commands = {
            command_name
            for command in commands
            for command_name in _collect_devctl_commands(command)
        }
        if any(
            script_id in INDIRECT_DEVCTL_COMMAND_SCRIPT_IDS.get(command_name, frozenset())
            for command_name in devctl_commands
        ):
            refs.append(bundle_name)
    return refs


def _collect_indirect_workflow_refs(
    script_id: str,
    workflow_texts: dict[str, str],
) -> list[str]:
    refs: list[str] = []
    for workflow_path, text in workflow_texts.items():
        devctl_commands = _collect_devctl_commands(text)
        if any(
            script_id in INDIRECT_DEVCTL_COMMAND_SCRIPT_IDS.get(command_name, frozenset())
            for command_name in devctl_commands
        ):
            refs.append(workflow_path)
    return refs


def build_report(repo_root: Path = REPO_ROOT) -> dict:
    workflow_texts = _workflow_texts(repo_root)
    script_entries: list[dict] = []
    violations: list[dict] = []
    exempt_count = 0
    enforced_count = 0
    tracked_check_count = 0
    tracked_probe_count = 0

    tracked_scripts = [
        ("check", script_id, relative_path)
        for script_id, relative_path in sorted(CHECK_SCRIPT_RELATIVE_PATHS.items())
    ]
    tracked_scripts.extend(
        ("probe", script_id, relative_path)
        for script_id, relative_path in sorted(PROBE_SCRIPT_RELATIVE_PATHS.items())
    )

    for script_kind, script_id, relative_path in tracked_scripts:
        if script_kind == "check":
            tracked_check_count += 1
        else:
            tracked_probe_count += 1
        exemption = ENFORCEMENT_EXEMPTIONS.get(script_id)
        direct_bundle_refs = _collect_direct_bundle_refs(relative_path)
        direct_workflow_refs = _collect_direct_workflow_refs(relative_path, workflow_texts)
        indirect_bundle_refs = _collect_indirect_bundle_refs(script_id)
        indirect_workflow_refs = _collect_indirect_workflow_refs(script_id, workflow_texts)
        enforced = bool(
            direct_bundle_refs
            or direct_workflow_refs
            or indirect_bundle_refs
            or indirect_workflow_refs
        )
        entry = {
            "kind": script_kind,
            "script_id": script_id,
            "path": relative_path,
            "direct_bundle_refs": direct_bundle_refs,
            "direct_workflow_refs": direct_workflow_refs,
            "indirect_bundle_refs": indirect_bundle_refs,
            "indirect_workflow_refs": indirect_workflow_refs,
            "exemption": exemption,
            "enforced": enforced,
        }
        script_entries.append(entry)
        if exemption is not None:
            exempt_count += 1
            continue
        if enforced:
            enforced_count += 1
            continue
        violations.append(
            {
                "kind": script_kind,
                "script_id": script_id,
                "path": relative_path,
                "reason": "no bundle/workflow enforcement lane detected",
            }
        )

    checked_count = len(script_entries) - exempt_count
    return {
        "command": "check_guard_enforcement_inventory",
        "timestamp": utc_timestamp(),
        "ok": len(violations) == 0,
        "workflow_count": len(workflow_texts),
        "tracked_script_count": len(script_entries),
        "tracked_check_count": tracked_check_count,
        "tracked_probe_count": tracked_probe_count,
        "checked_script_count": checked_count,
        "exempt_script_count": exempt_count,
        "enforced_script_count": enforced_count,
        "scripts": script_entries,
        "violations": violations,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_guard_enforcement_inventory", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- workflows_scanned: {report['workflow_count']}")
    lines.append(f"- tracked_scripts: {report['tracked_script_count']}")
    lines.append(f"- tracked_checks: {report['tracked_check_count']}")
    lines.append(f"- tracked_probes: {report['tracked_probe_count']}")
    lines.append(f"- checked_scripts: {report['checked_script_count']}")
    lines.append(f"- enforced_scripts: {report['enforced_script_count']}")
    lines.append(f"- exempt_scripts: {report['exempt_script_count']}")
    lines.append(f"- violations: {len(report['violations'])}")

    exempt = [item for item in report["scripts"] if item["exemption"] is not None]
    if exempt:
        lines.append("")
        lines.append("## Exemptions")
        for item in exempt:
            exemption = item["exemption"]
            lines.append(
                f"- `{item['script_id']}`: {exemption['kind']} - {exemption['reason']}"
            )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: every registered quality script should either have a real "
            "bundle/workflow enforcement lane or an explicit exemption with rationale."
        )
        for item in report["violations"]:
            lines.append(
                f"- `{item['kind']}` `{item['script_id']}` -> `{item['path']}`"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        report = build_report()
    except OSError as exc:
        return emit_runtime_error(
            "check_guard_enforcement_inventory",
            args.format,
            str(exc),
        )

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
