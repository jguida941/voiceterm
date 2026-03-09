"""Path classification and risk add-on helpers for check-router."""

from __future__ import annotations

from .check_router_constants import (
    BUNDLE_BY_LANE,
    DOCS_EXACT_PATHS,
    DOCS_PREFIXES,
    RELEASE_EXACT_PATHS,
    RELEASE_WORKFLOW_FILES,
    RISK_ADDONS,
    RUNTIME_PREFIXES,
    TOOLING_EXACT_PATHS,
    TOOLING_PREFIXES,
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


def _is_release_path(path: str) -> bool:
    if path in RELEASE_EXACT_PATHS:
        return True
    if not path.startswith(".github/workflows/"):
        return False
    return path.rsplit("/", 1)[-1] in RELEASE_WORKFLOW_FILES


def _is_tooling_path(path: str) -> bool:
    if path in TOOLING_EXACT_PATHS:
        return True
    if any(path.startswith(prefix) for prefix in TOOLING_PREFIXES):
        return True
    if path.startswith("dev/active/") and path.endswith(".md"):
        return True
    if path.startswith("dev/config/") and path.endswith(".md"):
        return True
    return False


def _is_runtime_path(path: str) -> bool:
    if any(path.startswith(prefix) for prefix in RUNTIME_PREFIXES):
        return True
    if path in {"rust/Cargo.toml", "rust/Cargo.lock", "rust/clippy.toml"}:
        return True
    return False


def _is_docs_path(path: str) -> bool:
    if path in DOCS_EXACT_PATHS:
        return True
    if any(path.startswith(prefix) for prefix in DOCS_PREFIXES):
        return True
    if path.endswith(".md") and not (
        _is_release_path(path) or _is_tooling_path(path) or _is_runtime_path(path)
    ):
        return True
    return False


def classify_lane(changed_paths: list[str]) -> dict:
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

    release_paths = [path for path in changed_paths if _is_release_path(path)]
    tooling_paths = [path for path in changed_paths if _is_tooling_path(path)]
    runtime_paths = [path for path in changed_paths if _is_runtime_path(path)]
    docs_paths = [path for path in changed_paths if _is_docs_path(path)]
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


def detect_risk_addons(changed_paths: list[str]) -> list[dict]:
    addons: list[dict] = []
    for spec in RISK_ADDONS:
        matched_paths = [
            path
            for path in changed_paths
            if any(token in path for token in spec["tokens"])
        ]
        if not matched_paths:
            continue
        addons.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "matched_paths": sorted(set(matched_paths)),
                "commands": list(spec["commands"]),
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
