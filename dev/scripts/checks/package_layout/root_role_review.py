"""Role-aware root organization review helpers for package-layout."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import RootRoleRule, detect_compatibility_shim
else:  # pragma: no cover - standalone script fallback
    from bootstrap import RootRoleRule, detect_compatibility_shim


def _matches_any(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(name, pattern) for pattern in patterns)


def _classify_path(path: Path, rule: RootRoleRule) -> str:
    if detect_compatibility_shim(
        path,
        namespace_subdir="",
        shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
        shim_required_metadata_fields=rule.shim_required_metadata_fields,
    ).is_valid:
        return "compat_shim"
    name = path.name
    if _matches_any(name, rule.generated_artifact_globs):
        return "generated_artifact"
    if _matches_any(name, rule.doc_authority_globs):
        return "doc_authority"
    if _matches_any(name, rule.public_entrypoint_globs):
        return "public_entrypoint"
    stem = path.stem
    if any(stem.endswith(suffix) for suffix in rule.support_suffixes):
        return "support_module"
    return "implementation_module"


def _sample_paths(paths: list[Path], limit: int = 3) -> list[str]:
    return [path.as_posix() for path in sorted(paths)[:limit]]


def collect_root_role_findings_from_rules(
    *,
    repo_root: Path,
    root_role_rules: tuple[RootRoleRule, ...],
) -> tuple[list[dict], int]:
    """Return advisory organization findings for configured flat roots."""
    findings: list[dict] = []
    for rule in root_role_rules:
        root_dir = repo_root / rule.root
        if not root_dir.exists() or not root_dir.is_dir():
            continue
        files = [
            path.relative_to(repo_root)
            for path in root_dir.iterdir()
            if path.is_file() and any(fnmatch(path.name, pattern) for pattern in rule.include_globs)
        ]
        role_paths = {
            "compat_shim": [],
            "public_entrypoint": [],
            "generated_artifact": [],
            "doc_authority": [],
            "support_module": [],
            "implementation_module": [],
        }
        for relative in sorted(files):
            role = _classify_path(repo_root / relative, rule)
            role_paths[role].append(relative)
        support_count = len(role_paths["support_module"])
        implementation_count = len(role_paths["implementation_module"])
        if (
            support_count <= rule.max_support_modules
            and implementation_count <= rule.max_implementation_modules
        ):
            continue
        findings.append(
            {
                "root": rule.root.as_posix(),
                "total_files": len(files),
                "compat_shim_files": len(role_paths["compat_shim"]),
                "public_entrypoint_files": len(role_paths["public_entrypoint"]),
                "generated_artifact_files": len(role_paths["generated_artifact"]),
                "doc_authority_files": len(role_paths["doc_authority"]),
                "support_module_files": support_count,
                "implementation_module_files": implementation_count,
                "max_support_modules": rule.max_support_modules,
                "max_implementation_modules": rule.max_implementation_modules,
                "support_examples": _sample_paths(role_paths["support_module"]),
                "implementation_examples": _sample_paths(
                    role_paths["implementation_module"]
                ),
                "guidance": rule.guidance,
                "policy_source": f"root_role:{rule.root.as_posix()}",
            }
        )
    return findings, len(root_role_rules)
