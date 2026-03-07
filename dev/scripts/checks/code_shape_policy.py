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
    "rust/src/bin/voiceterm/transcript_history.rs": ShapePolicy(
        soft_limit=750,
        hard_limit=950,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_code_shape.py": ShapePolicy(
        soft_limit=675,
        hard_limit=725,
        oversize_growth_limit=30,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/check_active_plan_sync.py": ShapePolicy(
        soft_limit=580,
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
        soft_limit=430,
        hard_limit=650,
        oversize_growth_limit=35,
        hard_lock_growth_limit=0,
    ),
    "dev/scripts/checks/code_shape_policy.py": ShapePolicy(
        soft_limit=420,
        hard_limit=550,
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
    "dev/scripts/checks/check_code_shape.py::main": FunctionShapeException(
        max_lines=210,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main still handles CLI parsing and report output; helper split is pending.",
    ),
    "dev/scripts/checks/check_mutation_score.py::main": FunctionShapeException(
        max_lines=210,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main still handles policy + format branching; support split is pending.",
    ),
    "dev/scripts/checks/check_rust_lint_debt.py::main": FunctionShapeException(
        max_lines=220,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main still combines report modes and dead-code inventory logic.",
    ),
    "dev/scripts/checks/check_structural_complexity.py::main": FunctionShapeException(
        max_lines=180,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Main still combines parser and output fallback handling.",
    ),
    "dev/scripts/checks/check_active_plan_sync.py::_build_report": FunctionShapeException(
        max_lines=390,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Active-plan snapshot + parity report assembly is still in a single pipeline function.",
    ),
    "dev/scripts/checks/check_multi_agent_sync.py::_build_report": FunctionShapeException(
        max_lines=310,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Cross-doc board/instruction/ledger reconciliation remains consolidated pending extraction.",
    ),
    "dev/scripts/devctl/cli_parser_release.py::add_release_parsers": FunctionShapeException(
        max_lines=175,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Release parser wiring still enumerates release subcommands in one registration block.",
    ),
    "dev/scripts/devctl/commands/autonomy_loop.py::run": FunctionShapeException(
        max_lines=230,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Autonomy loop runner still owns orchestration and output packet wiring before final split.",
    ),
    "dev/scripts/devctl/commands/autonomy_run.py::run": FunctionShapeException(
        max_lines=340,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Autonomy run command still combines policy resolution, lane execution, and reporting.",
    ),
    "dev/scripts/devctl/commands/hygiene_audits_adrs.py::audit_adrs": FunctionShapeException(
        max_lines=170,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="ADR audit still performs collection, policy checks, and report shaping in one function.",
    ),
    "dev/scripts/devctl/commands/integrations_import.py::run": FunctionShapeException(
        max_lines=220,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Integrations import run path still combines parsing, path audit, and write orchestration.",
    ),
    "dev/scripts/devctl/commands/loop_packet.py::run": FunctionShapeException(
        max_lines=170,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Loop packet run path still combines read/merge/emit flows pending helper extraction.",
    ),
    "dev/scripts/devctl/commands/sync.py::run": FunctionShapeException(
        max_lines=230,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Sync command still owns branch audit and remediation routing in a single runner.",
    ),
    "dev/scripts/devctl/commands/triage_loop.py::run": FunctionShapeException(
        max_lines=200,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 3",
        reason="Triage loop command still bundles gate checks, branch prep, and loop dispatch flow.",
    ),
    "dev/scripts/devctl/commands/docs_check.py::run": FunctionShapeException(
        max_lines=230,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 2",
        reason="Runner still combines policy checks and rendering before final split.",
    ),
    "dev/scripts/devctl/commands/docs_check_render.py::render_markdown_report": FunctionShapeException(
        max_lines=230,
        owner="MP-347",
        expires_on="2026-05-15",
        follow_up_mp="MP-347 Phase 2",
        reason="Renderer still builds the full markdown packet in one place.",
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
