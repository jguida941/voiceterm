"""Repo policy resolution for devctl quality guards and review probes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import REPO_ROOT
from .quality_policy_defaults import (
    AI_GUARD_REGISTRY,
    DEFAULT_AI_GUARD_CHECKS,
    DEFAULT_ENABLED_AI_GUARD_IDS,
    DEFAULT_REVIEW_PROBE_CHECKS,
    DEFAULT_ENABLED_REVIEW_PROBE_IDS,
    REVIEW_PROBE_REGISTRY,
    QualityStepSpec,
)
from .quality_policy_loader import (
    QUALITY_POLICY_ENV_VAR,
    load_policy_payload,
    resolve_policy_path,
)
from .quality_policy_scopes import (
    SCOPE_ATTRIBUTE_MAP,
    ResolvedQualityScopes,
    resolve_quality_scopes,
)
from .quality_policy_values import (
    coerce_bool,
    coerce_enabled_ids,
    coerce_guard_configs,
    coerce_overrides,
)

DEFAULT_POLICY_RELATIVE_PATH = "dev/config/devctl_repo_policy.json"


@dataclass(frozen=True, slots=True)
class RepoCapabilities:
    """Detected or overridden language/tooling capabilities for one repo."""

    python: bool = False
    rust: bool = False


@dataclass(frozen=True, slots=True)
class ResolvedQualityPolicy:
    """Resolved repo policy plus enabled quality steps for the current repo."""

    schema_version: int
    repo_name: str
    policy_path: Path
    capabilities: RepoCapabilities
    scopes: ResolvedQualityScopes
    ai_guard_checks: tuple[QualityStepSpec, ...]
    review_probe_checks: tuple[QualityStepSpec, ...]
    guard_configs: dict[str, dict[str, Any]]
    warnings: tuple[str, ...]


def _manifest_exists(repo_root: Path, filename: str) -> bool:
    return (repo_root / filename).exists() or any(candidate.is_file() for candidate in repo_root.glob(f"*/{filename}"))


def _has_python_sources(repo_root: Path) -> bool:
    return any(any(repo_root.glob(pattern)) for pattern in ("*.py", "*/*.py", "*/*/*.py"))


def detect_repo_capabilities(repo_root: Path = REPO_ROOT) -> RepoCapabilities:
    """Detect broad repo language capabilities using common manifests."""
    rust = _manifest_exists(repo_root, "Cargo.toml")
    python = any(
        _manifest_exists(repo_root, filename)
        for filename in (
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "requirements-dev.txt",
            "Pipfile",
        )
    )
    if not python:
        python = _has_python_sources(repo_root)
    return RepoCapabilities(python=python, rust=rust)


def _resolve_capabilities(
    payload: dict[str, Any] | None,
    *,
    repo_root: Path,
) -> RepoCapabilities:
    detected = detect_repo_capabilities(repo_root)
    if payload is None:
        return detected
    raw_capabilities = payload.get("capabilities")
    if not isinstance(raw_capabilities, dict):
        return detected
    return RepoCapabilities(
        python=coerce_bool(raw_capabilities.get("python"), detected.python),
        rust=coerce_bool(raw_capabilities.get("rust"), detected.rust),
    )


def _language_supported(
    languages: tuple[str, ...],
    capabilities: RepoCapabilities,
) -> bool:
    if not languages:
        return True
    return ("python" in languages and capabilities.python) or ("rust" in languages and capabilities.rust)


def _resolve_specs(
    *,
    enabled_ids: tuple[str, ...],
    registry: dict[str, QualityStepSpec],
    overrides: dict[str, dict[str, Any]],
    capabilities: RepoCapabilities,
    warnings: list[str],
    kind: str,
) -> tuple[QualityStepSpec, ...]:
    resolved: list[QualityStepSpec] = []
    seen_ids: set[str] = set()
    for script_id in enabled_ids:
        if script_id in seen_ids:
            continue
        seen_ids.add(script_id)
        spec = registry.get(script_id)
        if spec is None:
            warnings.append(f"{kind} `{script_id}` is not a known built-in entry")
            continue
        override = overrides.get(script_id, {})
        if override.get("enabled") is False:
            continue
        if not _language_supported(spec.languages, capabilities):
            warnings.append(
                f"{kind} `{script_id}` skipped because the repo capabilities do not "
                f"match {', '.join(spec.languages)}"
            )
            continue
        resolved.append(
            QualityStepSpec(
                step_name=str(override.get("step_name") or spec.step_name),
                script_id=spec.script_id,
                extra_args=tuple(override.get("extra_args") or spec.extra_args),
                languages=spec.languages,
                supports_commit_range=spec.supports_commit_range,
            )
        )
    return tuple(resolved)


def resolve_quality_policy(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> ResolvedQualityPolicy:
    """Resolve the active repo quality policy with safe defaults."""
    default_policy_path = repo_root / DEFAULT_POLICY_RELATIVE_PATH
    resolved_policy_path = resolve_policy_path(
        repo_root=repo_root,
        policy_path=policy_path,
        default_policy_path=default_policy_path,
    )
    warnings: list[str] = []
    payload = load_policy_payload(
        resolved_policy_path,
        warnings=warnings,
        active_paths=set(),
    )

    capabilities = _resolve_capabilities(payload, repo_root=repo_root)
    scopes = resolve_quality_scopes(
        payload,
        repo_root=repo_root,
        capabilities=capabilities,
        warnings=warnings,
        has_python_sources=_has_python_sources,
    )
    ai_guard_ids = coerce_enabled_ids(
        payload.get("enabled_ai_guard_ids") if payload else None,
        DEFAULT_ENABLED_AI_GUARD_IDS,
    )
    probe_ids = coerce_enabled_ids(
        payload.get("enabled_review_probe_ids") if payload else None,
        DEFAULT_ENABLED_REVIEW_PROBE_IDS,
    )
    ai_guard_overrides = coerce_overrides(payload.get("ai_guard_overrides") if payload else None)
    probe_overrides = coerce_overrides(payload.get("review_probe_overrides") if payload else None)
    guard_configs = coerce_guard_configs(payload.get("guard_configs") if payload else None)
    ai_guard_checks = _resolve_specs(
        enabled_ids=ai_guard_ids,
        registry=AI_GUARD_REGISTRY,
        overrides=ai_guard_overrides,
        capabilities=capabilities,
        warnings=warnings,
        kind="ai-guard",
    )
    review_probe_checks = _resolve_specs(
        enabled_ids=probe_ids,
        registry=REVIEW_PROBE_REGISTRY,
        overrides=probe_overrides,
        capabilities=capabilities,
        warnings=warnings,
        kind="review-probe",
    )
    schema_version = 1
    repo_name = "current-repo"
    if payload is not None:
        try:
            schema_version = int(payload.get("schema_version"))
        except (TypeError, ValueError):
            schema_version = 1
        repo_name = str(payload.get("repo_name") or repo_name).strip() or repo_name
    return ResolvedQualityPolicy(
        schema_version=schema_version,
        repo_name=repo_name,
        policy_path=resolved_policy_path,
        capabilities=capabilities,
        scopes=scopes,
        ai_guard_checks=ai_guard_checks,
        review_probe_checks=review_probe_checks,
        guard_configs=guard_configs,
        warnings=tuple(warnings),
    )


def resolve_ai_guard_checks(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Return active AI-guard steps for the repo policy."""
    policy = resolve_quality_policy(repo_root=repo_root, policy_path=policy_path)
    return tuple((spec.step_name, spec.script_id, spec.extra_args) for spec in policy.ai_guard_checks)


