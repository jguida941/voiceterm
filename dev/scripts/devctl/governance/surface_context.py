"""Derived context helpers for governed surface rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

try:
    from dev.scripts.checks.code_shape_function_exceptions import (
        FUNCTION_LANGUAGE_DEFAULTS,
    )
    from dev.scripts.checks.code_shape_policy import LANGUAGE_POLICIES
except ImportError:  # pragma: no cover - script-package fallback
    from checks.code_shape_function_exceptions import FUNCTION_LANGUAGE_DEFAULTS
    from checks.code_shape_policy import LANGUAGE_POLICIES

from .task_router_contract import render_task_router_table_markdown


def derive_surface_context(
    *,
    policy_path: str | Path | None,
    warnings: list[str],
    seed_context: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return render-time context derived from typed router and guard code."""
    from ..commands.check_router_constants import resolve_check_router_config

    router_config = resolve_check_router_config(
        policy_path=None if policy_path is None else str(policy_path)
    )
    for warning in router_config.warnings:
        if warning not in warnings:
            warnings.append(warning)
    docs = dict(seed_context or {})
    process_doc = docs.get("process_doc", "AGENTS.md")
    execution_tracker_doc = docs.get(
        "execution_tracker_doc",
        "dev/active/MASTER_PLAN.md",
    )
    active_registry_doc = docs.get(
        "active_registry_doc",
        "dev/active/INDEX.md",
    )
    development_doc = docs.get(
        "development_doc",
        "dev/guides/DEVELOPMENT.md",
    )
    return {
        "bootstrap_steps": render_bootstrap_steps(
            process_doc=process_doc,
            execution_tracker_doc=execution_tracker_doc,
            active_registry_doc=active_registry_doc,
        ),
        "key_commands_block": render_key_commands_block(),
        "post_edit_verification_steps": render_post_edit_verification_steps(
            bundle_by_lane=router_config.bundle_by_lane,
            process_doc=process_doc,
            development_doc=development_doc,
        ),
        "task_router_block": render_task_router_table_markdown(
            bundle_by_lane=router_config.bundle_by_lane
        ),
        "guard_limits_block": render_guard_limits_block(),
    }


def render_bootstrap_steps(
    *,
    process_doc: str,
    execution_tracker_doc: str,
    active_registry_doc: str,
) -> str:
    """Render the AI session-start bootstrap checklist."""
    steps = (
        "Step 0 for any edit, validation, or repo-owned launcher session: run `python3 dev/scripts/devctl.py startup-context --format summary`. If it exits non-zero, checkpoint or repair the state before editing or launching more work. Do not treat a user summary, stale chat continuity, or memory as a substitute for this receipt.",
        "Run `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md` for a slim startup packet: repo identity, active plans, hotspots, key commands, and recent quality signals when artifacts exist.",
        "Do not echo bootstrap packets back into chat by default. Keep any chat bootstrap acknowledgement to blocker state plus next step; inspect repo-owned artifacts or terminal output when more detail is needed.",
        f"Follow the deep links from steps 1-2 when full authority is needed: read `{process_doc}`, `{active_registry_doc}`, and `{execution_tracker_doc}`.",
        "Use `python3 dev/scripts/devctl.py context-graph --query '<term>' --format md` for bounded subgraphs instead of opening whole docs when only one file, guard, command, or MP scope is relevant.",
        "Use `python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md` when the slice needs proof over saved graph baselines.",
        "Only load additional active docs when the task class requires them, but do not treat `startup-context` as optional escalation once you intend to mutate the repo.",
    )
    return _render_numbered_lines(steps)


def render_key_commands_block() -> str:
    """Render the curated AI-facing command block."""
    sections = (
        (
            "Slim bootstrap packet",
            "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
        ),
        (
            "Typed startup packet",
            "python3 dev/scripts/devctl.py startup-context --format summary",
        ),
        (
            "Governed push execute",
            "python3 dev/scripts/devctl.py push --execute",
        ),
        (
            "Saved graph diff",
            "python3 dev/scripts/devctl.py context-graph --mode diff --from previous --to latest --format md",
        ),
        (
            "Quality policy catalog",
            "python3 dev/scripts/devctl.py quality-policy --format md",
        ),
        (
            "Routed CI guard bundle",
            "python3 dev/scripts/devctl.py check --profile ci",
        ),
        (
            "Probe hotspot packet",
            "python3 dev/scripts/devctl.py probe-report --format md",
        ),
        (
            "Governance review summary",
            "python3 dev/scripts/devctl.py governance-review --format md",
        ),
        (
            "Governance review record",
            "python3 dev/scripts/devctl.py governance-review --record --signal-type probe --check-id probe_exception_quality --verdict fixed --path dev/scripts/devctl/example.py --line 41 --finding-class rule_quality --recurrence-risk recurring --prevention-surface probe --guidance-id probe_exception_quality@dev/scripts/devctl/example.py:41 --guidance-followed true --format md",
        ),
        (
            "Review status",
            "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
        ),
        (
            "Review ensure follow",
            "python3 dev/scripts/devctl.py review-channel --action ensure --follow --terminal none --format json",
        ),
        (
            "Reviewer checkpoint",
            "python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason review-pass --checkpoint-payload-file /tmp/reviewer-checkpoint.json --expected-instruction-revision <live-revision> --terminal none --format md",
        ),
        (
            "Implementer wait",
            "python3 dev/scripts/devctl.py review-channel --action implementer-wait --reason awaiting-reviewer --terminal none --format json",
        ),
        (
            "Reviewer wait",
            "python3 dev/scripts/devctl.py review-channel --action reviewer-wait --reason awaiting-implementer --terminal none --format json",
        ),
        (
            "Docs governance",
            "python3 dev/scripts/devctl.py docs-check --strict-tooling",
        ),
        (
            "Surface refresh",
            "python3 dev/scripts/devctl.py render-surfaces --write --format md",
        ),
    )
    lines: list[str] = []
    for label, command in sections:
        lines.extend((f"# {label}", command, ""))
    return "\n".join(lines).rstrip()


