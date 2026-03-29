"""Resolution helpers for check-router repo-governance policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import REPO_ROOT
from ..governance.governed_doc_routing import resolve_governed_doc_routing
from ..repo_policy import load_repo_governance_section
from .check_router_constants import (
    BUNDLE_BY_LANE,
    DOCS_EXACT_PATHS,
    DOCS_PREFIXES,
    RELEASE_EXACT_PATHS,
    RELEASE_WORKFLOW_FILES,
    RISK_ADDONS,
    RUNTIME_EXACT_PATHS,
    RUNTIME_PREFIXES,
    TOOLING_EXACT_PATHS,
    TOOLING_MARKDOWN_PREFIXES,
    TOOLING_PREFIXES,
    CheckRouterConfig,
    RiskAddonSpec,
)
from .docs_check_policy import resolve_docs_check_policy


def _coerce_str_tuple(
    raw_value: Any,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(raw_value, list):
        return fallback
    values = tuple(str(item).strip() for item in raw_value if str(item).strip())
    return values or fallback


def _coerce_str_set(
    raw_value: Any,
    fallback: set[str],
) -> frozenset[str]:
    if not isinstance(raw_value, list):
        return frozenset(fallback)
    values = frozenset(str(item).strip() for item in raw_value if str(item).strip())
    return values or frozenset(fallback)


def _coerce_bundle_by_lane(raw_value: Any) -> dict[str, str]:
    if not isinstance(raw_value, dict):
        return dict(BUNDLE_BY_LANE)
    resolved = dict(BUNDLE_BY_LANE)
    for lane in BUNDLE_BY_LANE:
        override = str(raw_value.get(lane, "")).strip()
        if override:
            resolved[lane] = override
    return resolved


def _default_risk_addons() -> tuple[RiskAddonSpec, ...]:
    return tuple(
        RiskAddonSpec(
            id=str(spec["id"]),
            label=str(spec["label"]),
            tokens=tuple(spec["tokens"]),
            commands=tuple(spec["commands"]),
        )
        for spec in RISK_ADDONS
    )


def _coerce_risk_addons(raw_value: Any) -> tuple[RiskAddonSpec, ...]:
    if not isinstance(raw_value, list):
        return _default_risk_addons()
    resolved: list[RiskAddonSpec] = []
    for item in raw_value:
        if not isinstance(item, dict):
            continue
        addon_id = str(item.get("id", "")).strip()
        label = str(item.get("label", "")).strip()
        tokens = tuple(
            str(token).strip()
            for token in item.get("tokens", [])
            if str(token).strip()
        )
        commands = tuple(
            str(command).strip()
            for command in item.get("commands", [])
            if str(command).strip()
        )
        if addon_id and label and tokens and commands:
            resolved.append(
                RiskAddonSpec(
                    id=addon_id,
                    label=label,
                    tokens=tokens,
                    commands=commands,
                )
            )
    return tuple(resolved) or _default_risk_addons()


def _append_unique(values: list[str], candidate: str) -> None:
    text = str(candidate or "").strip()
    if text and text not in values:
        values.append(text)


def _prefixes_from_user_docs(user_docs: tuple[str, ...]) -> tuple[str, ...]:
    prefixes: list[str] = []
    for path in user_docs:
        parent = Path(path).parent.as_posix()
        if parent in {".", ""}:
            continue
        _append_unique(prefixes, f"{parent.rstrip('/')}/")
    return tuple(prefixes)


def resolve_check_router_config(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | None = None,
) -> CheckRouterConfig:
    """Resolve repo-specific routing rules from the shared repo policy file."""
    section, warnings, resolved_policy_path = load_repo_governance_section(
        "check_router",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    routing = resolve_governed_doc_routing(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    docs_policy = resolve_docs_check_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    docs_exact_default = tuple(docs_policy.user_docs)
    docs_prefix_default = _prefixes_from_user_docs(docs_policy.user_docs)
    return CheckRouterConfig(
        bundle_by_lane=_coerce_bundle_by_lane(section.get("bundle_by_lane")),
        release_exact_paths=_coerce_str_set(
            section.get("release_exact_paths"),
            RELEASE_EXACT_PATHS,
        ),
        release_workflow_files=_coerce_str_set(
            section.get("release_workflow_files"),
            RELEASE_WORKFLOW_FILES,
        ),
        tooling_exact_paths=_coerce_str_set(
            section.get("tooling_exact_paths"),
            TOOLING_EXACT_PATHS,
        ),
        tooling_prefixes=_coerce_str_tuple(
            section.get("tooling_prefixes"),
            TOOLING_PREFIXES,
        ),
        tooling_markdown_prefixes=_coerce_str_tuple(
            section.get("tooling_markdown_prefixes"),
            TOOLING_MARKDOWN_PREFIXES,
        ),
        governed_tooling_exact_paths=frozenset(routing.governed_tooling_docs),
        governed_tooling_prefixes=routing.governed_tooling_prefixes,
        runtime_prefixes=_coerce_str_tuple(
            section.get("runtime_prefixes"),
            RUNTIME_PREFIXES,
        ),
        runtime_exact_paths=_coerce_str_set(
            section.get("runtime_exact_paths"),
            RUNTIME_EXACT_PATHS,
        ),
        docs_prefixes=_coerce_str_tuple(
            section.get("docs_prefixes"),
            docs_prefix_default,
        ),
        docs_exact_paths=_coerce_str_set(
            section.get("docs_exact_paths"),
            set(docs_exact_default),
        ),
        risk_addons=_coerce_risk_addons(section.get("risk_addons")),
        policy_path=str(resolved_policy_path),
        warnings=warnings,
    )