def resolve_review_probe_checks(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Return active review-probe steps for the repo policy."""
    policy = resolve_quality_policy(repo_root=repo_root, policy_path=policy_path)
    return tuple((spec.step_name, spec.script_id, spec.extra_args) for spec in policy.review_probe_checks)


def resolve_review_probe_script_ids(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[str, ...]:
    """Return active probe script ids for aggregated probe-report runs."""
    policy = resolve_quality_policy(repo_root=repo_root, policy_path=policy_path)
    return tuple(spec.script_id for spec in policy.review_probe_checks)


def resolve_quality_scope_roots(
    scope_id: str,
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[Path, ...]:
    """Return the repo-relative roots for one configured quality scope."""
    attribute = SCOPE_ATTRIBUTE_MAP.get(scope_id)
    if attribute is None:
        raise KeyError(f"unknown quality scope id: {scope_id}")
    policy = resolve_quality_policy(repo_root=repo_root, policy_path=policy_path)
    return tuple(getattr(policy.scopes, attribute))


def resolve_guard_config(
    script_id: str,
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return the resolved per-script config payload for one guard or probe."""
    policy = resolve_quality_policy(repo_root=repo_root, policy_path=policy_path)
    config = policy.guard_configs.get(script_id)
    if not isinstance(config, dict):
        return {}
    return deepcopy(config)


def ai_guard_supports_commit_range(script_id: str) -> bool:
    """Return whether one AI guard supports commit-range arguments."""
    spec = AI_GUARD_REGISTRY.get(script_id)
    return bool(spec and spec.supports_commit_range)


def review_probe_supports_commit_range(script_id: str) -> bool:
    """Return whether one review probe supports commit-range arguments."""
    spec = REVIEW_PROBE_REGISTRY.get(script_id)
    return bool(spec and spec.supports_commit_range)
