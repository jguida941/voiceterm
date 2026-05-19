"""Serializable quality-policy payload helpers shared by CLI and exports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import ResolvedQualityPolicy


@dataclass(frozen=True, slots=True)
class StepPayload:
    """Serializable view of one configured quality step."""

    step_name: str
    script_id: str
    languages: list[str]
    extra_args: list[str]
    supports_commit_range: bool


@dataclass(frozen=True, slots=True)
class CapabilityPayload:
    """Serializable capability flags for the active repo."""

    python: bool
    rust: bool


@dataclass(frozen=True, slots=True)
class ScopePayload:
    """Serializable quality-scope roots for the active repo."""

    python_guard_roots: list[str]
    python_probe_roots: list[str]
    rust_guard_roots: list[str]
    rust_probe_roots: list[str]


@dataclass(frozen=True, slots=True)
class QualityPolicyPayload:
    """Structured JSON payload for `devctl quality-policy`."""

    command: str
    repo_name: str
    policy_path: str
    schema_version: int
    capabilities: CapabilityPayload
    quality_scopes: ScopePayload
    ai_guard_checks: list[StepPayload]
    review_probe_checks: list[StepPayload]
    guard_configs: dict[str, dict[str, object]]
    warnings: list[str]


def _format_roots(roots: tuple[Path, ...]) -> str:
    if not roots:
        return "(none)"
    return ", ".join(path.as_posix() for path in roots)


def step_payload(spec) -> StepPayload:
    return StepPayload(
        step_name=spec.step_name,
        script_id=spec.script_id,
        languages=list(spec.languages),
        extra_args=list(spec.extra_args),
        supports_commit_range=spec.supports_commit_range,
    )


def build_quality_policy_payload(policy: ResolvedQualityPolicy) -> QualityPolicyPayload:
    return QualityPolicyPayload(
        command="quality-policy",
        repo_name=policy.repo_name,
        policy_path=str(policy.policy_path),
        schema_version=policy.schema_version,
        capabilities=CapabilityPayload(
            python=policy.capabilities.python,
            rust=policy.capabilities.rust,
        ),
        quality_scopes=ScopePayload(
            python_guard_roots=[path.as_posix() for path in policy.scopes.python_guard_roots],
            python_probe_roots=[path.as_posix() for path in policy.scopes.python_probe_roots],
            rust_guard_roots=[path.as_posix() for path in policy.scopes.rust_guard_roots],
            rust_probe_roots=[path.as_posix() for path in policy.scopes.rust_probe_roots],
        ),
        ai_guard_checks=[step_payload(spec) for spec in policy.ai_guard_checks],
        review_probe_checks=[step_payload(spec) for spec in policy.review_probe_checks],
        guard_configs=policy.guard_configs,
        warnings=list(policy.warnings),
    )


def render_quality_policy_markdown(policy: ResolvedQualityPolicy) -> str:
    lines = ["# devctl quality-policy", ""]
    lines.append(f"- repo_name: {policy.repo_name}")
    lines.append(f"- policy_path: {policy.policy_path}")
    lines.append(f"- schema_version: {policy.schema_version}")
    lines.append(f"- python: {policy.capabilities.python}")
    lines.append(f"- rust: {policy.capabilities.rust}")
    lines.append(f"- ai_guard_count: {len(policy.ai_guard_checks)}")
    lines.append(f"- review_probe_count: {len(policy.review_probe_checks)}")
    lines.append(f"- guard_config_count: {len(policy.guard_configs)}")
    lines.append("")
    lines.append("## Quality Scopes")
    lines.append("")
    lines.append(f"- python_guard_roots: {_format_roots(policy.scopes.python_guard_roots)}")
    lines.append(f"- python_probe_roots: {_format_roots(policy.scopes.python_probe_roots)}")
    lines.append(f"- rust_guard_roots: {_format_roots(policy.scopes.rust_guard_roots)}")
    lines.append(f"- rust_probe_roots: {_format_roots(policy.scopes.rust_probe_roots)}")
    lines.append("")
    lines.append("## AI Guards")
    lines.append("")
    for spec in policy.ai_guard_checks:
        languages = ", ".join(spec.languages) or "all"
        extra_args = " ".join(spec.extra_args) if spec.extra_args else "(none)"
        lines.append(
            f"- {spec.step_name}: script_id={spec.script_id}, "
            f"languages={languages}, extra_args={extra_args}, "
            f"supports_commit_range={spec.supports_commit_range}, "
            f"supports_validation_scope={spec.supports_validation_scope}"
        )
    lines.append("")
    lines.append("## Review Probes")
    lines.append("")
    for spec in policy.review_probe_checks:
        languages = ", ".join(spec.languages) or "all"
        extra_args = " ".join(spec.extra_args) if spec.extra_args else "(none)"
        lines.append(
            f"- {spec.step_name}: script_id={spec.script_id}, "
            f"languages={languages}, extra_args={extra_args}, "
            f"supports_commit_range={spec.supports_commit_range}, "
            f"supports_validation_scope={spec.supports_validation_scope}"
        )
    lines.append("")
    lines.append("## Guard Configs")
    lines.append("")
    if policy.guard_configs:
        for script_id in sorted(policy.guard_configs):
            lines.append(f"- {script_id}: `{json.dumps(policy.guard_configs[script_id], sort_keys=True)}`")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if policy.warnings:
        for warning in policy.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    return "\n".join(lines)
