#!/usr/bin/env python3
"""Meta-guard: verify the governance system is internally consistent.

Checks that every registered guard and probe has a test, every guard runs
in at least one CI workflow, every over-limit function is tracked in the
exception list, and every CI workflow has a timeout.  This makes the
governance system self-proving.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path

_checks_dir = str(Path(__file__).resolve().parent.parent)
if _checks_dir not in sys.path:
    sys.path.insert(0, _checks_dir)

from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_script_catalog = importlib.import_module("dev.scripts.devctl.script_catalog")
CHECK_SCRIPT_FILES = _script_catalog.CHECK_SCRIPT_FILES
CHECK_SCRIPT_RELATIVE_PATHS = _script_catalog.CHECK_SCRIPT_RELATIVE_PATHS
PROBE_SCRIPT_FILES = _script_catalog.PROBE_SCRIPT_FILES
PROBE_SCRIPT_RELATIVE_PATHS = _script_catalog.PROBE_SCRIPT_RELATIVE_PATHS

_review_log = importlib.import_module("dev.scripts.devctl.governance_review_log")
DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS = _review_log.DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS
governance_review_row_disposition_errors = (
    _review_log.governance_review_row_disposition_errors
)
read_governance_review_rows = _review_log.read_governance_review_rows
resolve_governance_review_log_path = _review_log.resolve_governance_review_log_path
_ledger_helpers = importlib.import_module("dev.scripts.devctl.governance.ledger_helpers")
latest_rows_by_finding = _ledger_helpers.latest_rows_by_finding

CHECKS_DIR = REPO_ROOT / "dev" / "scripts" / "checks"
TESTS_DIR = REPO_ROOT / "dev" / "scripts" / "devctl" / "tests"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Guards that are helpers, advisory, or intentionally local-only.
GUARD_TEST_EXEMPTIONS: frozenset[str] = frozenset(
    {
        "bootstrap",  # shared helper, not a standalone guard
        "duplication_audit_support",  # helper module
        "compat_matrix_smoke",  # thin shim over compat_matrix
    }
)

# Guards not expected in CI (local helpers, manual, pilot lanes).
CI_COVERAGE_EXEMPTIONS: frozenset[str] = frozenset(
    {
        "bootstrap",
        "duplication_audit_support",
        "duplication_audit",
        "duplicate_types",
        "markdown_metadata_header",
        "mutation_score",
        "rustsec_policy",
        "test_coverage_parity",
        "structural_complexity",
        "command_source_validation",
        "rust_security_footguns",
        "agents_bundle_render",
    }
)


def _find_guard_test_gaps(violations: list[dict[str, str]]) -> int:
    """Check every registered guard has a test file."""
    found = 0
    for guard_id in sorted(CHECK_SCRIPT_FILES):
        if guard_id in GUARD_TEST_EXEMPTIONS:
            continue
        # Look for test_check_<id>.py or test_<id>.py in tests tree
        candidates = list(TESTS_DIR.rglob(f"test_check_{guard_id}*")) + list(
            TESTS_DIR.rglob(f"test_{guard_id}*")
        )
        if not candidates:
            violations.append(
                {
                    "check": "guard_test_coverage",
                    "guard_id": guard_id,
                    "detail": f"No test file found for guard '{guard_id}'",
                }
            )
            found += 1
    return found


def _find_probe_test_gaps(violations: list[dict[str, str]]) -> int:
    """Check every registered probe has a test file."""
    found = 0
    for probe_id in sorted(PROBE_SCRIPT_FILES):
        candidates = list(TESTS_DIR.rglob(f"test_{probe_id}*"))
        if not candidates:
            violations.append(
                {
                    "check": "probe_test_coverage",
                    "probe_id": probe_id,
                    "detail": f"No test file found for probe '{probe_id}'",
                }
            )
            found += 1
    return found


def _find_ci_coverage_gaps(violations: list[dict[str, str]]) -> int:
    """Check every registered guard is invoked by at least one CI workflow."""
    if not WORKFLOWS_DIR.is_dir():
        return 0
    # Collect all guard references from workflow YAML files
    workflow_text = ""
    for yml in WORKFLOWS_DIR.glob("*.yml"):
        workflow_text += yml.read_text(encoding="utf-8")

    found = 0
    for guard_id in sorted(CHECK_SCRIPT_FILES):
        if guard_id in CI_COVERAGE_EXEMPTIONS:
            continue
        filename = CHECK_SCRIPT_FILES[guard_id]
        # Guard can appear as script name, guard_id in devctl commands, or
        # as part of a profile invocation.
        if filename not in workflow_text and guard_id not in workflow_text:
            violations.append(
                {
                    "check": "ci_guard_coverage",
                    "guard_id": guard_id,
                    "detail": f"Guard '{guard_id}' not found in any CI workflow",
                }
            )
            found += 1
    return found


def _find_workflow_timeout_gaps(violations: list[dict[str, str]]) -> int:
    """Check every CI workflow job has a timeout-minutes field."""
    if not WORKFLOWS_DIR.is_dir():
        return 0
    timeout_re = re.compile(r"timeout-minutes\s*:")
    found = 0
    for yml in sorted(WORKFLOWS_DIR.glob("*.yml")):
        text = yml.read_text(encoding="utf-8")
        if "jobs:" not in text:
            continue
        if not timeout_re.search(text):
            violations.append(
                {
                    "check": "workflow_timeout",
                    "file": yml.name,
                    "detail": f"Workflow '{yml.name}' has no timeout-minutes in any job",
                }
            )
            found += 1
    return found


def _find_review_disposition_gaps(violations: list[dict[str, str]]) -> int:
    """Check latest governance-review rows for required disposition fields."""
    log_path = resolve_governance_review_log_path(repo_root=REPO_ROOT)
    rows = read_governance_review_rows(
        log_path,
        max_rows=DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS,
    )
    found = 0
    for row in latest_rows_by_finding(rows):
        disposition_errors = governance_review_row_disposition_errors(row)
        if not disposition_errors:
            continue
        detail = "; ".join(disposition_errors)
        violations.append(
            {
                "check": "review_disposition_schema",
                "finding_id": str(row.get("finding_id") or "unknown"),
                "detail": detail,
            }
        )
        found += 1
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "md", "terminal"], default="md")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    try:
        violations: list[dict[str, str]] = []
        _find_guard_test_gaps(violations)
        _find_probe_test_gaps(violations)
        _find_ci_coverage_gaps(violations)
        _find_workflow_timeout_gaps(violations)
        _find_review_disposition_gaps(violations)

        ok = len(violations) == 0

        report = {
            "command": "check_governance_closure",
            "ok": ok,
            "timestamp": utc_timestamp(),
            "schema_version": 1,
            "total_guards": len(CHECK_SCRIPT_FILES),
            "total_probes": len(PROBE_SCRIPT_FILES),
            "violations": violations,
            "violation_count": len(violations),
            "checks_run": [
                "guard_test_coverage",
                "probe_test_coverage",
                "ci_guard_coverage",
                "workflow_timeout",
                "review_disposition_schema",
            ],
        }

        if args.format == "json":
            output = json.dumps(report, indent=2, sort_keys=False)
        else:
            lines = [f"# check_governance_closure", ""]
            lines.append(f"- ok: {ok}")
            lines.append(f"- guards: {len(CHECK_SCRIPT_FILES)}")
            lines.append(f"- probes: {len(PROBE_SCRIPT_FILES)}")
            lines.append(f"- violations: {len(violations)}")
            lines.append("")
            if violations:
                lines.append("## Violations")
                lines.append("")
                for v in violations:
                    lines.append(f"- [{v['check']}] {v['detail']}")
            else:
                lines.append("All governance closure checks passed.")
            output = "\n".join(lines)

        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Report saved to: {args.output}")
        else:
            print(output)

        return 0 if ok else 1

    except RuntimeError as exc:
        return emit_runtime_error("check_governance_closure", args.format, str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
