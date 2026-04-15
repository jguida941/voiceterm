"""Command-side governance closeout helpers for ``devctl dogfood``."""

from __future__ import annotations

from pathlib import Path

from ...config import get_repo_root
from ...governance.guard_promotion_queue import (
    append_guard_promotion_candidate_from_review,
    resolve_guard_promotion_queue_path,
)
from ...governance_review_log import (
    build_governance_review_report,
    resolve_governance_review_log_path,
    resolve_governance_review_summary_root,
)
from ...governance_review_render import write_governance_review_summary
from ...runtime.dogfood_governance import (
    build_dogfood_governance_input,
    default_dogfood_governance_verdict,
    resolve_dogfood_target_path,
)
from ...runtime.dogfood_models import DogfoodRecord
from ...runtime.finding_backlog import record_finding_backlog_row


def governance_validation_error(args) -> str | None:
    """Return a user-facing validation error for dogfood governance closeout."""
    if not has_governance_closeout(args):
        return None
    if bool(getattr(args, "record_governance", False)) and not bool(
        getattr(args, "record", False)
    ):
        return "`devctl dogfood --record-governance` requires `--record`."
    if dogfood_governance_verdict(args) is None:
        return "Unable to derive a governance-review verdict from this dogfood status."
    target_kind = str(getattr(args, "target_kind", "") or "").strip()
    target_id = str(getattr(args, "target_id", "") or "").strip()
    if (
        not str(getattr(args, "finding_path", "") or "").strip()
        and target_kind
        and target_id
        and not resolve_dogfood_target_path(
            target_kind=target_kind,
            target_id=target_id,
            repo_root=get_repo_root(),
        )
    ):
        return (
            "Unable to resolve a default governance path for this dogfood target. "
            "Use --finding-path."
        )
    return None


def maybe_record_governance_closeout(
    args,
    recorded_row: DogfoodRecord,
    *,
    governance_log_path: Path | None = None,
    governance_summary_root: Path | None = None,
    promotion_queue_path: Path | None = None,
) -> tuple[dict[str, object] | None, dict[str, str] | None, dict[str, object] | None]:
    """Write the linked governance-review row when this dogfood run requests it."""
    if not has_governance_closeout(args):
        return None, None, None

    governance_log_path = governance_log_path or resolve_governance_review_log_path()
    governance_summary_root = (
        governance_summary_root or resolve_governance_review_summary_root()
    )
    promotion_queue_path = promotion_queue_path or resolve_guard_promotion_queue_path(None)
    source_command = str(getattr(args, "source_command", "") or "").strip()
    if not source_command:
        source_command = (
            "python3 dev/scripts/devctl.py dogfood --record --dev-mode "
            f"--target-kind {recorded_row.target_kind} "
            f"--target-id {recorded_row.target_id}"
        )
    write_result = record_finding_backlog_row(
        review_input=build_dogfood_governance_input(
            recorded_row,
            finding_id=getattr(args, "finding_id", None),
            check_id=getattr(args, "governance_check_id", None),
            file_path=getattr(args, "finding_path", None),
            line=getattr(args, "finding_line", None),
            severity=getattr(args, "severity", None),
            risk_type=getattr(args, "risk_type", None),
            source_command=source_command,
            notes=getattr(args, "notes", None),
            finding_type=getattr(args, "finding_type", None),
            finding_class=getattr(args, "finding_class", None),
            recurrence_risk=getattr(args, "recurrence_risk", None),
            prevention_surface=getattr(args, "prevention_surface", None),
            waiver_reason=getattr(args, "waiver_reason", None),
            verdict=dogfood_governance_verdict(args),
            repo_root=get_repo_root(),
        ),
        repo_root=get_repo_root(),
        governance=None,
        log_path=governance_log_path,
    )
    promotion_candidate = append_guard_promotion_candidate_from_review(
        write_result.row,
        queue_path=promotion_queue_path,
    )
    governance_report = build_governance_review_report(
        log_path=governance_log_path,
        max_rows=5000,
    )
    governance_paths = write_governance_review_summary(
        governance_report,
        summary_root=governance_summary_root,
    )
    return write_result.row, governance_paths, promotion_candidate


def has_governance_closeout(args) -> bool:
    """Return whether this dogfood invocation should touch governance-review."""
    scalar_fields = (
        "finding_path",
        "finding_id",
        "governance_check_id",
        "governance_verdict",
        "finding_class",
        "recurrence_risk",
        "prevention_surface",
        "finding_type",
        "severity",
        "risk_type",
        "waiver_reason",
    )
    if bool(getattr(args, "record_governance", False)):
        return True
    if any(str(getattr(args, field_name, "") or "").strip() for field_name in scalar_fields):
        return True
    return getattr(args, "finding_line", None) is not None


def dogfood_governance_verdict(args) -> str | None:
    """Return the effective governance-review verdict for this dogfood row."""
    override = str(getattr(args, "governance_verdict", "") or "").strip()
    if override:
        return override
    return default_dogfood_governance_verdict(
        str(getattr(args, "status", "") or "").strip()
    )
