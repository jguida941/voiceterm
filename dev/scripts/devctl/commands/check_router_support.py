"""Path classification and risk add-on helpers for check-router."""

from __future__ import annotations

from pathlib import Path

from ..config import REPO_ROOT
from .check_router_constants import (
    BUNDLE_BY_LANE,
    CheckRouterConfig,
    resolve_check_router_config,
)

__all__ = [
    "BUNDLE_BY_LANE",
    "classify_lane",
    "dedupe_commands",
    "detect_risk_addons",
    "sample_paths",
]


def sample_paths(paths: list[str], *, limit: int = 8) -> list[str]:
    return sorted(paths)[:limit]


def _is_release_path(path: str, config: CheckRouterConfig) -> bool:
    if path in config.release_exact_paths:
        return True
    if not path.startswith(".github/workflows/"):
        return False
    return path.rsplit("/", 1)[-1] in config.release_workflow_files


def _is_tooling_path(path: str, config: CheckRouterConfig) -> bool:
    if path in config.governed_tooling_exact_paths:
        return True
    if path.endswith(".md") and any(
        path.startswith(prefix) for prefix in config.governed_tooling_prefixes
    ):
        return True
    if path in config.tooling_exact_paths:
        return True
    if any(path.startswith(prefix) for prefix in config.tooling_prefixes):
        return True
    if any(
        path.startswith(prefix) and path.endswith(".md")
        for prefix in config.tooling_markdown_prefixes
    ):
        return True
    return False


def _is_runtime_path(path: str, config: CheckRouterConfig) -> bool:
    if any(path.startswith(prefix) for prefix in config.runtime_prefixes):
        return True
    if path in config.runtime_exact_paths:
        return True
    return False


def _is_docs_path(path: str, config: CheckRouterConfig) -> bool:
    if path in config.docs_exact_paths:
        return True
    if any(path.startswith(prefix) for prefix in config.docs_prefixes):
        return True
    if path.endswith(".md") and not (
        _is_release_path(path, config)
        or _is_tooling_path(path, config)
        or _is_runtime_path(path, config)
    ):
        return True
    return False


def classify_lane(
    changed_paths: list[str],
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> dict:
    config = resolve_check_router_config(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    if not changed_paths:
        lane = "docs"
        reasons = ["No changed paths detected; defaulting to docs lane."]
        categories = {
            "release_paths": [],
            "tooling_paths": [],
            "runtime_paths": [],
            "docs_paths": [],
            "unknown_paths": [],
        }
        return {"lane": lane, "reasons": reasons, "categories": categories}

    release_paths = [path for path in changed_paths if _is_release_path(path, config)]
    tooling_paths = [path for path in changed_paths if _is_tooling_path(path, config)]
    runtime_paths = [path for path in changed_paths if _is_runtime_path(path, config)]
    docs_paths = [path for path in changed_paths if _is_docs_path(path, config)]
    unknown_paths = [
        path
        for path in changed_paths
        if path not in set(release_paths + tooling_paths + runtime_paths + docs_paths)
    ]

    reasons: list[str] = []
    if release_paths:
        lane = "release"
        reasons.append(
            "Release-sensitive files changed: " + ", ".join(sample_paths(release_paths))
        )
    elif tooling_paths:
        lane = "tooling"
        reasons.append(
            "Tooling/process/CI files changed: "
            + ", ".join(sample_paths(tooling_paths))
        )
    elif runtime_paths:
        lane = "runtime"
        reasons.append(
            "Runtime source changed: " + ", ".join(sample_paths(runtime_paths))
        )
    elif docs_paths and len(docs_paths) == len(changed_paths):
        lane = "docs"
        reasons.append("Docs-only change set detected.")
    else:
        lane = "tooling"
        reasons.append(
            "Unknown paths detected; escalating to stricter tooling lane: "
            + ", ".join(sample_paths(unknown_paths))
        )

    return {
        "lane": lane,
        "reasons": reasons,
        "categories": {
            "release_paths": sorted(release_paths),
            "tooling_paths": sorted(tooling_paths),
            "runtime_paths": sorted(runtime_paths),
            "docs_paths": sorted(docs_paths),
            "unknown_paths": sorted(unknown_paths),
        },
    }


def detect_risk_addons(
    changed_paths: list[str],
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> list[dict]:
    config = resolve_check_router_config(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    addons: list[dict] = []
    for spec in config.risk_addons:
        matched_paths = [
            path
            for path in changed_paths
            if any(token in path for token in spec.tokens)
        ]
        if not matched_paths:
            continue
        addons.append(
            {
                "id": spec.id,
                "label": spec.label,
                "matched_paths": sorted(set(matched_paths)),
                "commands": list(spec.commands),
            }
        )
    return addons


def dedupe_commands(command_rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in command_rows:
        key = " ".join(row["command"].split())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped
