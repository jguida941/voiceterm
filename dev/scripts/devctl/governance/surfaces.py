"""Policy-owned render-surface report builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..common_io import display_path
from ..config import REPO_ROOT
from .repo_policy import load_repo_governance_section
from .surface_runtime import evaluate_surface, render_surface_report_markdown


@dataclass(frozen=True, slots=True)
class RepoPackMetadata:
    """Stable repo-pack identity for surface generation."""

    pack_id: str
    pack_version: str
    product_name: str
    repo_name: str


@dataclass(frozen=True, slots=True)
class SurfaceSpec:
    """One policy-owned surface render target."""

    surface_id: str
    surface_type: str
    renderer: str
    output_path: str
    template_path: str | None
    tracked: bool
    local_only: bool
    description: str
    required_contains: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SurfacePolicy:
    """Resolved surface-generation policy for one repo."""

    policy_path: str
    warnings: tuple[str, ...]
    metadata: RepoPackMetadata
    context: dict[str, str]
    surfaces: tuple[SurfaceSpec, ...]


def load_surface_policy(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> SurfacePolicy:
    """Load the repo-governance surface-generation section."""
    section, warnings, resolved_policy_path = load_repo_governance_section(
        "surface_generation",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    parsed_warnings = list(warnings)
    metadata = _parse_repo_pack_metadata(
        section.get("repo_pack_metadata"),
        repo_root=repo_root,
    )
    context = _build_context(
        raw_context=section.get("context"),
        metadata=metadata,
        warnings=parsed_warnings,
    )
    surfaces = _parse_surface_specs(
        section.get("surfaces"),
        warnings=parsed_warnings,
    )
    return SurfacePolicy(
        policy_path=display_path(resolved_policy_path, repo_root=repo_root),
        warnings=tuple(parsed_warnings),
        metadata=metadata,
        context=context,
        surfaces=surfaces,
    )


def build_surface_report(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
    surface_ids: tuple[str, ...] = (),
    write: bool = False,
    allow_missing_local_only: bool = False,
    allowed_renderers: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Build the render-surfaces report for command or guard use."""
    policy = load_surface_policy(repo_root=repo_root, policy_path=policy_path)
    requested = frozenset(surface_ids)
    known_ids = {spec.surface_id for spec in policy.surfaces}
    unknown = sorted(requested.difference(known_ids))
    if unknown:
        return _build_unknown_surface_report(policy, unknown)
    selected = [
        spec
        for spec in policy.surfaces
        if (not requested or spec.surface_id in requested)
        and (allowed_renderers is None or spec.renderer in allowed_renderers)
    ]
    report_surfaces = [
        evaluate_surface(
            spec,
            context=policy.context,
            repo_root=repo_root,
            write=write,
            allow_missing_local_only=allow_missing_local_only,
        )
        for spec in selected
    ]
    return _build_surface_report_payload(policy, report_surfaces)


def _parse_repo_pack_metadata(
    payload: object,
    *,
    repo_root: Path,
) -> RepoPackMetadata:
    if not isinstance(payload, dict):
        return RepoPackMetadata(
            pack_id=repo_root.name,
            pack_version="0.0.0",
            product_name=repo_root.name,
            repo_name=repo_root.name,
        )
    return RepoPackMetadata(
        pack_id=str(payload.get("pack_id") or repo_root.name).strip(),
        pack_version=str(payload.get("pack_version") or "0.0.0").strip(),
        product_name=str(payload.get("product_name") or repo_root.name).strip(),
        repo_name=str(payload.get("repo_name") or repo_root.name).strip(),
    )


def _build_context(
    *,
    raw_context: object,
    metadata: RepoPackMetadata,
    warnings: list[str],
) -> dict[str, str]:
    context = {
        "repo_pack_id": metadata.pack_id,
        "repo_pack_version": metadata.pack_version,
        "product_name": metadata.product_name,
        "repo_name": metadata.repo_name,
    }
    if not isinstance(raw_context, dict):
        return context
    for key, value in raw_context.items():
        key_text = str(key).strip()
        if not key_text:
            warnings.append("surface_generation.context contained an empty key; skipped.")
            continue
        context[key_text] = _stringify_context_value(value)
    return context


