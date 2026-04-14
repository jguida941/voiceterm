"""Core startup receipt models and path helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import get_repo_root
from .authority_snapshot import AuthoritySnapshot
from .governance_scan import scan_repo_governance_safely
from .startup_receipt_freshness import (
    IMPLEMENTATION_STRICT_STARTUP_INTENT,
    startup_receipt_problems_for_intent,
)

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance

_RECEIPT_ARTIFACT_RELATIVE_PATH = Path("startup/latest/receipt.json")


@dataclass(frozen=True, slots=True)
class StartupReceipt:
    """Persistent proof that startup-context ran for the current HEAD."""

    schema_version: int = 1
    contract_id: str = "StartupReceipt"
    generated_at_utc: str = ""
    repo_name: str = ""
    current_branch: str = ""
    head_commit_sha: str = ""
    receipt_intent_scope: str = IMPLEMENTATION_STRICT_STARTUP_INTENT
    reviewer_loop_blocked: bool = False
    implementation_block_reason: str = ""
    review_gate_allows_push: bool = False
    receipt_source_tree_head_sha: str = ""
    receipt_admin_drift_allowed: bool = False
    advisory_action: str = ""
    advisory_reason: str = ""
    recommended_action: str = ""
    push_action: str = ""
    push_reason: str = ""
    push_eligible_now: bool = False
    push_next_step_summary: str = ""
    push_next_step_command: str = ""
    publication_backlog_state: str = "none"
    publication_backlog_summary: str = ""
    publication_backlog_recommended: bool = False
    publication_backlog_urgent: bool = False
    publication_guidance: str = ""
    attention_revision: str = ""
    staged_path_count: int = 0
    unstaged_path_count: int = 0
    checkpoint_required: bool = False
    safe_to_continue_editing: bool = True
    startup_authority_ok: bool = False
    startup_authority_errors: tuple[str, ...] = ()
    startup_authority_warnings: tuple[str, ...] = ()
    authority_snapshot: AuthoritySnapshot | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["startup_authority_errors"] = list(self.startup_authority_errors)
        payload["startup_authority_warnings"] = list(self.startup_authority_warnings)
        if self.authority_snapshot is not None:
            payload["authority_snapshot"] = self.authority_snapshot.to_dict()
        else:
            payload.pop("authority_snapshot", None)
        return payload


def startup_receipt_path(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path:
    """Return the canonical startup receipt path."""
    resolved_root = repo_root or get_repo_root()
    return resolved_root / startup_receipt_relative_path(
        governance=governance,
        repo_root=resolved_root,
    )


def startup_receipt_relative_path(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path:
    """Return the repo-relative startup receipt path."""
    reports_root = _reports_root_relative_path(
        governance=governance,
        repo_root=repo_root,
    )
    return reports_root / _RECEIPT_ARTIFACT_RELATIVE_PATH


def startup_receipt_problems(
    receipt: StartupReceipt | None,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Return receipt freshness problems for launcher/mutation gates."""
    return startup_receipt_problems_for_intent(
        receipt,
        repo_root=repo_root,
        intent=IMPLEMENTATION_STRICT_STARTUP_INTENT,
    )


def _reports_root_relative_path(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path:
    configured = _configured_reports_root(governance=governance, repo_root=repo_root)
    if configured is not None:
        return configured
    from . import startup_receipt as startup_receipt_module

    configured_path_config = getattr(
        startup_receipt_module,
        "configured_path_config",
        None,
    )
    if callable(configured_path_config):
        repo_pack = configured_path_config()
        if repo_pack is not None:
            return Path(repo_pack.reports_root_rel)
    return Path()


def _configured_reports_root(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path | None:
    reports_root = ""
    if governance is not None:
        reports_root = str(governance.path_roots.reports or "").strip()
    if not reports_root:
        scanned = scan_repo_governance_safely(repo_root or get_repo_root())
        if scanned is not None:
            reports_root = str(scanned.path_roots.reports or "").strip()
    if not reports_root:
        return None
    return Path(reports_root)
