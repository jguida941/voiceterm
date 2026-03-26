"""Routing and warm-ref helpers for startup work-intake."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..governance.push_routing import PushRefRoutingState, resolve_preflight_since_ref
from .project_governance import PlanRegistryEntry, ProjectGovernance
from .review_state_locator import resolved_review_state_relative_path
from .review_state_models import ReviewState
from .work_intake_models import IntakeRoutingState


def build_routing(
    repo_root: Path,
    *,
    governance: ProjectGovernance,
    advisory_action: str,
) -> IntakeRoutingState:
    """Build startup routing hints from live ProjectGovernance fields."""
    startup_reads = tuple(
        path for path in governance.startup_order if path and (repo_root / path).exists()
    )
    workflow_profiles = tuple(
        profile for profile in governance.workflow_profiles if profile
    )
    push_defaults = _push_defaults(governance.command_routing_defaults)
    if "current_branch" not in push_defaults:
        push_defaults["current_branch"] = governance.repo_identity.current_branch
    if "upstream_ref" not in push_defaults:
        push_defaults["upstream_ref"] = governance.push_enforcement.upstream_ref
    post_push_bundle = _mapping_text(_mapping(push_defaults.get("post_push")).get("bundle"))
    return IntakeRoutingState(
        startup_reads=startup_reads,
        workflow_profiles=workflow_profiles,
        selected_workflow_profile=_selected_profile(
            workflow_profiles,
            advisory_action=advisory_action,
            post_push_bundle=post_push_bundle,
        ),
        default_remote=_mapping_text(push_defaults.get("default_remote")),
        development_branch=_mapping_text(push_defaults.get("development_branch")),
        preflight_command=_preflight_command(push_defaults),
        post_push_bundle=post_push_bundle,
    )


def scope_hints(
    entry: PlanRegistryEntry | None,
    review_state: ReviewState | None,
) -> tuple[str, ...]:
    """Return the small set of scope hints carried by the intake packet."""
    hints: list[str] = []
    for value in (
        entry.scope if entry is not None else "",
        review_state.current_session.last_reviewed_scope if review_state is not None else "",
    ):
        value = value.strip()
        if value and value not in hints:
            hints.append(value)
    return tuple(hints)


def warm_refs(
    repo_root: Path,
    *,
    governance: ProjectGovernance,
    active_entry: PlanRegistryEntry | None,
    routing: IntakeRoutingState,
) -> tuple[str, ...]:
    """Return the bounded set of warm refs for startup reading."""
    refs: list[str] = list(routing.startup_reads)
    _append_existing_ref(
        refs,
        repo_root,
        active_entry.path if active_entry is not None else "",
    )
    _append_existing_ref(refs, repo_root, governance.plan_registry.tracker_path)
    _append_existing_ref(refs, repo_root, governance.plan_registry.index_path)
    _append_existing_ref(refs, repo_root, governance.docs_authority)
    _append_existing_ref(
        refs,
        repo_root,
        resolved_review_state_relative_path(
            repo_root,
            governance=governance,
        ),
    )
    _append_existing_ref(refs, repo_root, governance.bridge_config.bridge_path.strip())
    return tuple(refs)


def writeback_sinks(
    governance: ProjectGovernance,
    active_entry: PlanRegistryEntry | None,
) -> tuple[str, ...]:
    """Return authoritative writeback sinks for startup follow-up work."""
    sinks: list[str] = []
    for candidate in (
        active_entry.path if active_entry is not None else "",
        governance.plan_registry.tracker_path,
    ):
        candidate = candidate.strip()
        if candidate and candidate not in sinks:
            sinks.append(candidate)
    return tuple(sinks)


def _append_existing_ref(refs: list[str], repo_root: Path, candidate: str) -> None:
    candidate = candidate.strip()
    if not candidate or candidate in refs:
        return
    if (repo_root / candidate).exists():
        refs.append(candidate)


def _push_defaults(
    command_routing_defaults: dict[str, object] | None,
) -> dict[str, object]:
    if command_routing_defaults is None:
        return {}
    push_defaults = command_routing_defaults.get("push")
    return dict(push_defaults) if isinstance(push_defaults, dict) else {}


def _preflight_command(push_defaults: dict[str, object]) -> str:
    preflight = _mapping(push_defaults.get("preflight"))
    command = _mapping_text(preflight.get("command"))
    if not command:
        return ""
    remote = _mapping_text(push_defaults.get("default_remote")) or "origin"
    development_branch = _mapping_text(push_defaults.get("development_branch")) or "main"
    template = _mapping_text(preflight.get("since_ref_template"))
    since_ref = resolve_preflight_since_ref(
        remote=remote,
        development_branch=development_branch,
        release_branch=(
            _mapping_text(push_defaults.get("release_branch"))
            or development_branch
        ),
        since_ref_template=template,
        route_state=PushRefRoutingState(
            current_branch=_mapping_text(push_defaults.get("current_branch")),
            upstream_ref=_mapping_text(push_defaults.get("upstream_ref")),
        ),
    )
    command_parts = [
        "python3",
        "dev/scripts/devctl.py",
        command,
        "--since-ref",
        since_ref,
    ]
    if bool(preflight.get("execute")):
        command_parts.append("--execute")
    return " ".join(command_parts)


def _selected_profile(
    workflow_profiles: tuple[str, ...],
    *,
    advisory_action: str,
    post_push_bundle: str,
) -> str:
    if advisory_action == "push_allowed" and post_push_bundle in workflow_profiles:
        return post_push_bundle
    if "bundle.tooling" in workflow_profiles:
        return "bundle.tooling"
    if post_push_bundle and post_push_bundle in workflow_profiles:
        return post_push_bundle
    return workflow_profiles[0] if workflow_profiles else ""


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _mapping_text(value: Any) -> str:
    return str(value or "").strip()


__all__ = ["build_routing", "scope_hints", "warm_refs", "writeback_sinks"]
