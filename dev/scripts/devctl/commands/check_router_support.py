"""Path classification and risk add-on helpers for check-router."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dev.scripts.devctl.runtime.decision_explainability import (
    rejected_rule_trace as _probe_rejected_rule,
    rule_match_evidence as _probe_rule_match,
)
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


def _match_evidence(rule_id: str, summary: str, *evidence: str) -> dict[str, object]:
    return _probe_rule_match(rule_id, summary, *evidence).to_dict()


def _rejected_rule_trace(
    rule_id: str,
    summary: str,
    rejected_because: str,
    *evidence: str,
) -> dict[str, object]:
    return _probe_rejected_rule(rule_id, summary, rejected_because, *evidence).to_dict()


@dataclass(frozen=True, slots=True)
class LaneEvidence:
    lane: str
    changed_paths: tuple[str, ...]
    release_paths: tuple[str, ...]
    tooling_paths: tuple[str, ...]
    runtime_paths: tuple[str, ...]
    docs_paths: tuple[str, ...]
    unknown_paths: tuple[str, ...]


def _is_release_path(path: str, config: CheckRouterConfig) -> bool:
    return path in config.release_exact_paths or (
        path.startswith(".github/workflows/")
        and path.rsplit("/", 1)[-1] in config.release_workflow_files
    )


def _is_tooling_path(path: str, config: CheckRouterConfig) -> bool:
    return (
        path in config.governed_tooling_exact_paths
        or (
            path.endswith(".md")
            and any(path.startswith(prefix) for prefix in config.governed_tooling_prefixes)
        )
        or path in config.tooling_exact_paths
        or any(path.startswith(prefix) for prefix in config.tooling_prefixes)
        or any(
            path.startswith(prefix) and path.endswith(".md")
            for prefix in config.tooling_markdown_prefixes
        )
    )


def _is_runtime_path(path: str, config: CheckRouterConfig) -> bool:
    return any(path.startswith(prefix) for prefix in config.runtime_prefixes) or path in config.runtime_exact_paths


def _is_docs_path(path: str, config: CheckRouterConfig) -> bool:
    return path in config.docs_exact_paths or any(
        path.startswith(prefix) for prefix in config.docs_prefixes
    ) or (
        path.endswith(".md")
        and not (
            _is_release_path(path, config)
            or _is_tooling_path(path, config)
            or _is_runtime_path(path, config)
        )
    )


def _classification_result(
    *,
    lane: str,
    reasons: list[str],
    categories: dict[str, list[str]],
    rule_summary: str,
    match_evidence: list[dict[str, object]],
    rejected_rule_traces: list[dict[str, object]],
) -> dict[str, object]:
    return dict(
        lane=lane,
        reasons=reasons,
        categories=categories,
        rule_summary=rule_summary,
        match_evidence=match_evidence,
        rejected_rule_traces=rejected_rule_traces,
    )


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
        return _classification_result(
            lane="docs",
            reasons=["No changed paths detected; defaulting to docs lane."],
            categories={name: [] for name in ("release_paths", "tooling_paths", "runtime_paths", "docs_paths", "unknown_paths")},
            rule_summary="Defaulted to the docs lane because git reported no changed paths for router classification.",
            match_evidence=[
                _match_evidence(
                    "check_router.no_changed_paths_defaults_to_docs",
                    "The router falls back to the docs lane when there are no changed paths to classify.",
                    "changed_paths=0",
                )
            ],
            rejected_rule_traces=[],
        )

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

    rule_summary, match_evidence, rejected_rule_traces = _lane_explanation(
        LaneEvidence(
            lane=lane,
            changed_paths=tuple(changed_paths),
            release_paths=tuple(release_paths),
            tooling_paths=tuple(tooling_paths),
            runtime_paths=tuple(runtime_paths),
            docs_paths=tuple(docs_paths),
            unknown_paths=tuple(unknown_paths),
        )
    )

    return _classification_result(
        lane=lane,
        reasons=reasons,
        categories={
            "release_paths": sorted(release_paths),
            "tooling_paths": sorted(tooling_paths),
            "runtime_paths": sorted(runtime_paths),
            "docs_paths": sorted(docs_paths),
            "unknown_paths": sorted(unknown_paths),
        },
        rule_summary=rule_summary,
        match_evidence=match_evidence,
        rejected_rule_traces=rejected_rule_traces,
    )


def _lane_explanation(
    evidence: LaneEvidence,
) -> tuple[str, list[dict[str, object]], list[dict[str, object]]]:
    lane = evidence.lane
    release_paths = list(evidence.release_paths)
    tooling_paths = list(evidence.tooling_paths)
    runtime_paths = list(evidence.runtime_paths)
    docs_paths = list(evidence.docs_paths)
    unknown_paths = list(evidence.unknown_paths)
    changed_paths = list(evidence.changed_paths)
    if lane == "release":
        return (
            "Selected the release lane because release-sensitive files outrank every other lane.",
            [
                _match_evidence(
                    "check_router.release_paths",
                    "At least one release-sensitive file changed, so the release lane wins immediately.",
                    "release_paths=" + ", ".join(sample_paths(release_paths)),
                )
            ],
            [
                _rejected_rule_trace(
                    "check_router.tooling_paths",
                    "Route to tooling when governed tooling/process files changed.",
                    "Release-sensitive paths outrank tooling paths.",
                    "tooling_paths=" + ", ".join(sample_paths(tooling_paths)),
                )
                if tooling_paths
                else _rejected_rule_trace(
                    "check_router.tooling_paths",
                    "Route to tooling when governed tooling/process files changed.",
                    "No tooling-path match was needed after the release match.",
                ),
                _rejected_rule_trace(
                    "check_router.runtime_paths",
                    "Route to runtime when runtime source changed and no higher lane matched.",
                    "Release-sensitive paths outrank runtime paths.",
                    "runtime_paths=" + ", ".join(sample_paths(runtime_paths)),
                )
                if runtime_paths
                else _rejected_rule_trace(
                    "check_router.runtime_paths",
                    "Route to runtime when runtime source changed and no higher lane matched.",
                    "No runtime-path match was needed after the release match.",
                ),
            ],
        )
    if lane == "tooling" and tooling_paths:
        return (
            "Selected the tooling lane because governed tooling/process/doc-authority paths changed, and that lane outranks runtime/docs routing.",
            [_match_evidence("check_router.tooling_paths", "Governed tooling/process/CI paths changed, so the tooling lane applies.", "tooling_paths=" + ", ".join(sample_paths(tooling_paths)))],
            [
                _rejected_rule_trace("check_router.release_paths", "Route to release when release-sensitive files changed.", "No release-sensitive path matched this change set."),
                _rejected_rule_trace("check_router.runtime_paths", "Route to runtime when runtime source changed and no higher lane matched.", "Tooling precedence is stricter than runtime when both appear in the same slice.", "runtime_paths=" + ", ".join(sample_paths(runtime_paths))) if runtime_paths else _rejected_rule_trace("check_router.docs_only", "Route to docs when every changed path is a user-facing document.", "This change set includes governed tooling/process files, so it is not docs-only.", f"docs_paths={len(docs_paths)}", f"changed_paths={len(changed_paths)}"),
            ],
        )
    if lane == "tooling":
        return (
            "Escalated to the tooling lane because unknown paths appeared, so the router chose the stricter governed bundle instead of guessing a narrower lane.",
            [_match_evidence("check_router.unknown_paths_escalate_to_tooling", "Unknown paths trigger the stricter tooling lane to avoid missing governance checks.", "unknown_paths=" + ", ".join(sample_paths(unknown_paths)))],
            [_rejected_rule_trace("check_router.docs_only", "Route to docs when every changed path is a user-facing document.", "Unknown paths mean the router cannot honestly claim this is docs-only.", f"docs_paths={len(docs_paths)}", f"changed_paths={len(changed_paths)}")],
        )
    if lane == "runtime":
        return (
            "Selected the runtime lane because runtime source changed and no release or tooling rule overrode it.",
            [_match_evidence("check_router.runtime_paths", "Runtime source changed, so the runtime bundle is required.", "runtime_paths=" + ", ".join(sample_paths(runtime_paths)))],
            [
                _rejected_rule_trace("check_router.release_paths", "Route to release when release-sensitive files changed.", "No release-sensitive path matched this change set."),
                _rejected_rule_trace("check_router.tooling_paths", "Route to tooling when governed tooling/process files changed.", "No governed tooling path matched this change set."),
            ],
        )
    return (
        "Selected the docs lane because every changed path is a user-facing document and no higher-priority tooling/runtime/release rule matched.",
        [_match_evidence("check_router.docs_only", "The entire change set stayed inside user-facing docs, so the docs bundle is sufficient.", f"docs_paths={len(docs_paths)}", f"changed_paths={len(changed_paths)}")],
        [
            _rejected_rule_trace("check_router.release_paths", "Route to release when release-sensitive files changed.", "No release-sensitive path matched this change set."),
            _rejected_rule_trace("check_router.tooling_paths", "Route to tooling when governed tooling/process files changed.", "No governed tooling path matched this change set."),
            _rejected_rule_trace("check_router.runtime_paths", "Route to runtime when runtime source changed and no higher lane matched.", "No runtime source path matched this change set."),
        ],
    )


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
