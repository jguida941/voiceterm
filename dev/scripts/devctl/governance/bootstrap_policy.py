"""Starter-policy helpers for portable governance repo onboarding."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from .bootstrap_surfaces import build_surface_generation_governance
from .bootstrap_push import build_starter_push_governance
from ..config import REPO_ROOT
from ..quality_policy import RepoCapabilities, detect_repo_capabilities
from ..quality_policy_scopes import resolve_quality_scopes

STARTER_POLICY_RELATIVE_PATH = "dev/config/devctl_repo_policy.json"
ENGINE_PRESETS_DIR = REPO_ROOT / "dev" / "config" / "quality_presets"

_COMMON_USER_DOCS = (
    "README.md",
    "QUICK_START.md",
    "guides/USAGE.md",
    "guides/CLI_FLAGS.md",
    "guides/INSTALL.md",
    "guides/TROUBLESHOOTING.md",
    "docs/README.md",
    "docs/USAGE.md",
    "docs/INSTALL.md",
    "docs/TROUBLESHOOTING.md",
)
_COMMON_TOOLING_DOCS = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "dev/guides/DEVELOPMENT.md",
    "docs/DEVELOPMENT.md",
    "dev/README.md",
    "README.md",
)
_COMMON_EVOLUTION_DOCS = (
    "dev/history/ENGINEERING_EVOLUTION.md",
    "docs/engineering/ENGINEERING_EVOLUTION.md",
    "docs/CHANGELOG_ENGINEERING.md",
    "CHANGELOG.md",
)
_COMMON_TOOLING_EXACT = (
    "AGENTS.md",
    "Makefile",
    "CONTRIBUTING.md",
    "dev/guides/DEVELOPMENT.md",
    "docs/DEVELOPMENT.md",
    "dev/README.md",
    "README.md",
)
_COMMON_TOOLING_PREFIXES = (
    "dev/scripts/",
    "scripts/",
    "tools/",
    ".github/workflows/",
    ".github/actions/",
)
_COMMON_TOOLING_MARKDOWN_PREFIXES = (
    "dev/",
    "docs/internal/",
    "docs/engineering/",
)
_COMMON_RUNTIME_PREFIXES = (
    "src/",
    "app/",
    "lib/",
    "crates/",
    "rust/src/",
    "python/",
)
_COMMON_DOCS_PREFIXES = (
    "docs/",
    "guides/",
)
_COMMON_RELEASE_EXACT = (
    "Cargo.toml",
    "Cargo.lock",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
)
_COMMON_RELEASE_WORKFLOWS = (
    "release.yml",
    "release_preflight.yml",
    "publish.yml",
    "publish_pypi.yml",
    "publish_release_binaries.yml",
)


@dataclass(frozen=True, slots=True)
class StarterRepoPolicyResult:
    """Result payload for writing one starter repo policy file."""

    policy_path: str
    written: bool
    preset: str | None
    capabilities: RepoCapabilities
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StarterRepoLayout:
    """Detected repo paths used to seed starter governance policy."""

    user_docs: list[str]
    tooling_required_docs: list[str]
    evolution_doc: str
    tooling_exact_paths: list[str]
    tooling_prefixes: list[str]
    tooling_markdown_prefixes: list[str]
    runtime_prefixes: list[str]
    docs_prefixes: list[str]
    release_exact_paths: list[str]
    release_workflow_files: list[str]


def _first_existing(repo_root: Path, candidates: tuple[str, ...]) -> str | None:
    for relative in candidates:
        if (repo_root / relative).exists():
            return relative
    return None


def _existing_paths(repo_root: Path, candidates: tuple[str, ...]) -> list[str]:
    return [relative for relative in candidates if (repo_root / relative).exists()]


def _existing_dirs(repo_root: Path, candidates: tuple[str, ...]) -> list[str]:
    return [relative for relative in candidates if (repo_root / relative.rstrip("/")).is_dir()]


def _select_preset(capabilities: RepoCapabilities) -> str | None:
    if capabilities.python and capabilities.rust:
        return "quality_presets/portable_python_rust.json"
    if capabilities.python:
        return "quality_presets/portable_python.json"
    if capabilities.rust:
        return "quality_presets/portable_rust.json"
    return None


def _has_python_sources(root: Path) -> bool:
    return any(any(root.glob(pattern)) for pattern in ("*.py", "*/*.py", "*/*/*.py"))


def _seed_quality_presets(
    repo_root: Path,
    *,
    warnings: list[str],
) -> None:
    target_dir = repo_root / "dev" / "config" / "quality_presets"
    target_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(ENGINE_PRESETS_DIR.glob("*.json")):
        target_path = target_dir / source.name
        try:
            shutil.copy2(source, target_path)
        except OSError as exc:
            warnings.append(f"starter preset copy failed for {target_path}: {exc}")


def _serialize_quality_scopes(payload) -> dict[str, list[str]]:
    return {
        "python_guard_roots": [path.as_posix() for path in payload.python_guard_roots],
        "python_probe_roots": [path.as_posix() for path in payload.python_probe_roots],
        "rust_guard_roots": [path.as_posix() for path in payload.rust_guard_roots],
        "rust_probe_roots": [path.as_posix() for path in payload.rust_probe_roots],
    }


def _build_check_router_governance(
    layout: StarterRepoLayout,
) -> dict:
    check_router: dict[str, object] = {}
    check_router["bundle_by_lane"] = {
        "docs": "bundle.docs",
        "runtime": "bundle.runtime",
        "tooling": "bundle.tooling",
        "release": "bundle.release",
    }
    check_router["release_exact_paths"] = layout.release_exact_paths
    check_router["release_workflow_files"] = layout.release_workflow_files
    check_router["tooling_exact_paths"] = layout.tooling_exact_paths
    check_router["tooling_prefixes"] = layout.tooling_prefixes
    check_router["tooling_markdown_prefixes"] = layout.tooling_markdown_prefixes
    check_router["runtime_prefixes"] = layout.runtime_prefixes
    check_router["runtime_exact_paths"] = layout.release_exact_paths
    check_router["docs_prefixes"] = layout.docs_prefixes
    check_router["docs_exact_paths"] = layout.user_docs
    check_router["risk_addons"] = []
    return check_router


def _build_docs_check_governance(
    layout: StarterRepoLayout,
) -> dict:
    docs_check: dict[str, object] = {}
    docs_check["user_docs"] = layout.user_docs
    docs_check["tooling_change_prefixes"] = layout.tooling_prefixes
    docs_check["tooling_change_exact"] = layout.tooling_exact_paths
    docs_check["tooling_required_docs"] = layout.tooling_required_docs
    docs_check["tooling_required_doc_aliases"] = {}
    docs_check["evolution_doc"] = layout.evolution_doc
    docs_check["evolution_change_prefixes"] = layout.tooling_prefixes
    docs_check["evolution_change_exact"] = layout.tooling_exact_paths
    docs_check["deprecated_reference_targets"] = layout.tooling_required_docs
    docs_check["deprecated_reference_patterns"] = []
    return docs_check


def build_starter_repo_policy(repo_root: Path) -> tuple[dict, str | None, tuple[str, ...], RepoCapabilities]:
    """Build a conservative repo-policy starter payload for one target repo."""
    capabilities = detect_repo_capabilities(repo_root)
    preset = _select_preset(capabilities)
    warnings: list[str] = []
    if preset is None:
        warnings.append(
            "No Python or Rust capability was detected; the starter policy was written without a portable preset."
        )

    user_docs = _existing_paths(repo_root, _COMMON_USER_DOCS) or ["README.md"]
    tooling_required_docs = _existing_paths(repo_root, _COMMON_TOOLING_DOCS) or [
        user_docs[0]
    ]
    evolution_doc = _first_existing(repo_root, _COMMON_EVOLUTION_DOCS) or "CHANGELOG.md"
    tooling_exact_paths = _existing_paths(repo_root, _COMMON_TOOLING_EXACT)
    tooling_prefixes = _existing_dirs(repo_root, _COMMON_TOOLING_PREFIXES)
    tooling_markdown_prefixes = _existing_dirs(repo_root, _COMMON_TOOLING_MARKDOWN_PREFIXES)
    runtime_prefixes = _existing_dirs(repo_root, _COMMON_RUNTIME_PREFIXES)
    docs_prefixes = _existing_dirs(repo_root, _COMMON_DOCS_PREFIXES)
    release_exact_paths = _existing_paths(repo_root, _COMMON_RELEASE_EXACT)
    release_workflow_files = [
        relative
        for relative in _COMMON_RELEASE_WORKFLOWS
        if (repo_root / ".github" / "workflows" / relative).exists()
    ]

    if capabilities.rust and "src/" not in runtime_prefixes and (repo_root / "src").is_dir():
        runtime_prefixes.append("src/")
    if capabilities.python and "app/" not in runtime_prefixes and (repo_root / "app").is_dir():
        runtime_prefixes.append("app/")
    if not docs_prefixes and (repo_root / "docs").is_dir():
        docs_prefixes.append("docs/")
    quality_scopes = resolve_quality_scopes(
        None,
        repo_root=repo_root,
        capabilities=capabilities,
        warnings=warnings,
        has_python_sources=_has_python_sources,
    )

    layout = StarterRepoLayout(
        user_docs=user_docs,
        tooling_required_docs=tooling_required_docs,
        evolution_doc=evolution_doc,
        tooling_exact_paths=tooling_exact_paths,
        tooling_prefixes=tooling_prefixes,
        tooling_markdown_prefixes=tooling_markdown_prefixes,
        runtime_prefixes=runtime_prefixes,
        docs_prefixes=docs_prefixes,
        release_exact_paths=release_exact_paths,
        release_workflow_files=release_workflow_files,
    )
    repo_governance: dict[str, object] = {}
    repo_governance["check_router"] = _build_check_router_governance(layout)
    repo_governance["docs_check"] = _build_docs_check_governance(layout)
    push_governance = build_starter_push_governance(repo_root)
    repo_governance["push"] = push_governance.to_policy_payload()
    repo_governance["surface_generation"] = build_surface_generation_governance(
        repo_root=repo_root,
        tooling_required_docs=layout.tooling_required_docs,
        runtime_prefixes=layout.runtime_prefixes,
        tooling_prefixes=layout.tooling_prefixes,
        branch_policy=push_governance.surface_branch_policy(),
        development_branch=push_governance.development_branch,
    )

    payload = {
        "schema_version": 1,
        "repo_name": repo_root.name,
        "capabilities": {
            "python": capabilities.python,
            "rust": capabilities.rust,
        },
        "quality_scopes": _serialize_quality_scopes(quality_scopes),
        "repo_governance": repo_governance,
    }
    if preset:
        payload["extends"] = [preset]
    return payload, preset, tuple(warnings), capabilities


def write_starter_repo_policy(
    repo_root: Path,
    *,
    force: bool = False,
) -> StarterRepoPolicyResult:
    """Write the starter repo policy file unless one already exists."""
    policy_path = repo_root / STARTER_POLICY_RELATIVE_PATH
    payload, preset, warnings, capabilities = build_starter_repo_policy(repo_root)
    warning_list = list(warnings)
    if policy_path.exists() and not force:
        return StarterRepoPolicyResult(
            policy_path=str(policy_path),
            written=False,
            preset=preset,
            capabilities=capabilities,
            warnings=tuple(warning_list),
        )
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if preset:
        _seed_quality_presets(repo_root, warnings=warning_list)
    return StarterRepoPolicyResult(
        policy_path=str(policy_path),
        written=True,
        preset=preset,
        capabilities=capabilities,
        warnings=tuple(warning_list),
    )
