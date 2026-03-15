"""Repo-local onboarding guide writer for portable governance bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..quality_policy import RepoCapabilities
from .bootstrap_policy import STARTER_POLICY_RELATIVE_PATH

STARTER_SETUP_GUIDE_RELATIVE_PATH = "dev/guides/PORTABLE_GOVERNANCE_SETUP.md"


@dataclass(frozen=True, slots=True)
class StarterSetupGuideResult:
    """Result payload for writing one repo-local setup guide."""

    guide_path: str
    written: bool


def _relative_display(repo_root: Path, raw_path: str | None, fallback: str) -> str:
    if not raw_path:
        return fallback
    path = Path(raw_path)
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return raw_path


def _capability_label(capabilities: RepoCapabilities) -> str:
    labels: list[str] = []
    if capabilities.python:
        labels.append("Python")
    if capabilities.rust:
        labels.append("Rust")
    return " + ".join(labels) if labels else "No language capability detected yet"


def render_starter_setup_guide(
    repo_root: Path,
    *,
    starter_policy_path: str | None,
    starter_policy_preset: str | None,
    capabilities: RepoCapabilities,
    next_steps: tuple[str, ...],
) -> str:
    """Render the repo-local setup guide for an adopted governance repo."""
    policy_display = _relative_display(
        repo_root,
        starter_policy_path,
        STARTER_POLICY_RELATIVE_PATH,
    )
    lines = [f"# Portable Governance Setup For `{repo_root.name}`", ""]
    lines.append(
        "This file is the one obvious bootstrap surface for an AI or maintainer "
        "setting this repo up with the portable devctl guard/probe stack."
    )
    lines.extend(
        [
            "",
            "## Detected Repo Shape",
            "",
            f"- repo_name: `{repo_root.name}`",
            f"- detected_capabilities: `{_capability_label(capabilities)}`",
            f"- starter_policy_path: `{policy_display}`",
            f"- starter_policy_preset: `{starter_policy_preset or '(none yet)'}`",
            "",
            "## Read These Files First",
            "",
            "- `dev/guides/PORTABLE_GOVERNANCE_SETUP.md`",
            f"- `{policy_display}`",
            "- `dev/scripts/README.md`",
            "- `dev/guides/PORTABLE_CODE_GOVERNANCE.md`",
            "",
            "## Run Order",
            "",
        ]
    )
    lines.extend(f"{index}. `{step}`" for index, step in enumerate(next_steps, start=1))
    lines.extend(
        [
            "",
            "## Customize Before Strict Use",
            "",
            "- Tighten `repo_governance.check_router.*` so lane routing matches this repo's real runtime/tooling/docs boundaries.",
            "- Tighten `repo_governance.docs_check.*` so canonical user docs, maintainer docs, and engineering-history files reflect this repo instead of the starter defaults.",
            "- Review the resolved `quality-policy` output before treating the first `adoption-scan` as authoritative.",
            "",
            "## Truthful Scope",
            "",
            "- The portable quality engine is ready for Python and Rust repos.",
            "- Higher-level VoiceTerm control-plane helpers such as Ralph, mutation loops, and host-process hygiene are still more repo-local than the core guard/probe engine.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_starter_setup_guide(
    repo_root: Path,
    *,
    starter_policy_path: str | None,
    starter_policy_preset: str | None,
    capabilities: RepoCapabilities,
    next_steps: tuple[str, ...],
    force: bool = False,
) -> StarterSetupGuideResult:
    """Write the repo-local setup guide unless one already exists."""
    guide_path = repo_root / STARTER_SETUP_GUIDE_RELATIVE_PATH
    if guide_path.exists() and not force:
        return StarterSetupGuideResult(
            guide_path=str(guide_path),
            written=False,
        )

    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text(
        render_starter_setup_guide(
            repo_root,
            starter_policy_path=starter_policy_path,
            starter_policy_preset=starter_policy_preset,
            capabilities=capabilities,
            next_steps=next_steps,
        ),
        encoding="utf-8",
    )
    return StarterSetupGuideResult(
        guide_path=str(guide_path),
        written=True,
    )
