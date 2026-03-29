"""Helpers for exporting the portable governance stack as a self-contained bundle."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import REPO_ROOT
from .governance_export_artifacts import write_generated_artifacts
from .quality_policy import resolve_quality_policy
from .time_utils import utc_timestamp

DEFAULT_EXPORT_BASE_DIR = REPO_ROOT.parent / "portable_snapshot_exports"
DEFAULT_HEAD_REF = "HEAD"
EXPORT_SOURCE_PATHS = (
    ".github/workflows",
    "AGENTS.md",
    "dev/README.md",
    "dev/active",
    "dev/config",
    "dev/config/templates",
    "dev/guides/DEVELOPMENT.md",
    "dev/guides/MCP_DEVCTL_ALIGNMENT.md",
    "dev/guides/PORTABLE_CODE_GOVERNANCE.md",
    "dev/history/ENGINEERING_EVOLUTION.md",
    "dev/scripts/README.md",
    "dev/scripts/checks",
    "dev/scripts/devctl",
    "dev/scripts/devctl.py",
)


@dataclass(frozen=True, slots=True)
class GovernanceExportResult:
    """Structured result from one governance export run."""

    snapshot_dir: str
    zip_path: str | None
    copied_sources: tuple[str, ...]
    generated_artifacts: dict[str, str]
    policy_path: str
    created_at_utc: str


@dataclass(frozen=True, slots=True)
class GovernanceExportRequest:
    """Input bundle for one governance export run."""

    export_base_dir: str | Path | None
    snapshot_name: str | None
    policy_path: str | Path | None
    since_ref: str | None
    head_ref: str = DEFAULT_HEAD_REF
    create_zip: bool = True
    force: bool = False


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    """Serializable manifest for one exported governance bundle."""

    command: str
    created_at: str
    repo_root: str
    export_root: str
    quality_policy_override: str | None
    copied_sources: list[str]
    generated_artifacts: dict[str, str]


def default_snapshot_name(*, timestamp: str | None = None) -> str:
    """Return the default portable-governance snapshot directory name."""
    stamp = (timestamp or utc_timestamp()).split("T", 1)[0]
    return f"portable_code_governance_snapshot_{stamp}"


def resolve_export_base_dir(
    raw_path: str | Path | None,
    *,
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Resolve the export base directory relative to the repo parent by default."""
    if raw_path is None or not str(raw_path).strip():
        return (repo_root.parent / DEFAULT_EXPORT_BASE_DIR.name).resolve()
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def build_governance_export(
    request: GovernanceExportRequest,
    *,
    repo_root: Path = REPO_ROOT,
) -> GovernanceExportResult:
    """Copy the governance stack and generate fresh portable review artifacts."""
    created_at = utc_timestamp()
    base_dir = resolve_export_base_dir(
        request.export_base_dir,
        repo_root=repo_root,
    )
    repo_root_resolved = repo_root.resolve()
    export_inside_repo = base_dir == repo_root_resolved
    if not export_inside_repo:
        try:
            base_dir.relative_to(repo_root_resolved)
        except ValueError:
            pass
        else:
            export_inside_repo = True
    if export_inside_repo:
        raise ValueError(
            "export base dir must live outside the repository root; "
            "copying the governance snapshot inside the repo poisons duplication audits"
        )
    snapshot_dir = base_dir / _sanitize_snapshot_name(
        request.snapshot_name or default_snapshot_name(timestamp=created_at)
    )
    if snapshot_dir.exists():
        if not request.force:
            raise ValueError(
                f"snapshot destination already exists: {snapshot_dir} " "(re-run with --force to replace it)"
            )
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for relative_path in EXPORT_SOURCE_PATHS:
        source = repo_root / relative_path
        destination = snapshot_dir / relative_path
        if not source.exists():
            continue
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        copied.append(relative_path)
    copied_sources = tuple(copied)
    generated_artifacts = write_generated_artifacts(
        snapshot_dir=snapshot_dir,
        repo_root=repo_root,
        policy_path=request.policy_path,
        since_ref=request.since_ref,
        head_ref=request.head_ref,
    )
    manifest = SnapshotManifest(
        command="governance-export",
        created_at=created_at,
        repo_root=str(repo_root),
        export_root=str(snapshot_dir),
        quality_policy_override=str(request.policy_path) if request.policy_path else None,
        copied_sources=list(copied_sources),
        generated_artifacts=generated_artifacts,
    )
    manifest_path = snapshot_dir / "generated" / "snapshot_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    generated_artifacts["manifest_json"] = str(manifest_path)

    zip_path: str | None = None
    if request.create_zip:
        archive_base = snapshot_dir.with_suffix("")
        zip_path = shutil.make_archive(
            base_name=str(archive_base),
            format="zip",
            root_dir=str(snapshot_dir.parent),
            base_dir=snapshot_dir.name,
        )
    resolved_policy = resolve_quality_policy(
        repo_root=repo_root,
        policy_path=request.policy_path,
    )
    return GovernanceExportResult(
        snapshot_dir=str(snapshot_dir),
        zip_path=zip_path,
        copied_sources=copied_sources,
        generated_artifacts=generated_artifacts,
        policy_path=str(resolved_policy.policy_path),
        created_at_utc=created_at,
    )


def _sanitize_snapshot_name(name: str) -> str:
    tokens = [token for token in str(name).strip().replace(" ", "_").split("/") if token]
    sanitized = "_".join(tokens)
    return sanitized or default_snapshot_name()
