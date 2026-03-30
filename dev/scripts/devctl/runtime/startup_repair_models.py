"""Typed models for startup repair classification and action results."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class StartupRepairIssue:
    """One classified startup issue."""

    issue_id: str
    issue_class: str
    source: str
    owner: str
    summary: str
    detail: str = ""
    recommended_command: str = ""
    repairable: bool = False
    safe_to_apply_now: bool = False
    apply_action: str = ""
    changes_tracked_state: bool = False
    blocked_by_approval_boundary: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StartupRepairActionRecord:
    """One attempted safe repair action."""

    action_id: str
    ok: bool
    exit_code: int
    detail: str = ""
    changed_tracked_state: bool = False
    resulting_attention_status: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StartupRepairResult:
    """Typed report from one startup repair run."""

    schema_version: int = 1
    contract_id: str = "StartupRepairResult"
    repo_name: str = ""
    current_branch: str = ""
    startup_receipt_path: str = ""
    advisory_action: str = ""
    advisory_reason: str = ""
    reviewer_mode: str = "single_agent"
    bridge_active: bool = False
    startup_authority_ok: bool = False
    checkpoint_required: bool = False
    safe_to_continue_editing: bool = True
    review_attention_status: str = "inactive"
    review_attention_owner: str = "system"
    review_attention_summary: str = ""
    issue_count: int = 0
    repairable_issue_count: int = 0
    safe_fix_available_count: int = 0
    issues: tuple[StartupRepairIssue, ...] = ()
    applied_actions: tuple[StartupRepairActionRecord, ...] = ()
    next_action: str = "healthy"
    next_reason: str = ""
    next_command: str = ""
    ok: bool = True

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["issues"] = [issue.to_dict() for issue in self.issues]
        payload["applied_actions"] = [
            action.to_dict() for action in self.applied_actions
        ]
        return payload
