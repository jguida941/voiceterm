"""Receipt helpers for the typed startup-context gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
from typing import TYPE_CHECKING, Any

from ..config import get_repo_root
from ..repo_packs import active_path_config
from ..time_utils import utc_timestamp

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .startup_context import StartupContext

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
    advisory_action: str = ""
    advisory_reason: str = ""
    recommended_action: str = ""
    checkpoint_required: bool = False
    safe_to_continue_editing: bool = True
    startup_authority_ok: bool = False
    startup_authority_errors: tuple[str, ...] = ()
    startup_authority_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["startup_authority_errors"] = list(self.startup_authority_errors)
        payload["startup_authority_warnings"] = list(self.startup_authority_warnings)
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


def build_startup_receipt(
    ctx: "StartupContext",
    *,
    authority_report: dict[str, Any],
    repo_root: Path | None = None,
) -> StartupReceipt:
    """Build the persistent receipt written by startup-context."""
    resolved_root = repo_root or get_repo_root()
    governance = ctx.governance
    repo_identity = governance.repo_identity if governance is not None else None
    push = governance.push_enforcement if governance is not None else None
    authority_errors = tuple(
        str(row).strip()
        for row in authority_report.get("errors", ())
        if str(row).strip()
    )
    authority_warnings = tuple(
        str(row).strip()
        for row in authority_report.get("warnings", ())
        if str(row).strip()
    )
    return StartupReceipt(
        generated_at_utc=utc_timestamp(),
        repo_name=repo_identity.repo_name if repo_identity is not None else "",
        current_branch=repo_identity.current_branch if repo_identity is not None else "",
        head_commit_sha=_git_stdout(resolved_root, "rev-parse", "HEAD"),
        advisory_action=str(ctx.advisory_action or "").strip(),
        advisory_reason=str(ctx.advisory_reason or "").strip(),
        recommended_action=(
            str(push.recommended_action or "").strip() if push is not None else ""
        ),
        checkpoint_required=bool(push.checkpoint_required) if push is not None else False,
        safe_to_continue_editing=(
            bool(push.safe_to_continue_editing) if push is not None else True
        ),
        startup_authority_ok=bool(authority_report.get("ok", False)),
        startup_authority_errors=authority_errors,
        startup_authority_warnings=authority_warnings,
    )


def write_startup_receipt(
    receipt: StartupReceipt,
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path:
    """Persist one startup receipt to the managed startup artifact path."""
    path = startup_receipt_path(
        governance=governance,
        repo_root=repo_root,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
    return path


def load_startup_receipt(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> StartupReceipt | None:
    """Load the latest startup receipt when it exists."""
    path = startup_receipt_path(governance=governance, repo_root=repo_root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return startup_receipt_from_mapping(payload)


def startup_receipt_from_mapping(payload: dict[str, object]) -> StartupReceipt:
    """Restore a startup receipt from a JSON-like mapping."""
    return StartupReceipt(
        schema_version=int(payload.get("schema_version") or 1),
        contract_id=str(payload.get("contract_id") or "StartupReceipt").strip(),
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        repo_name=str(payload.get("repo_name") or "").strip(),
        current_branch=str(payload.get("current_branch") or "").strip(),
        head_commit_sha=str(payload.get("head_commit_sha") or "").strip(),
        advisory_action=str(payload.get("advisory_action") or "").strip(),
        advisory_reason=str(payload.get("advisory_reason") or "").strip(),
        recommended_action=str(payload.get("recommended_action") or "").strip(),
        checkpoint_required=bool(payload.get("checkpoint_required", False)),
        safe_to_continue_editing=bool(payload.get("safe_to_continue_editing", True)),
        startup_authority_ok=bool(payload.get("startup_authority_ok", False)),
        startup_authority_errors=tuple(
            str(row).strip()
            for row in payload.get("startup_authority_errors", ())
            if str(row).strip()
        ),
        startup_authority_warnings=tuple(
            str(row).strip()
            for row in payload.get("startup_authority_warnings", ())
            if str(row).strip()
        ),
    )


def startup_receipt_problems(
    receipt: StartupReceipt | None,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Return receipt freshness problems for launcher/mutation gates."""
    if receipt is None:
        return [
            "Startup receipt is missing. Run the repo's `startup-context` command before guarded launcher or mutation commands.",
        ]
    resolved_root = repo_root or get_repo_root()
    current_branch = _git_stdout(resolved_root, "branch", "--show-current")
    current_head = _git_stdout(resolved_root, "rev-parse", "HEAD")
    problems: list[str] = []
    if (
        receipt.current_branch
        and current_branch
        and receipt.current_branch != current_branch
    ):
        problems.append(
            "Startup receipt is stale for the current branch "
            f"(`{receipt.current_branch}` -> `{current_branch}`)."
        )
    if (
        receipt.head_commit_sha
        and current_head
        and receipt.head_commit_sha != current_head
    ):
        problems.append(
            "Startup receipt is stale for the current HEAD commit "
            f"(`{receipt.head_commit_sha[:12]}` -> `{current_head[:12]}`)."
        )
    if receipt.checkpoint_required or not receipt.safe_to_continue_editing:
        problems.append(
            "Latest startup receipt still requires a checkpoint before another implementation or launcher step."
        )
    if not receipt.startup_authority_ok:
        problems.append(
            "Latest startup receipt recorded startup-authority failures."
        )
    return problems


def _reports_root_relative_path(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path:
    configured = _configured_reports_root(governance=governance, repo_root=repo_root)
    if configured is not None:
        return configured
    return Path(active_path_config().reports_root_rel)


def _configured_reports_root(
    *,
    governance: "ProjectGovernance | None" = None,
    repo_root: Path | None = None,
) -> Path | None:
    reports_root = ""
    if governance is not None:
        reports_root = str(governance.path_roots.reports or "").strip()
    if not reports_root:
        scanned = _scan_repo_governance(repo_root or get_repo_root())
        if scanned is not None:
            reports_root = str(scanned.path_roots.reports or "").strip()
    if not reports_root:
        return None
    return Path(reports_root)


def _scan_repo_governance(repo_root: Path) -> "ProjectGovernance | None":
    try:
        from ..governance.draft import scan_repo_governance
    except ImportError:
        return None
    try:
        return scan_repo_governance(repo_root)
    except (OSError, ValueError):
        return None


def _git_stdout(repo_root: Path, *cmd: str) -> str:
    try:
        result = subprocess.run(
            ["git", *cmd],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


__all__ = [
    "StartupReceipt",
    "build_startup_receipt",
    "load_startup_receipt",
    "startup_receipt_from_mapping",
    "startup_receipt_relative_path",
    "startup_receipt_path",
    "startup_receipt_problems",
    "write_startup_receipt",
]
