"""Dogfood governance defaults and target-resolution helpers."""

from __future__ import annotations

import importlib
from pathlib import Path

from ..config import get_repo_root
from ..governance.ledger_helpers import optional_text
from ..governance.script_catalog_registry import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)
from ..governance.system_catalog import build_system_catalog
from ..governance_review.models import GovernanceReviewInput
from .dogfood_models import DogfoodRecord

DOGFOOD_ROLE_DEFAULT_PATHS = {
    "reviewer": "dev/scripts/devctl/runtime/reviewer_runtime_models.py",
    "implementer": "dev/scripts/devctl/commands/governance/session_resume.py",
    "dashboard": "dev/scripts/devctl/commands/dashboard.py",
}


def build_dogfood_governance_input(
    record: DogfoodRecord,
    *,
    finding_id: str | None = None,
    check_id: str | None = None,
    file_path: str | None = None,
    line: int | None = None,
    severity: str | None = None,
    risk_type: str | None = None,
    source_command: str | None = None,
    notes: str | None = None,
    finding_type: str | None = None,
    finding_class: str | None = None,
    recurrence_risk: str | None = None,
    prevention_surface: str | None = None,
    waiver_reason: str | None = None,
    verdict: str | None = None,
    repo_root: Path | None = None,
) -> GovernanceReviewInput:
    """Build one dogfood-scoped governance-review input with sane defaults."""
    resolved_path = optional_text(file_path) or resolve_dogfood_target_path(
        target_kind=record.target_kind,
        target_id=record.target_id,
        repo_root=repo_root,
    )
    if not resolved_path:
        raise ValueError(
            "Unable to resolve a default governance path for this dogfood target. "
            "Provide --finding-path."
        )
    notes = _merge_campaign_note(
        optional_text(notes) or optional_text(record.notes),
        record=record,
    )
    return GovernanceReviewInput(
        finding_id=optional_text(finding_id),
        signal_type="dogfood",
        check_id=optional_text(check_id)
        or f"dogfood.{record.target_kind}.{record.target_id}",
        verdict=optional_text(verdict) or default_dogfood_governance_verdict(record.status),
        file_path=resolved_path,
        line=line,
        severity=optional_text(severity),
        risk_type=optional_text(risk_type),
        source_command=optional_text(source_command)
        or optional_text(record.source_command)
        or "python3 dev/scripts/devctl.py dogfood --record --dev-mode",
        repo_name=record.repo_name,
        repo_path=record.repo_path,
        notes=notes,
        finding_type=optional_text(finding_type),
        finding_class=optional_text(finding_class)
        or default_dogfood_finding_class(record),
        recurrence_risk=optional_text(recurrence_risk) or "recurring",
        prevention_surface=optional_text(prevention_surface)
        or default_dogfood_prevention_surface(record),
        waiver_reason=optional_text(waiver_reason),
    )


def resolve_dogfood_target_path(
    *,
    target_kind: str,
    target_id: str,
    repo_root: Path | None = None,
) -> str:
    """Resolve the default code path associated with one dogfood target."""
    effective_root = (repo_root or get_repo_root() or Path(".")).resolve()
    if target_kind == "guard":
        return CHECK_SCRIPT_RELATIVE_PATHS.get(target_id, "")
    if target_kind == "probe":
        return PROBE_SCRIPT_RELATIVE_PATHS.get(target_id, "")
    if target_kind == "role":
        return DOGFOOD_ROLE_DEFAULT_PATHS.get(target_id, "")
    if target_kind != "command":
        return ""
    catalog = build_system_catalog(repo_root=effective_root)
    command = next((entry for entry in catalog.commands if entry.name == target_id), None)
    if command is None or not command.handler_module:
        return ""
    return _module_relative_path(command.handler_module, repo_root=effective_root)


def default_dogfood_governance_verdict(status: str) -> str:
    if status == "passed":
        return "fixed"
    if status == "skipped":
        return "deferred"
    return "confirmed_issue"


def default_dogfood_finding_class(record: DogfoodRecord) -> str:
    if record.status == "blocked":
        return "workflow_gap"
    if record.target_kind == "probe":
        return "rule_quality"
    return "local_defect"


def default_dogfood_prevention_surface(record: DogfoodRecord) -> str:
    if record.target_kind == "guard":
        return "guard"
    if record.target_kind == "probe":
        return "probe"
    if record.target_kind == "role" and record.status == "blocked":
        return "authority_rule"
    return "contract"


def _module_relative_path(module_name: str, *, repo_root: Path) -> str:
    module = importlib.import_module(module_name)
    module_file = getattr(module, "__file__", "")
    if not module_file:
        return ""
    module_path = Path(module_file).resolve()
    try:
        return str(module_path.relative_to(repo_root))
    except ValueError:
        return ""


def _merge_campaign_note(base_notes: str | None, *, record: DogfoodRecord) -> str | None:
    campaign_note = _campaign_note(record)
    if not base_notes:
        return campaign_note
    if not campaign_note:
        return base_notes
    return f"{base_notes}\n{campaign_note}"


def _campaign_note(record: DogfoodRecord) -> str | None:
    parts: list[str] = []
    if record.campaign_id:
        parts.append(f"campaign_id={record.campaign_id}")
    if record.scenario_id:
        parts.append(f"scenario_id={record.scenario_id}")
    if record.repo_scope:
        parts.append(f"repo_scope={record.repo_scope}")
    if record.repo_label:
        parts.append(f"repo_label={record.repo_label}")
    if record.repo_path:
        parts.append(f"repo_path={record.repo_path}")
    if record.topology:
        parts.append(f"topology={record.topology}")
    if record.lane_role:
        parts.append(f"lane_role={record.lane_role}")
    if record.live_run_refs:
        parts.append(f"live_run_refs=[{', '.join(record.live_run_refs)}]")
    if record.governance_finding_ids:
        parts.append(
            f"governance_finding_ids=[{', '.join(record.governance_finding_ids)}]"
        )
    return "; ".join(parts) if parts else None
