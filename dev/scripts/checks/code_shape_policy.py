"""Shared policies for check_code_shape."""

from __future__ import annotations

from pathlib import Path

try:
    from code_shape_function_exceptions import (
        FUNCTION_LANGUAGE_DEFAULTS,
        FUNCTION_POLICY_EXCEPTIONS,
        FUNCTION_POLICY_OVERRIDES,
    )
    from code_shape_shared import FunctionShapePolicy, ShapePolicy
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.code_shape_function_exceptions import (
        FUNCTION_LANGUAGE_DEFAULTS,
        FUNCTION_POLICY_EXCEPTIONS,
        FUNCTION_POLICY_OVERRIDES,
    )
    from dev.scripts.checks.code_shape_shared import (
        FunctionShapePolicy,
        ShapePolicy,
    )


LANGUAGE_POLICIES: dict[str, ShapePolicy] = {
    # Existing Rust runtime has a few legacy oversized files; this guard is
    # intentionally non-regressive and blocks new oversize growth.
    ".rs": ShapePolicy(
        soft_limit=900,
        hard_limit=1400,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    ".py": ShapePolicy(
        soft_limit=350,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
}

BEST_PRACTICE_DOCS: dict[str, tuple[str, ...]] = {
    ".rs": (
        "https://doc.rust-lang.org/book/",
        "https://rust-lang.github.io/api-guidelines/",
    ),
    ".py": (
        "https://docs.python.org/3/",
        "https://peps.python.org/pep-0008/",
    ),
}

SHAPE_AUDIT_GUIDANCE = (
    "Run a shape audit before merge: identify modularization or consolidation opportunities. "
    "Do not bypass shape limits with readability-reducing code-golf edits."
)

# MP-346 hotspot budgets: staged decomposition files use explicit path budgets.
PATH_POLICY_OVERRIDES: dict[str, ShapePolicy] = {
    # High-signal integration tests with heavy scenario matrices are governed by
    # explicit budgets instead of being fully excluded from shape controls.
    "rust/src/bin/voiceterm/event_loop/tests.rs": ShapePolicy(
        soft_limit=6500,
        hard_limit=7000,
        oversize_growth_limit=150,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/writer/state/tests.rs": ShapePolicy(
        soft_limit=1750,
        hard_limit=1950,
        oversize_growth_limit=80,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/status_line/format/tests.rs": ShapePolicy(
        soft_limit=1370,
        hard_limit=1500,
        oversize_growth_limit=80,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/status_line/buttons/tests.rs": ShapePolicy(
        soft_limit=1300,
        hard_limit=1450,
        oversize_growth_limit=80,
        hard_lock_growth_limit=0,
    ),
    "rust/src/ipc/tests.rs": ShapePolicy(
        soft_limit=1850,
        hard_limit=2100,
        oversize_growth_limit=80,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/writer/state.rs": ShapePolicy(
        soft_limit=500,
        hard_limit=600,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/writer/state/dispatch.rs": ShapePolicy(
        soft_limit=600,
        hard_limit=700,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/writer/state/redraw.rs": ShapePolicy(
        soft_limit=500,
        hard_limit=600,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/writer/state/policy.rs": ShapePolicy(
        soft_limit=450,
        hard_limit=550,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs": ShapePolicy(
        soft_limit=650,
        hard_limit=700,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/prompt/claude_prompt_detect.rs": ShapePolicy(
        soft_limit=600,
        hard_limit=600,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/theme/style_pack.rs": ShapePolicy(
        soft_limit=400,
        hard_limit=500,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/main.rs": ShapePolicy(
        soft_limit=950,
        hard_limit=1050,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/transcript_history.rs": ShapePolicy(
        soft_limit=750,
        hard_limit=950,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/dev_command/broker/mod.rs": ShapePolicy(
        soft_limit=400,
        hard_limit=450,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/dev_command/command_state.rs": ShapePolicy(soft_limit=500, hard_limit=550, oversize_growth_limit=0, hard_lock_growth_limit=0),
    "dev/scripts/checks/check_code_shape.py": ShapePolicy(
        soft_limit=675,
        hard_limit=725,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_active_plan_sync.py": ShapePolicy(
        soft_limit=650,
        hard_limit=700,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_multi_agent_sync.py": ShapePolicy(
        soft_limit=520,
        hard_limit=700,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_structural_complexity.py": ShapePolicy(
        soft_limit=400,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/compat_matrix_smoke.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_rust_lint_debt.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_rust_best_practices.py": ShapePolicy(
        soft_limit=525,
        hard_limit=650,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_bundle_workflow_parity.py": ShapePolicy(
        soft_limit=675,
        hard_limit=750,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_duplication_audit.py": ShapePolicy(
        soft_limit=450,
        hard_limit=550,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_duplication_audit_support.py": ShapePolicy(
        soft_limit=550,
        hard_limit=650,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_architecture_surface_sync.py": ShapePolicy(
        soft_limit=650,
        hard_limit=725,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/code_shape_function_exceptions.py": ShapePolicy(
        soft_limit=450,
        hard_limit=525,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/code_shape_policy.py": ShapePolicy(
        soft_limit=875,
        hard_limit=950,
        oversize_growth_limit=80,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/coderabbit_ralph_loop_core.py": ShapePolicy(
        soft_limit=360,
        hard_limit=500,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/naming_consistency_core.py": ShapePolicy(
        soft_limit=370,
        hard_limit=500,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/collect.py": ShapePolicy(
        soft_limit=360,
        hard_limit=500,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/commands/autonomy_run.py": ShapePolicy(
        soft_limit=370,
        hard_limit=500,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/commands/sync.py": ShapePolicy(
        soft_limit=360,
        hard_limit=500,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/cli_parser/reporting.py": ShapePolicy(
        soft_limit=300,
        hard_limit=400,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/commands/check_phases.py": ShapePolicy(
        soft_limit=400,
        hard_limit=550,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/commands/hygiene.py": ShapePolicy(
        soft_limit=380,
        hard_limit=550,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/commands/review_channel.py": ShapePolicy(
        soft_limit=900,
        hard_limit=1000,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/tests/test_review_channel_context_refs.py": ShapePolicy(
        soft_limit=220,
        hard_limit=300,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/review_channel/event_reducer.py": ShapePolicy(
        soft_limit=500,
        hard_limit=600,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/review_channel/launch.py": ShapePolicy(
        soft_limit=325,
        hard_limit=425,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/review_channel/handoff.py": ShapePolicy(
        soft_limit=675,
        hard_limit=775,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/review_channel/state.py": ShapePolicy(
        soft_limit=325,
        hard_limit=425,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/state/activity/activity_reports.py": ShapePolicy(
        soft_limit=675,
        hard_limit=750,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/tests/collaboration/test_context_pack_refs.py": ShapePolicy(
        soft_limit=220,
        hard_limit=300,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/state/presentation/presentation_state.py": ShapePolicy(
        soft_limit=550,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/theme/colors.py": ShapePolicy(
        soft_limit=425,
        hard_limit=500,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/theme/qss/qss_panels.py": ShapePolicy(
        soft_limit=425,
        hard_limit=500,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/theme/qss/qss_controls.py": ShapePolicy(
        soft_limit=450,
        hard_limit=525,
        oversize_growth_limit=20,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/theme/editor/theme_editor.py": ShapePolicy(
        soft_limit=1400,
        hard_limit=1500,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/theme/runtime/theme_engine.py": ShapePolicy(
        soft_limit=500,
        hard_limit=575,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/theme/editor/theme_preview.py": ShapePolicy(
        soft_limit=550,
        hard_limit=625,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/views/workspaces/activity_workspace.py": ShapePolicy(
        soft_limit=450,
        hard_limit=550,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/state/bridge/lane_builder.py": ShapePolicy(
        soft_limit=400,
        hard_limit=475,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_mobile_relay_protocol.py": ShapePolicy(
        soft_limit=650,
        hard_limit=725,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_python_broad_except.py": ShapePolicy(
        soft_limit=425,
        hard_limit=500,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/mobile_status_views.py": ShapePolicy(
        soft_limit=375,
        hard_limit=450,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/views/workspaces/home_workspace.py": ShapePolicy(
        soft_limit=475,
        hard_limit=550,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/views/main_window.py": ShapePolicy(
        soft_limit=900,
        hard_limit=1000,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/views/ui_pages.py": ShapePolicy(
        soft_limit=850,
        hard_limit=950,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
    "app/operator_console/views/ui_refresh.py": ShapePolicy(
        soft_limit=1150,
        hard_limit=1250,
        oversize_growth_limit=40,
        hard_lock_growth_limit=0,
    ),
}

PATH_POLICY_PREFIX_OVERRIDES: dict[str, ShapePolicy] = {
    "rust/src/bin/voiceterm/dev_command/": ShapePolicy(
        soft_limit=360,
        hard_limit=450,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
}


def policy_for_path(path: Path) -> tuple[ShapePolicy | None, str | None]:
    """Return path-specific policy and source label."""
    path_str = path.as_posix()
    override = PATH_POLICY_OVERRIDES.get(path_str)
    if override is not None:
        return override, f"path_override:{path_str}"
    prefix_override = max(
        (
            (prefix, policy)
            for prefix, policy in PATH_POLICY_PREFIX_OVERRIDES.items()
            if path_str.startswith(prefix)
        ),
        key=lambda item: len(item[0]),
        default=None,
    )
    if prefix_override is not None:
        prefix, policy = prefix_override
        return policy, f"path_prefix_override:{prefix}"
    policy = LANGUAGE_POLICIES.get(path.suffix)
    if policy is None:
        return None, None
    return policy, f"language_default:{path.suffix}"


def function_policy_for_path(
    path: Path,
) -> tuple[FunctionShapePolicy | None, str | None]:
    """Return path-specific or language-default function-size policy and source label."""
    policy = FUNCTION_POLICY_OVERRIDES.get(path.as_posix())
    if policy is not None:
        return policy, f"function_path_override:{path.as_posix()}"
    lang_default = FUNCTION_LANGUAGE_DEFAULTS.get(path.suffix)
    if lang_default is not None:
        return lang_default, f"function_language_default:{path.suffix}"
    return None, None
