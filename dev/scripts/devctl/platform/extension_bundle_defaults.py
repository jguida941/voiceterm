"""Default extension bundles for known repo-packs.

Each repo-pack that adopts the governance platform can define its own
``ExtensionBundle`` here.  The contract types live in
``extension_bundle``; this module only wires concrete defaults.
"""

from __future__ import annotations

from .extension_bundle import AutomationSpec, ExtensionBundle, ExtensionSurface

VOICETERM_EXTENSION_BUNDLE = ExtensionBundle(
    repo_pack_id="voiceterm",
    surfaces=(
        ExtensionSurface(
            surface_id="codex_hooks",
            target_path=".codex/hooks.json",
            source_contract="ProjectGovernance",
            format="json",
            description="Pre-commit and pre-push hooks",
        ),
        ExtensionSurface(
            surface_id="claude_settings",
            target_path=".claude/settings.local.json",
            source_contract="ProjectGovernance",
            format="json",
            description="Claude Code project settings",
        ),
        ExtensionSurface(
            surface_id="mcp_tools",
            target_path=".mcp.json",
            source_contract="ProjectGovernance",
            format="json",
            description="MCP tool server configuration",
        ),
        ExtensionSurface(
            surface_id="claude_agents",
            target_path=".claude/agents/",
            source_contract="ProjectGovernance",
            format="json",
            description="Project subagent definitions",
        ),
    ),
    automations=(
        AutomationSpec(
            task_id="lint_and_fix",
            devctl_command="guard-run --profile quick",
            execution_modes=("local", "github_workflow"),
            description="Quick lint and auto-fix",
        ),
        AutomationSpec(
            task_id="full_ci",
            devctl_command="check --profile ci",
            execution_modes=("local", "github_workflow", "codex_automation"),
            description="Full CI guard bundle",
        ),
        AutomationSpec(
            task_id="probe_report",
            devctl_command="probe-report --format md",
            execution_modes=("local", "github_workflow", "claude_agent"),
            description="Code quality probe scan",
        ),
    ),
)


REGISTERED_EXTENSION_BUNDLES: dict[str, ExtensionBundle] = {
    VOICETERM_EXTENSION_BUNDLE.repo_pack_id: VOICETERM_EXTENSION_BUNDLE,
}


def registered_extension_bundles() -> dict[str, ExtensionBundle]:
    """Return a copy of the known repo-pack extension bundle registry."""
    return dict(REGISTERED_EXTENSION_BUNDLES)
