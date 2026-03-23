"""Starter surface-generation helpers for portable governance onboarding."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .surface_context import (
    render_bootstrap_steps,
    render_guard_limits_block,
    render_key_commands_block,
    render_post_edit_verification_steps,
)


@dataclass(frozen=True)
class SurfaceSeed:
    """Typed seed input for starter surface definitions."""

    surface_id: str
    surface_type: str
    template_path: str
    output_path: str
    tracked: bool
    local_only: bool
    description: str
    required_contains: tuple[str, ...] = ()


def build_surface_generation_governance(
    *,
    repo_root: Path,
    tooling_required_docs: list[str],
    runtime_prefixes: list[str],
    tooling_prefixes: list[str],
    branch_policy: str,
    development_branch: str,
) -> dict[str, object]:
    """Build starter repo-pack surface-generation policy."""
    surface_generation: dict[str, object] = {}
    surface_generation["repo_pack_metadata"] = _build_repo_pack_metadata(repo_root)
    surface_generation["context"] = _build_surface_generation_context(
        repo_root=repo_root,
        tooling_required_docs=tooling_required_docs,
        runtime_prefixes=runtime_prefixes,
        tooling_prefixes=tooling_prefixes,
        branch_policy=branch_policy,
        development_branch=development_branch,
    )
    surface_generation["surfaces"] = [
        _build_surface_spec(
            SurfaceSeed(
                surface_id="claude_instructions",
                surface_type="local_instructions",
                template_path="dev/config/templates/claude_instructions.template.md",
                output_path="CLAUDE.md",
                tracked=False,
                local_only=True,
                description="Local-only Claude instructions surface.",
                required_contains=(
                    "## Governance capabilities (available during work)",
                    "## Task Router Quick Map",
                    "`decision_mode` gates action: `auto_apply` means fix directly,",
                    "`python3 dev/scripts/devctl.py governance-review --record ...`",
                    "## Mandatory post-edit verification (blocking)",
                    "After EVERY file create/edit, you MUST run the repo-required verification before",
                    "Done means the required guards/tests passed.",
                ),
            )
        ),
        _build_surface_spec(
            SurfaceSeed(
                surface_id="portable_pre_commit_hook_stub",
                surface_type="starter_artifact",
                template_path="dev/config/templates/portable_governance_pre_commit_hook.stub.template.sh",
                output_path="dev/config/templates/portable_governance_pre_commit_hook.stub.sh",
                tracked=True,
                local_only=False,
                description="Starter pre-commit hook stub.",
            )
        ),
        _build_surface_spec(
            SurfaceSeed(
                surface_id="portable_pre_push_hook_stub",
                surface_type="starter_artifact",
                template_path="dev/config/templates/portable_governance_pre_push_hook.stub.template.sh",
                output_path="dev/config/templates/portable_governance_pre_push_hook.stub.sh",
                tracked=True,
                local_only=False,
                description="Starter pre-push hook stub.",
            )
        ),
        _build_surface_spec(
            SurfaceSeed(
                surface_id="portable_tooling_workflow_stub",
                surface_type="starter_artifact",
                template_path="dev/config/templates/portable_governance_tooling_workflow.stub.template.yml",
                output_path="dev/config/templates/portable_governance_tooling_workflow.stub.yml",
                tracked=True,
                local_only=False,
                description="Starter tooling workflow stub.",
            )
        ),
    ]
    return surface_generation


def _build_repo_pack_metadata(repo_root: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    metadata["pack_id"] = repo_root.name
    metadata["pack_version"] = "0.1.0-dev"
    metadata["product_name"] = repo_root.name
    metadata["repo_name"] = repo_root.name
    return metadata


def _build_surface_generation_context(
    *,
    repo_root: Path,
    tooling_required_docs: list[str],
    runtime_prefixes: list[str],
    tooling_prefixes: list[str],
    branch_policy: str,
    development_branch: str,
) -> dict[str, object]:
    primary_doc = tooling_required_docs[0]
    context: dict[str, object] = {}
    context["process_doc"] = primary_doc
    context["execution_tracker_doc"] = primary_doc
    context["active_registry_doc"] = primary_doc
    context["architecture_doc"] = primary_doc
    context["development_doc"] = primary_doc
    context["scripts_readme_doc"] = primary_doc
    context["ci_workflows_doc"] = ".github/workflows/README.md"
    context["cli_flags_doc"] = primary_doc
    context["project_summary"] = f"Replace with a one-line summary for {repo_root.name}."
    context["rust_source"] = runtime_prefixes[0] if runtime_prefixes else "src/"
    context["python_tooling"] = (
        tooling_prefixes[0] if tooling_prefixes else "tools/"
    )
    context["guard_scripts"] = "tools/checks/"
    context["msrv"] = "replace-me"
    context["branch_policy"] = branch_policy
    context["voice_command"] = "replace-command --help"
    context["development_branch"] = development_branch
    context["python_version"] = "3.11"
    bundle_by_lane = {
        "docs": "bundle.docs",
        "runtime": "bundle.runtime",
        "tooling": "bundle.tooling",
        "release": "bundle.release",
    }
    context["bootstrap_steps"] = render_bootstrap_steps(
        process_doc=primary_doc,
        execution_tracker_doc=primary_doc,
        active_registry_doc=primary_doc,
    )
    context["key_commands_block"] = render_key_commands_block()
    context["post_edit_verification_intro"] = (
        "After EVERY file create/edit, you MUST run the repo-required "
        "verification before reporting the task as done."
    )
    context["post_edit_verification_steps"] = render_post_edit_verification_steps(
        bundle_by_lane=bundle_by_lane,
        process_doc=primary_doc,
        development_doc=primary_doc,
    )
    context["post_edit_verification_done_criteria"] = (
        "Done means the required guards/tests passed. Do not report completion "
        "after only writing code or running a partial subset of checks. If a "
        "required guard fails, fix it or report the blocker explicitly."
    )
    context["task_router_block"] = (
        "- Rendered at surface-build time from the repo's typed task router."
    )
    context["guard_limits_block"] = render_guard_limits_block()
    context["user_preferences_block"] = "- Replace with operator preferences."
    return context


def _build_surface_spec(seed: SurfaceSeed) -> dict[str, object]:
    spec: dict[str, object] = {}
    spec["id"] = seed.surface_id
    spec["surface_type"] = seed.surface_type
    spec["renderer"] = "template_file"
    spec["template_path"] = seed.template_path
    spec["output_path"] = seed.output_path
    spec["tracked"] = seed.tracked
    spec["local_only"] = seed.local_only
    spec["description"] = seed.description
    if seed.required_contains:
        spec["required_contains"] = list(seed.required_contains)
    return spec
