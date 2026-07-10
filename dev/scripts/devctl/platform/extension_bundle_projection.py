"""Repo-pack-aware projection helpers for ExtensionBundle surfaces.

This module turns the typed ``ExtensionBundle`` scaffold into a concrete
read-only projection. The projection reports which extension surfaces and
governed automations the active repo-pack owns today, where those surfaces
would live in the repo, and whether those targets currently exist.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..common_io import display_path, resolve_repo_path
from ..config import REPO_ROOT
from ..governance.repo_policy import load_repo_governance_section
from .extension_bundle import (
    VALID_EXECUTION_MODES,
    VALID_SURFACE_FORMATS,
    AutomationSpec,
    ExtensionBundle,
    ExtensionSurface,
)
from .extension_bundle_defaults import registered_extension_bundles


def resolve_extension_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    repo_pack_id: str | None = None,
    policy_path: str | Path | None = None,
) -> ExtensionBundle:
    """Return the registered bundle for the active repo-pack or fail closed."""
    resolved_repo_pack_id = (
        str(repo_pack_id or "").strip()
        or _policy_pack_id(repo_root=repo_root, policy_path=policy_path)
    )
    if not resolved_repo_pack_id:
        raise RuntimeError(
            "ExtensionBundle resolution requires "
            "`repo_governance.surface_generation.repo_pack_metadata.pack_id` "
            "or an explicit repo_pack_id."
        )
    bundle = registered_extension_bundles().get(resolved_repo_pack_id)
    if bundle is None:
        raise RuntimeError(
            f"No registered ExtensionBundle exists for repo-pack "
            f"`{resolved_repo_pack_id}`."
        )
    return bundle


def build_extension_bundle_projection(
    *,
    repo_root: Path = REPO_ROOT,
    repo_pack_id: str | None = None,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build one read-only report for the active repo-pack extension bundle."""
    policy_pack_id, policy_warnings, resolved_policy_path = _read_policy_pack_id(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    warnings = list(policy_warnings)
    try:
        bundle = resolve_extension_bundle(
            repo_root=repo_root,
            repo_pack_id=repo_pack_id,
            policy_path=policy_path,
        )
    except RuntimeError as exc:
        return {
            "command": "extension-bundle-projection",
            "ok": False,
            "error": str(exc),
            "repo_pack_id": str(repo_pack_id or "").strip(),
            "policy_pack_id": policy_pack_id,
            "policy_path": (
                display_path(resolved_policy_path, repo_root=repo_root)
                if resolved_policy_path is not None
                else ""
            ),
            "warnings": warnings,
            "surface_count": 0,
            "automation_count": 0,
            "present_surface_count": 0,
            "missing_surface_count": 0,
            "surfaces": [],
            "automations": [],
        }

    if policy_pack_id and policy_pack_id != bundle.repo_pack_id:
        warnings.append(
            "repo-governance pack id "
            f"`{policy_pack_id}` does not match the selected ExtensionBundle "
            f"`{bundle.repo_pack_id}`."
        )

    surface_entries = [
        _project_surface(surface, repo_root=repo_root, warnings=warnings)
        for surface in bundle.surfaces
    ]
    automation_entries = [
        _project_automation(automation, warnings=warnings)
        for automation in bundle.automations
    ]
    present_surface_count = sum(1 for entry in surface_entries if entry["exists"])

    return {
        "command": "extension-bundle-projection",
        "ok": True,
        "repo_pack_id": bundle.repo_pack_id,
        "policy_pack_id": policy_pack_id,
        "policy_path": (
            display_path(resolved_policy_path, repo_root=repo_root)
            if resolved_policy_path is not None
            else ""
        ),
        "warnings": warnings,
        "surface_count": len(surface_entries),
        "automation_count": len(automation_entries),
        "present_surface_count": present_surface_count,
        "missing_surface_count": len(surface_entries) - present_surface_count,
        "surfaces": surface_entries,
        "automations": automation_entries,
    }


def render_extension_bundle_projection_markdown(report: dict[str, Any]) -> str:
    """Render one maintainer-friendly markdown summary for the bundle report."""
    lines = ["# devctl extension-bundle", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- repo_pack_id: {report.get('repo_pack_id') or '(unknown)'}")
    lines.append(
        f"- policy_pack_id: {report.get('policy_pack_id') or '(not declared)'}"
    )
    lines.append(f"- policy_path: {report.get('policy_path') or '(unknown)'}")
    lines.append(f"- surface_count: {report.get('surface_count', 0)}")
    lines.append(f"- automation_count: {report.get('automation_count', 0)}")
    lines.append(
        f"- present_surface_count: {report.get('present_surface_count', 0)}"
    )
    lines.append(
        f"- missing_surface_count: {report.get('missing_surface_count', 0)}"
    )
    error = str(report.get("error") or "").strip()
    if error:
        lines.append(f"- error: {error}")
    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(["", "## Warnings"])
        for warning in warnings:
            lines.append(f"- {warning}")
    surfaces = report.get("surfaces") or []
    if surfaces:
        lines.extend(["", "## Surfaces"])
        for entry in surfaces:
            lines.append(
                "- {surface_id}: state={state}; target_kind={target_kind}; "
                "format={format}; target={target_path}".format(**entry)
            )
            if entry.get("description"):
                lines.append(f"  - description: {entry['description']}")
            if entry.get("source_contract"):
                lines.append(f"  - source_contract: {entry['source_contract']}")
    automations = report.get("automations") or []
    if automations:
        lines.extend(["", "## Automations"])
        for entry in automations:
            lines.append(
                "- {task_id}: modes={modes}; command={command}".format(
                    task_id=entry["task_id"],
                    modes=", ".join(entry["execution_modes"]),
                    command=entry["command"],
                )
            )
            if entry.get("description"):
                lines.append(f"  - description: {entry['description']}")
            if entry.get("schedule"):
                lines.append(f"  - schedule: {entry['schedule']}")
    return "\n".join(lines)


def _read_policy_pack_id(
    *,
    repo_root: Path,
    policy_path: str | Path | None,
) -> tuple[str, list[str], Path | None]:
    section, warnings, resolved_policy_path = load_repo_governance_section(
        "surface_generation",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    metadata = section.get("repo_pack_metadata")
    if not isinstance(metadata, dict):
        return "", list(warnings), resolved_policy_path
    return str(metadata.get("pack_id") or "").strip(), list(warnings), resolved_policy_path


def _policy_pack_id(
    *,
    repo_root: Path,
    policy_path: str | Path | None,
) -> str:
    policy_pack_id, _warnings, _resolved_policy_path = _read_policy_pack_id(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    return policy_pack_id


def _project_surface(
    surface: ExtensionSurface,
    *,
    repo_root: Path,
    warnings: list[str],
) -> dict[str, Any]:
    if surface.format not in VALID_SURFACE_FORMATS:
        warnings.append(
            f"surface `{surface.surface_id}` uses unsupported format "
            f"`{surface.format}`."
        )
    target_kind = "directory" if surface.target_path.endswith("/") else "file"
    absolute_target = resolve_repo_path(surface.target_path, repo_root=repo_root)
    exists = (
        absolute_target.is_dir() if target_kind == "directory" else absolute_target.is_file()
    )
    return {
        "surface_id": surface.surface_id,
        "target_path": display_path(absolute_target, repo_root=repo_root),
        "absolute_target_path": str(absolute_target),
        "target_kind": target_kind,
        "exists": exists,
        "state": "present" if exists else "missing",
        "format": surface.format,
        "source_contract": surface.source_contract,
        "description": surface.description,
    }


def _project_automation(
    automation: AutomationSpec,
    *,
    warnings: list[str],
) -> dict[str, Any]:
    invalid_modes = [
        mode for mode in automation.execution_modes if mode not in VALID_EXECUTION_MODES
    ]
    if invalid_modes:
        warnings.append(
            f"automation `{automation.task_id}` uses unsupported execution modes: "
            + ", ".join(f"`{mode}`" for mode in invalid_modes)
        )
    return {
        "task_id": automation.task_id,
        "devctl_command": automation.devctl_command,
        "command": f"python3 dev/scripts/devctl.py {automation.devctl_command}",
        "execution_modes": list(automation.execution_modes),
        "schedule": automation.schedule,
        "description": automation.description,
    }
