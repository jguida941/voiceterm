"""Public helper surface for the multi-agent sync package."""

from __future__ import annotations

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

from .instruction_validation import (
    _validate_instruction_rows,
    _validate_signoff_rows,
)
from .collision_validation import _validate_mp_collisions
from .lane_lock_validation import _validate_lane_locks
from .lane_validation import (
    _cycle_complete_for_signoff,
    _extend_runtime_truth_errors,
    _validate_agent_names,
    _validate_agent_presence,
    _validate_lane_alignment,
    _warn_unknown_ledger_statuses,
)
from .master_lane_validation import _validate_master_lane_rows
from .markdown_tables import (
    _extract_table_rows,
    _normalize,
    _rows_by_key,
    _sorted_agents,
    _sorted_signers,
)
from .models import (
    MASTER_BOARD_HEADING,
    RUNBOOK_BOARD_HEADING,
    RUNBOOK_INSTRUCTION_HEADING,
    RUNBOOK_LEDGER_HEADING,
    RUNBOOK_SIGNOFF_HEADING,
    UTC_Z_PATTERN,
)
from .report import build_report
from .runtime_truth import evaluate_runtime_truth

MASTER_PLAN_PATH = REPO_ROOT / "dev/active/MASTER_PLAN.md"
RUNBOOK_PATH = REPO_ROOT / "dev/active/review_channel.md"


def _build_report() -> dict:
    return build_report(
        repo_root=REPO_ROOT,
        master_plan_path=MASTER_PLAN_PATH,
        runbook_path=RUNBOOK_PATH,
        extract_table_rows_fn=_extract_table_rows,
        evaluate_runtime_truth_fn=evaluate_runtime_truth,
    )


__all__ = [
    "MASTER_BOARD_HEADING",
    "MASTER_PLAN_PATH",
    "RUNBOOK_BOARD_HEADING",
    "RUNBOOK_INSTRUCTION_HEADING",
    "RUNBOOK_LEDGER_HEADING",
    "RUNBOOK_PATH",
    "RUNBOOK_SIGNOFF_HEADING",
    "UTC_Z_PATTERN",
    "_build_report",
    "_cycle_complete_for_signoff",
    "_extend_runtime_truth_errors",
    "_extract_table_rows",
    "_normalize",
    "_rows_by_key",
    "_sorted_agents",
    "_sorted_signers",
    "_validate_agent_names",
    "_validate_agent_presence",
    "_validate_instruction_rows",
    "_validate_lane_alignment",
    "_validate_lane_locks",
    "_validate_master_lane_rows",
    "_validate_mp_collisions",
    "_validate_signoff_rows",
    "_warn_unknown_ledger_statuses",
    "build_report",
    "evaluate_runtime_truth",
]
