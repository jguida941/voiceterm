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

# Phase 3C hotspot budgets (MP-265): these files must not grow while staged
# decomposition work is active.
PATH_POLICY_OVERRIDES: dict[str, ShapePolicy] = {
    "rust/src/bin/voiceterm/writer/state.rs": ShapePolicy(
        soft_limit=2750,
        hard_limit=2750,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs": ShapePolicy(
        soft_limit=1143,
        hard_limit=1143,
        oversize_growth_limit=0,
        hard_lock_growth_limit=0,
    ),
    "rust/src/bin/voiceterm/prompt/claude_prompt_detect.rs": ShapePolicy(
        soft_limit=930,
        hard_limit=930,
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
        soft_limit=600,
        hard_limit=650,
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
