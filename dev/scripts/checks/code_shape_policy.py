"""Shared policies for check_code_shape."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShapePolicy:
    soft_limit: int
    hard_limit: int
    oversize_growth_limit: int
    hard_lock_growth_limit: int


@dataclass(frozen=True)
class FunctionShapePolicy:
    max_lines: int


@dataclass(frozen=True)
class FunctionShapeException:
    max_lines: int
    owner: str
    expires_on: str
    follow_up_mp: str
    reason: str


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
        soft_limit=1300,
        hard_limit=1450,
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
        soft_limit=700,
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
    "rust/src/bin/voiceterm/status_line/format.rs": ShapePolicy(
        soft_limit=1000,
        hard_limit=1200,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/theme/rule_profile.rs": ShapePolicy(
        soft_limit=1000,
        hard_limit=1200,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/theme/style_pack.rs": ShapePolicy(
        soft_limit=750,
        hard_limit=950,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/transcript_history.rs": ShapePolicy(
        soft_limit=750,
        hard_limit=950,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_code_shape.py": ShapePolicy(
        soft_limit=650,
        hard_limit=700,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/commands/check.py": ShapePolicy(
        soft_limit=425,
        hard_limit=500,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_active_plan_sync.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_multi_agent_sync.py": ShapePolicy(
        soft_limit=450,
        hard_limit=650,
        oversize_growth_limit=25,
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
        soft_limit=400,
        hard_limit=650,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/devctl/cli_parser_reporting.py": ShapePolicy(
        soft_limit=380,
        hard_limit=500,
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
    "dev/scripts/devctl/commands/mcp.py": ShapePolicy(
        soft_limit=725,
        hard_limit=850,
        oversize_growth_limit=25,
        hard_lock_growth_limit=0,
    ),
}


FUNCTION_LANGUAGE_DEFAULTS: dict[str, FunctionShapePolicy] = {
    ".py": FunctionShapePolicy(max_lines=150),
}


FUNCTION_POLICY_OVERRIDES: dict[str, FunctionShapePolicy] = {
    "rust/src/bin/voiceterm/writer/state/dispatch.rs": FunctionShapePolicy(
        max_lines=220,
    ),
    "rust/src/bin/voiceterm/writer/state/redraw.rs": FunctionShapePolicy(
        max_lines=220,
    ),
    "rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs": FunctionShapePolicy(
        max_lines=260,
    ),
}


FUNCTION_POLICY_EXCEPTIONS: dict[str, FunctionShapeException] = {
    "rust/src/bin/voiceterm/writer/state/dispatch.rs::dispatch_message": FunctionShapeException(
        max_lines=620,
        owner="MP-346",
        expires_on="2026-05-15",
        follow_up_mp="MP-346 Step 2f.2",
        reason="Phase-2e file split landed; per-branch PTY dispatch split is pending.",
    ),
    "rust/src/bin/voiceterm/writer/state/redraw.rs::maybe_redraw_status": FunctionShapeException(
        max_lines=480,
        owner="MP-346",
        expires_on="2026-05-15",
        follow_up_mp="MP-346 Step 2f.2",
        reason="Status redraw path still carries transitional batching/state-apply sequencing.",
    ),
    "rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs::feed_prompt_output_and_sync": FunctionShapeException(
        max_lines=340,
        owner="MP-346",
        expires_on="2026-05-15",
        follow_up_mp="MP-346 Step 3b",
        reason="Prompt-occlusion decomposition into provider-neutral core is scheduled in Phase 3.",
    ),
    "dev/scripts/checks/check_code_shape.py::main": FunctionShapeException(
        max_lines=210,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main still owns CLI parse + report rendering dispatch while checker helpers are split in follow-up.",
    ),
    "dev/scripts/checks/check_mutation_score.py::main": FunctionShapeException(
        max_lines=210,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main retains policy/format fanout while mutation-report support extraction is scheduled.",
    ),
    "dev/scripts/checks/check_rust_lint_debt.py::main": FunctionShapeException(
        max_lines=220,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main orchestrates reporting modes and dead-code inventory branches pending subcommand split.",
    ),
    "dev/scripts/checks/check_structural_complexity.py::main": FunctionShapeException(
        max_lines=180,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main still coordinates parser/output fallback handling while complexity checks stabilize.",
    ),
    "dev/scripts/devctl/commands/docs_check.py::run": FunctionShapeException(
        max_lines=230,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 2",
        reason="Command runner still coordinates policy+render pipeline before final docs-check command split.",
    ),
    "dev/scripts/devctl/commands/docs_check_render.py::render_markdown_report": FunctionShapeException(
        max_lines=230,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 2",
        reason="Renderer still emits full markdown packet assembly before report-template extraction.",
    ),
}


def policy_for_path(path: Path) -> tuple[ShapePolicy | None, str | None]:
    """Return path-specific policy and source label."""
    override = PATH_POLICY_OVERRIDES.get(path.as_posix())
    if override is not None:
        return override, f"path_override:{path.as_posix()}"
    policy = LANGUAGE_POLICIES.get(path.suffix)
    if policy is None:
        return None, None
    return policy, f"language_default:{path.suffix}"


def function_policy_for_path(path: Path) -> tuple[FunctionShapePolicy | None, str | None]:
    """Return path-specific or language-default function-size policy and source label."""
    policy = FUNCTION_POLICY_OVERRIDES.get(path.as_posix())
    if policy is not None:
        return policy, f"function_path_override:{path.as_posix()}"
    lang_default = FUNCTION_LANGUAGE_DEFAULTS.get(path.suffix)
    if lang_default is not None:
        return lang_default, f"function_language_default:{path.suffix}"
    return None, None
