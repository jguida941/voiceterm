#!/usr/bin/env python3
"""Fail when AUDIT_STATUS.md still claims completed Phase 3/4 work is open."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PHASE4_TEST_NAMES = (
    "test_phase4_clean_path_surface_snapshot_alignment",
    "test_phase4_rescue_path_recovers_doctor_health_and_snapshot",
    "test_phase4_surface_convergence_across_startup_push_doctor_and_bridge_projection",
    "test_phase4_remote_session_commit_approval_stays_generation_bound",
)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    audit_text: str | None = None,
    code_signals: dict[str, bool] | None = None,
) -> dict[str, object]:
    text = (
        audit_text
        if audit_text is not None
        else (repo_root / "AUDIT_STATUS.md").read_text(encoding="utf-8")
    )
    signals = code_signals or _detect_code_signals(repo_root)
    stale_rows: list[str] = []
    for signal, marker in (
        ("contract_ownership_map", "| D | contract_ownership_map in StartupContext | NOT CODED |"),
        ("audit_sync_guard", "| F | Audit file auto-sync guard | NOT CODED |"),
        ("surface_consistency_guard", "| I | Cross-surface consistency proof | NOT CODED |"),
        ("phase4_clean_path", "| K | Prove clean end-to-end path | NOT TESTED |"),
        ("phase4_rescue_path", "| L | Prove rescue end-to-end path | NOT TESTED |"),
    ):
        if signals.get(signal) and marker in text:
            stale_rows.append(marker)
    if signals.get("phase4_all") and (
        "remaining tracked follow-up is Phase 3 surface-ownership / generation consistency work"
        in text
    ):
        stale_rows.append("Session Resume still says Phase 3 follow-up is remaining.")
    return {
        "command": "check_audit_status_sync",
        "ok": not stale_rows,
        "code_signals": signals,
        "stale_rows": stale_rows,
    }


def _detect_code_signals(repo_root: Path) -> dict[str, bool]:
    startup_text = (repo_root / "dev/scripts/devctl/runtime/startup_context.py").read_text(
        encoding="utf-8"
    )
    phase4_tests_text = (
        repo_root / "dev/scripts/devctl/tests/runtime/test_remote_commit_pipeline_phases34.py"
    ).read_text(encoding="utf-8")
    phase4_signals = {name: name in phase4_tests_text for name in PHASE4_TEST_NAMES}
    return {
        "contract_ownership_map": "contract_ownership_map" in startup_text,
        "surface_consistency_guard": (
            repo_root / "dev/scripts/checks/check_review_surface_consistency.py"
        ).exists(),
        "audit_sync_guard": (
            repo_root / "dev/scripts/checks/check_audit_status_sync.py"
        ).exists(),
        "phase4_clean_path": phase4_signals[PHASE4_TEST_NAMES[0]],
        "phase4_rescue_path": phase4_signals[PHASE4_TEST_NAMES[1]],
        "phase4_convergence": phase4_signals[PHASE4_TEST_NAMES[2]],
        "phase4_remote_session": phase4_signals[PHASE4_TEST_NAMES[3]],
        "phase4_all": all(phase4_signals.values()),
    }


def _render_report(report: dict[str, object]) -> str:
    lines = ["# check_audit_status_sync", ""]
    lines.append(f"- ok: {report.get('ok')}")
    for key, value in sorted((report.get("code_signals") or {}).items()):
        lines.append(f"- {key}: {value}")
    stale_rows = report.get("stale_rows") or []
    if stale_rows:
        lines.append("")
        lines.append("## Stale audit rows")
        for row in stale_rows:
            lines.append(f"- {row}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_report(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