def _stringify_context_value(value: object) -> str:
    if isinstance(value, list):
        return "\n".join(
            f"{index}. {item}" for index, item in enumerate(value, start=1)
        )
    return str(value).strip()


def _parse_surface_specs(
    payload: object,
    *,
    warnings: list[str],
) -> tuple[SurfaceSpec, ...]:
    if not isinstance(payload, list):
        warnings.append("surface_generation.surfaces is missing or not a list.")
        return ()
    specs: list[SurfaceSpec] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(payload, start=1):
        if not isinstance(entry, dict):
            warnings.append(
                f"surface_generation.surfaces[{index}] is not an object; skipped."
            )
            continue
        surface_id = str(entry.get("id") or "").strip()
        output_path = str(entry.get("output_path") or "").strip()
        renderer = str(entry.get("renderer") or "").strip()
        if not surface_id or not output_path or not renderer:
            warnings.append(
                "surface_generation.surfaces[{index}] is missing `id`, `renderer`, or `output_path`; skipped.".format(
                    index=index
                )
            )
            continue
        if surface_id in seen_ids:
            warnings.append(f"duplicate surface id `{surface_id}`; skipped later entry.")
            continue
        template_path = entry.get("template_path")
        template_value = str(template_path).strip() if template_path else None
        if renderer == "template_file" and not template_value:
            warnings.append(f"surface `{surface_id}` needs `template_path`; skipped.")
            continue
        required_contains = _parse_required_contains(
            entry.get("required_contains"),
            surface_id=surface_id,
            warnings=warnings,
        )
        specs.append(
            SurfaceSpec(
                surface_id=surface_id,
                surface_type=str(entry.get("surface_type") or "instruction").strip(),
                renderer=renderer,
                output_path=output_path,
                template_path=template_value,
                tracked=bool(entry.get("tracked", False)),
                local_only=bool(entry.get("local_only", False)),
                description=str(entry.get("description") or "").strip(),
                required_contains=required_contains,
            )
        )
        seen_ids.add(surface_id)
    return tuple(specs)


def _parse_required_contains(
    payload: object,
    *,
    surface_id: str,
    warnings: list[str],
) -> tuple[str, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        warnings.append(
            f"surface `{surface_id}` has non-list `required_contains`; ignored."
        )
        return ()
    items: list[str] = []
    for index, entry in enumerate(payload, start=1):
        text = str(entry).strip()
        if not text:
            warnings.append(
                f"surface `{surface_id}` has empty `required_contains[{index}]`; ignored."
            )
            continue
        items.append(text)
    return tuple(items)


def _build_unknown_surface_report(
    policy: SurfacePolicy,
    unknown: list[str],
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    report["command"] = "render-surfaces"
    report["ok"] = False
    report["policy_path"] = policy.policy_path
    report["warnings"] = list(policy.warnings)
    report["error"] = "unknown surface id(s): " + ", ".join(unknown)
    report["surfaces"] = []
    return report


def _build_surface_report_payload(
    policy: SurfacePolicy,
    report_surfaces: list[dict[str, Any]],
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    report["command"] = "render-surfaces"
    report["ok"] = all(bool(entry.get("ok", False)) for entry in report_surfaces)
    report["policy_path"] = policy.policy_path
    report["repo_pack_id"] = policy.metadata.pack_id
    report["repo_pack_version"] = policy.metadata.pack_version
    report["product_name"] = policy.metadata.product_name
    report["repo_name"] = policy.metadata.repo_name
    report["surface_count"] = len(report_surfaces)
    report["warnings"] = list(policy.warnings)
    report["surfaces"] = report_surfaces
    return report