def render_post_edit_verification_steps(
    *,
    bundle_by_lane: Mapping[str, str],
    process_doc: str,
    development_doc: str,
) -> str:
    """Render the blocking post-edit verification checklist."""
    bundles = ", ".join(
        f"`{bundle_by_lane[lane]}`"
        for lane in ("runtime", "docs", "tooling", "release")
    )
    steps = (
        f"Run the task-class bundle from `{process_doc}` after every file create/edit: {bundles}.",
        f"Run any additional path or risk add-ons required by `python3 dev/scripts/devctl.py check-router --format md`, `{process_doc}`, and `{development_doc}#after-file-edits`.",
        "For new modules, refactors, policy changes, or business-logic edits, run `python3 dev/scripts/devctl.py check --profile ci` and `python3 dev/scripts/devctl.py probe-report --format md`.",
        "If you changed generated instruction surfaces or repo policy, run `python3 dev/scripts/devctl.py render-surfaces --write --format md` and `python3 dev/scripts/checks/check_instruction_surface_sync.py`.",
        "If you changed governance/platform contract routing or runtime contract models, run `python3 dev/scripts/devctl.py quality-policy --format md`, `python3 dev/scripts/devctl.py platform-contracts --format md`, and `python3 dev/scripts/checks/check_platform_contract_closure.py`.",
        "`python3 dev/scripts/devctl.py check --profile quick` is only a local iteration step; it does not replace the required bundle or handoff verification.",
    )
    return _render_numbered_lines(steps)


def render_guard_limits_block() -> str:
    """Render the AI-facing summary of guard-enforced limits."""
    rust_function_limit = _function_length_limit(".rs", default=100)
    python_function_limit = _function_length_limit(".py", default=150)
    rust_soft_limit, rust_hard_limit = _file_size_limits(
        ".rs",
        soft_default=900,
        hard_default=1400,
    )
    python_soft_limit, python_hard_limit = _file_size_limits(
        ".py",
        soft_default=350,
        hard_default=650,
    )
    lines = [
        "- This block is rendered from `dev/scripts/checks/code_shape_function_exceptions.py` and `dev/scripts/checks/code_shape_policy.py`; rerun `python3 dev/scripts/devctl.py render-surfaces --write --format md` after policy changes.",
        (
            "- **Function length**: Rust max {rust_limit} lines; Python max "
            "{python_limit} lines (`code_shape` guard)."
        ).format(
            rust_limit=rust_function_limit,
            python_limit=python_function_limit,
        ),
        (
            "- **File size**: Rust soft {rust_soft} / hard {rust_hard}; "
            "Python soft {python_soft} / hard {python_hard} (`code_shape` guard)."
        ).format(
            rust_soft=rust_soft_limit,
            rust_hard=rust_hard_limit,
            python_soft=python_soft_limit,
            python_hard=python_hard_limit,
        ),
        "- **Duplication**: identical normalized function bodies across files are blocked (`check_function_duplication.py`). Extract shared helpers instead of copying.",
        "- Function exceptions/overrides live in `dev/scripts/checks/code_shape_function_exceptions.py`; the live enabled guard/probe inventory lives in `python3 dev/scripts/devctl.py quality-policy --format md`.",
    ]
    return "\n".join(lines)


def _render_numbered_lines(items: tuple[str, ...]) -> str:
    return "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(items, start=1)
    )


def _function_length_limit(extension: str, *, default: int) -> int:
    policy = FUNCTION_LANGUAGE_DEFAULTS.get(extension)
    return policy.max_lines if policy is not None else default


def _file_size_limits(
    extension: str,
    *,
    soft_default: int,
    hard_default: int,
) -> tuple[int, int]:
    policy = LANGUAGE_POLICIES.get(extension)
    if policy is None:
        return soft_default, hard_default
    return policy.soft_limit, policy.hard_limit
