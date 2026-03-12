"""Scope discovery and normalization helpers for quality-policy resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .quality_policy import RepoCapabilities

SCOPE_ATTRIBUTE_MAP = {
    "python_guard": "python_guard_roots",
    "python_probe": "python_probe_roots",
    "rust_guard": "rust_guard_roots",
    "rust_probe": "rust_probe_roots",
}

COMMON_PYTHON_SCOPE_CANDIDATES = (
    Path("src"),
    Path("app"),
    Path("scripts"),
    Path("tools"),
    Path("dev/scripts"),
    Path("python"),
)


@dataclass(frozen=True, slots=True)
class ResolvedQualityScopes:
    """Resolved repo-relative source roots used by guards and review probes."""

    python_guard_roots: tuple[Path, ...] = ()
    python_probe_roots: tuple[Path, ...] = ()
    rust_guard_roots: tuple[Path, ...] = ()
    rust_probe_roots: tuple[Path, ...] = ()


def _discover_rust_scope_roots(
    repo_root: Path,
    *,
    capabilities: RepoCapabilities,
) -> tuple[Path, ...]:
    if not capabilities.rust:
        return ()
    roots: set[Path] = set()
    candidate_manifests = (
        repo_root / "Cargo.toml",
        *repo_root.glob("*/Cargo.toml"),
        *repo_root.glob("*/*/Cargo.toml"),
    )
    for manifest in candidate_manifests:
        if not manifest.is_file():
            continue
        src_root = manifest.parent / "src"
        if src_root.is_dir():
            roots.add(src_root.relative_to(repo_root))
    if roots:
        return tuple(sorted(roots))
    return (Path("src"),) if (repo_root / "src").is_dir() else ()


def resolve_quality_scopes(
    payload: dict[str, Any] | None,
    *,
    repo_root: Path,
    capabilities: RepoCapabilities,
    warnings: list[str],
    has_python_sources,
) -> ResolvedQualityScopes:
    """Resolve repo-relative scope roots for guards and probes."""
    if capabilities.python:
        python_defaults = tuple(
            candidate
            for candidate in COMMON_PYTHON_SCOPE_CANDIDATES
            if (repo_root / candidate).is_dir() and has_python_sources(repo_root / candidate)
        )
        if not python_defaults and has_python_sources(repo_root):
            python_defaults = (Path("."),)
    else:
        python_defaults = ()
    rust_defaults = _discover_rust_scope_roots(
        repo_root,
        capabilities=capabilities,
    )
    raw_scopes = payload.get("quality_scopes") if payload else None
    if not isinstance(raw_scopes, dict):
        return ResolvedQualityScopes(
            python_guard_roots=python_defaults,
            python_probe_roots=python_defaults,
            rust_guard_roots=rust_defaults,
            rust_probe_roots=rust_defaults,
        )

    def resolve_scope_roots(
        scope_name: str,
        fallback: tuple[Path, ...],
    ) -> tuple[Path, ...]:
        raw_value = raw_scopes.get(scope_name)
        if not isinstance(raw_value, list):
            return fallback
        roots: list[Path] = []
        seen: set[Path] = set()
        for item in raw_value:
            raw = str(item).strip()
            if not raw:
                continue
            candidate = Path(raw).expanduser()
            if candidate.is_absolute():
                try:
                    candidate = candidate.relative_to(repo_root)
                except ValueError:
                    warnings.append("quality scope " f"`{scope_name}` ignored absolute path outside repo: {raw}")
                    continue
            normalized = Path(".") if candidate in {Path(""), Path(".")} else candidate
            if normalized.parts and normalized.parts[0] == "..":
                warnings.append(f"quality scope `{scope_name}` ignored path escaping repo root: {raw}")
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            roots.append(normalized)
        return tuple(roots)

    return ResolvedQualityScopes(
        python_guard_roots=resolve_scope_roots(
            "python_guard_roots",
            python_defaults,
        ),
        python_probe_roots=resolve_scope_roots(
            "python_probe_roots",
            python_defaults,
        ),
        rust_guard_roots=resolve_scope_roots("rust_guard_roots", rust_defaults),
        rust_probe_roots=resolve_scope_roots("rust_probe_roots", rust_defaults),
    )
