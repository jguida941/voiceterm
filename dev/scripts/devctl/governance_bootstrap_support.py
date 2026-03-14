"""Helpers for preparing copied repositories for portable-governance pilots."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .governance.bootstrap_guide import write_starter_setup_guide
from .governance.bootstrap_policy import (
    STARTER_POLICY_RELATIVE_PATH,
    write_starter_repo_policy,
)
from .quality_policy import RepoCapabilities, detect_repo_capabilities
from .time_utils import utc_timestamp


@dataclass(frozen=True, slots=True)
class GovernanceBootstrapResult:
    """Result payload for one pilot bootstrap run."""

    target_repo: str
    git_state: str
    repaired_git_file: bool
    initialized_git_repo: bool
    broken_gitdir_hint: str | None
    starter_policy_path: str | None
    starter_policy_written: bool
    starter_policy_preset: str | None
    starter_policy_warnings: tuple[str, ...]
    starter_setup_guide_path: str | None
    starter_setup_guide_written: bool
    next_steps: tuple[str, ...]
    created_at_utc: str


@dataclass(frozen=True, slots=True)
class BootstrapArtifactsResult:
    """Starter artifacts written or detected during bootstrap."""

    capabilities: RepoCapabilities
    starter_policy_path: str | None
    starter_policy_written: bool
    starter_policy_preset: str | None
    starter_policy_warnings: tuple[str, ...]
    starter_setup_guide_path: str | None
    starter_setup_guide_written: bool


def _build_next_steps(
    target_repo: Path,
    *,
    starter_policy_path: str | None,
) -> tuple[str, ...]:
    steps = [
        "Copy or export the governance stack into the target repo if it is not already present.",
        f"cd {target_repo}",
    ]
    if starter_policy_path:
        steps.append(
            "Inspect the starter policy at `dev/config/devctl_repo_policy.json` "
            "and tighten repo_governance paths before strict use."
        )
    else:
        steps.append(
            "Create or copy `dev/config/devctl_repo_policy.json` before relying on repo-specific routing/docs governance."
        )
    steps.extend(
        [
            "python3 dev/scripts/devctl.py quality-policy --format md",
            "python3 dev/scripts/devctl.py render-surfaces --write --format md",
            "python3 dev/scripts/devctl.py check --profile ci --adoption-scan",
            "python3 dev/scripts/devctl.py probe-report --adoption-scan --format md",
        ]
    )
    return tuple(steps)


def _write_bootstrap_artifacts(
    repo_root: Path,
    *,
    write_starter_policy: bool,
    force_starter_policy: bool,
) -> BootstrapArtifactsResult:
    capabilities = detect_repo_capabilities(repo_root)
    starter_policy_path: str | None = None
    starter_policy_written = False
    starter_policy_preset: str | None = None
    starter_policy_warnings: tuple[str, ...] = ()
    policy_path = repo_root / STARTER_POLICY_RELATIVE_PATH

    if write_starter_policy:
        starter_policy = write_starter_repo_policy(
            repo_root,
            force=force_starter_policy,
        )
        capabilities = starter_policy.capabilities
        starter_policy_path = starter_policy.policy_path
        starter_policy_written = starter_policy.written
        starter_policy_preset = starter_policy.preset
        starter_policy_warnings = starter_policy.warnings
    elif policy_path.exists():
        starter_policy_path = str(policy_path)

    next_steps = _build_next_steps(
        repo_root,
        starter_policy_path=starter_policy_path,
    )
    setup_guide = write_starter_setup_guide(
        repo_root,
        starter_policy_path=starter_policy_path,
        starter_policy_preset=starter_policy_preset,
        capabilities=capabilities,
        next_steps=next_steps,
        force=force_starter_policy,
    )
    return BootstrapArtifactsResult(
        capabilities=capabilities,
        starter_policy_path=starter_policy_path,
        starter_policy_written=starter_policy_written,
        starter_policy_preset=starter_policy_preset,
        starter_policy_warnings=starter_policy_warnings,
        starter_setup_guide_path=setup_guide.guide_path,
        starter_setup_guide_written=setup_guide.written,
    )


def bootstrap_governance_pilot_repo(
    target_repo: str | Path,
    *,
    write_starter_policy: bool = True,
    force_starter_policy: bool = False,
) -> GovernanceBootstrapResult:
    """Repair broken copied-repo git state so governance tools can run locally."""
    repo_root = Path(target_repo).expanduser().resolve()
    if not repo_root.exists():
        raise ValueError(f"target repo does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise ValueError(f"target repo is not a directory: {repo_root}")

    created_at = utc_timestamp()
    git_file = repo_root / ".git"
    repaired_git_file = False
    initialized_git_repo = False
    broken_gitdir_hint: str | None = None
    starter_policy_path: str | None = None
    starter_policy_written = False
    starter_policy_preset: str | None = None
    starter_policy_warnings: tuple[str, ...] = ()
    starter_setup_guide_path: str | None = None
    starter_setup_guide_written = False
    next_steps: tuple[str, ...] = ()

    if _git_context_is_valid(repo_root):
        bootstrap_artifacts = _write_bootstrap_artifacts(
            repo_root,
            write_starter_policy=write_starter_policy,
            force_starter_policy=force_starter_policy,
        )
        starter_policy_path = bootstrap_artifacts.starter_policy_path
        starter_policy_written = bootstrap_artifacts.starter_policy_written
        starter_policy_preset = bootstrap_artifacts.starter_policy_preset
        starter_policy_warnings = bootstrap_artifacts.starter_policy_warnings
        starter_setup_guide_path = bootstrap_artifacts.starter_setup_guide_path
        starter_setup_guide_written = bootstrap_artifacts.starter_setup_guide_written
        next_steps = _build_next_steps(
            repo_root,
            starter_policy_path=starter_policy_path,
        )
        return GovernanceBootstrapResult(
            target_repo=str(repo_root),
            git_state="valid",
            repaired_git_file=False,
            initialized_git_repo=False,
            broken_gitdir_hint=None,
            starter_policy_path=starter_policy_path,
            starter_policy_written=starter_policy_written,
            starter_policy_preset=starter_policy_preset,
            starter_policy_warnings=starter_policy_warnings,
            starter_setup_guide_path=starter_setup_guide_path,
            starter_setup_guide_written=starter_setup_guide_written,
            next_steps=next_steps,
            created_at_utc=created_at,
        )

    if git_file.is_file():
        broken_gitdir_hint = git_file.read_text(encoding="utf-8", errors="replace").strip()
        git_file.unlink()
        repaired_git_file = True
    elif git_file.exists():
        raise ValueError(f"unsupported .git path shape in target repo: {git_file}")

    _run_git(repo_root, ["git", "init"])
    initialized_git_repo = True
    bootstrap_artifacts = _write_bootstrap_artifacts(
        repo_root,
        write_starter_policy=write_starter_policy,
        force_starter_policy=force_starter_policy,
    )
    starter_policy_path = bootstrap_artifacts.starter_policy_path
    starter_policy_written = bootstrap_artifacts.starter_policy_written
    starter_policy_preset = bootstrap_artifacts.starter_policy_preset
    starter_policy_warnings = bootstrap_artifacts.starter_policy_warnings
    starter_setup_guide_path = bootstrap_artifacts.starter_setup_guide_path
    starter_setup_guide_written = bootstrap_artifacts.starter_setup_guide_written
    next_steps = _build_next_steps(
        repo_root,
        starter_policy_path=starter_policy_path,
    )
    return GovernanceBootstrapResult(
        target_repo=str(repo_root),
        git_state="reinitialized",
        repaired_git_file=repaired_git_file,
        initialized_git_repo=initialized_git_repo,
        broken_gitdir_hint=broken_gitdir_hint,
        starter_policy_path=starter_policy_path,
        starter_policy_written=starter_policy_written,
        starter_policy_preset=starter_policy_preset,
        starter_policy_warnings=starter_policy_warnings,
        starter_setup_guide_path=starter_setup_guide_path,
        starter_setup_guide_written=starter_setup_guide_written,
        next_steps=next_steps,
        created_at_utc=created_at,
    )


def _git_context_is_valid(repo_root: Path) -> bool:
    try:
        _run_git(repo_root, ["git", "rev-parse", "--show-toplevel"])
    except RuntimeError:
        return False
    return True


def _run_git(repo_root: Path, cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "git failed")
    return result.stdout.strip()
