#!/usr/bin/env python3
"""Fail when a newly added guard is not a complete executable feature."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence

try:
    from check_bootstrap import REPO_ROOT, run_format_check, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        run_format_check,
        utc_timestamp,
    )


if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from feature_completion_support import (
        FeatureCompletionSupport as Support,
        FeatureCompletionViolation,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.feature_completion_support import (
        FeatureCompletionSupport as Support,
        FeatureCompletionViolation,
    )

COMMAND = "check_feature_completion"
CONTRACT_ID = "FeatureCompletionGuard"


def build_report(
    *,
    git_status_output: str | None = None,
    registered_check_paths: frozenset[str] | None = None,
    bundled_check_paths: frozenset[str] | None = None,
    quality_check_paths: frozenset[str] | None = None,
    router_mapped_paths: frozenset[str] | None = None,
    existing_paths: frozenset[str] | None = None,
    source_text_by_path: Mapping[str, str] | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    status_output = git_status_output if git_status_output is not None else Support.git_status_output(warnings)
    candidate_paths = tuple(
        path for path in Support.new_or_added_paths(status_output) if Support.is_check_entrypoint(path)
    )
    registered = (
        registered_check_paths
        if registered_check_paths is not None
        else Support.registered_check_paths()
    )
    bundled = bundled_check_paths if bundled_check_paths is not None else _bundled_check_paths()
    quality = (
        quality_check_paths if quality_check_paths is not None else Support.quality_check_paths()
    )
    router_mapped = (
        router_mapped_paths if router_mapped_paths is not None else Support.router_mapped_paths()
    )
    existing = existing_paths if existing_paths is not None else Support.existing_paths(candidate_paths)
    source_text = dict(source_text_by_path or {})

    violations: list[FeatureCompletionViolation] = []
    for path in candidate_paths:
        violations.extend(
            Support.check_guard_completion(
                path=path,
                registered=registered,
                bundled=bundled,
                quality=quality,
                router_mapped=router_mapped,
                existing=existing,
                source_text=source_text,
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "candidate_count": len(candidate_paths),
        "candidate_paths": list(candidate_paths),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _bundled_check_paths() -> frozenset[str]:
    return Support.bundled_check_paths()


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- candidate_count: {report.get('candidate_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(
                    f"- {violation.get('path')}: {violation.get('reason')} "
                    f"({violation.get('detail')})"
                )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    return run_format_check(argv=argv, command=COMMAND, description=__doc__ or COMMAND, build_report=build_report, render_markdown=render_markdown)


if __name__ == "__main__":
    raise SystemExit(main())
