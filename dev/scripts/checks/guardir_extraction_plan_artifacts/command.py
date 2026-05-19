#!/usr/bin/env python3
"""Guard checked-off GuardIR extraction-plan artifact claims."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

_BOOT_ROOT = str(Path(__file__).resolve().parents[4])
if _BOOT_ROOT not in sys.path:
    sys.path.insert(0, _BOOT_ROOT)

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

PLAN_REL_PATH = Path("dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md")


def build_report(*, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    plan_path = repo_root / PLAN_REL_PATH
    violations: list[dict[str, object]] = []
    plan_text = ""
    if not plan_path.is_file():
        violations.append(
            {
                "check": "canonical_plan_missing",
                "path": PLAN_REL_PATH.as_posix(),
                "detail": "Canonical GuardIR extraction plan is missing.",
            }
        )
    else:
        plan_text = plan_path.read_text(encoding="utf-8")
    checked = _phase_06_checked_artifacts(plan_text)
    for artifact in checked:
        path = repo_root / artifact["path"]
        if not path.is_file():
            violations.append(
                {
                    "check": "checked_plan_artifact_missing",
                    "path": artifact["path"],
                    "claim": artifact["claim"],
                    "detail": (
                        "Extraction plan marks this Phase 0.6 artifact green, "
                        "but the repo artifact is missing."
                    ),
                }
            )
            continue
        shape_error = artifact["shape"](path)
        if shape_error:
            violations.append(
                {
                    "check": "checked_plan_artifact_invalid",
                    "path": artifact["path"],
                    "claim": artifact["claim"],
                    "detail": shape_error,
                }
            )
    return {
        "command": "check_guardir_extraction_plan_artifacts",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "plan_path": PLAN_REL_PATH.as_posix(),
        "checked_artifact_count": len(checked),
        "violations": violations,
    }


def _phase_06_checked_artifacts(plan_text: str) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = [
        _artifact(
            claim="TopologyHardcodeInventory emitted",
            trigger="✅ `TopologyHardcodeInventory` emitted",
            path="dev/state/topology_hardcode_inventory.jsonl",
            shape=_jsonl_contract("TopologyHardcodeInventory"),
        ),
        _artifact(
            claim="provider-hardcode guard exists",
            trigger='✅ Guard rejects NEW `"codex"`/`"claude"`/`"cursor"` literals',
            path="dev/scripts/checks/check_no_new_hardcoded_provider_authority.py",
            shape=_python_script,
        ),
        _artifact(
            claim="count-coupled topology guard exists",
            trigger="✅ Guard rejects NEW count-coupled `ReviewerMode` enum members",
            path="dev/scripts/checks/check_no_new_topology_count_coupling.py",
            shape=_python_script,
        ),
        _artifact(
            claim="cognitive role fleet config scaffold exists",
            trigger="✅ `dev/config/cognitive_role_fleet.json` skeleton exists",
            path="dev/config/cognitive_role_fleet.json",
            shape=_json_contract("CognitiveRoleFleetConfig"),
        ),
    ]
    return [
        artifact for artifact in candidates if str(artifact["trigger"]) in plan_text
    ]


def _artifact(
    *,
    claim: str,
    trigger: str,
    path: str,
    shape: Callable[[Path], str],
) -> dict[str, object]:
    return {"claim": claim, "trigger": trigger, "path": path, "shape": shape}


def _python_script(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if "main" not in text:
        return "Python guard script does not expose or delegate a main entrypoint."
    return ""


def _json_contract(expected_contract_id: str) -> Callable[[Path], str]:
    def check(path: Path) -> str:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return f"Invalid JSON: {exc}"
        if not isinstance(payload, dict):
            return "Expected a JSON object."
        if payload.get("contract_id") != expected_contract_id:
            return f"Expected contract_id={expected_contract_id!r}."
        return ""

    return check


def _jsonl_contract(expected_contract_id: str) -> Callable[[Path], str]:
    def check(path: Path) -> str:
        rows = 0
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            rows += 1
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                return f"Invalid JSONL at line {line_no}: {exc}"
            if payload.get("contract_id") != expected_contract_id:
                return f"Line {line_no} expected contract_id={expected_contract_id!r}."
        if rows == 0:
            return "Expected at least one JSONL inventory row."
        return ""

    return check


def _render_md(report: dict[str, object]) -> str:
    violations = report.get("violations")
    rows = violations if isinstance(violations, list) else []
    lines = ["# check_guardir_extraction_plan_artifacts", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- plan_path: {report['plan_path']}")
    lines.append(f"- checked_artifact_count: {report['checked_artifact_count']}")
    lines.append(f"- violation_count: {len(rows)}")
    if rows:
        lines.append("")
        lines.append("## Violations")
        for row in rows:
            if isinstance(row, dict):
                lines.append(
                    f"- `{row.get('path')}` {row.get('check')}: {row.get('detail')}"
                )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
