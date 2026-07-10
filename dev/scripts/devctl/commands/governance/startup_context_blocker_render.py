"""Startup-context blocker-table projection through the shared renderer.

Kept as a sibling of ``startup_context_render`` so the core markdown
renderer stays under the ``code_shape`` soft limit while the MP-381
shared-renderer wiring still lives next door. This module is the first
production consumer of ``startup_summary_to_violations``: it projects
blocking startup-context conditions (``advisory_action``,
``reviewer_gate.implementation_blocked``, ``push_decision.action``)
through the shared ``CheckResult`` / ``ViolationRecord`` family and
``render_check_result_md`` so startup-context blockers render through
the same contract family as checks, probes, and governance-review.

The output is intentionally empty when nothing is blocking, so healthy
startup states render no blocker section rather than a synthetic
"all clear" table.
"""

from __future__ import annotations

from ...runtime.check_result_models import (
    CHECK_RESULT_CONTRACT_ID,
    CHECK_RESULT_SCHEMA_VERSION,
    CheckResult,
)
from ...runtime.check_result_render import render_check_result_md
from ...runtime.startup_summary_violations import startup_summary_to_violations
from ...time_utils import utc_timestamp


def append_blocker_table(lines: list[str], ctx_dict: dict) -> None:
    """Append a shared-renderer blocker table when startup has any blockers.

    Projects blocking startup-context conditions through the shared
    ``startup_summary_to_violations`` adapter into a step-less
    ``CheckResult`` envelope and renders that envelope with
    ``render_check_result_md``. Callers own the enclosing ``## Blockers``
    section header so the rendered ``## Violation Detail`` subtable
    flows beneath it. No-op when no blocking condition is present.
    """
    violations = startup_summary_to_violations(ctx_dict)
    if not violations:
        return
    result = CheckResult(
        schema_version=CHECK_RESULT_SCHEMA_VERSION,
        contract_id=CHECK_RESULT_CONTRACT_ID,
        command="startup-context",
        timestamp=utc_timestamp(),
        success=False,
        total=0,
        passed=0,
        failed=len(violations),
        skipped=0,
        steps=(),
        violations=violations,
    )
    lines.append("## Blockers")
    lines.append("")
    lines.append(render_check_result_md(result))
    lines.append("")


__all__ = ["append_blocker_table"]
