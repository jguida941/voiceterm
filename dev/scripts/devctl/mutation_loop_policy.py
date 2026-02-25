"""Policy helpers for `devctl mutation-loop` bounded fix execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .loop_fix_policy import evaluate_fix_policy as evaluate_fix_policy_common
from .loop_fix_policy import load_policy as load_policy_common


def load_policy(repo_root: Path) -> dict[str, Any]:
    return load_policy_common(repo_root)


def evaluate_fix_policy(
    *,
    mode: str,
    branch: str,
    fix_command: str | None,
    policy: dict[str, Any],
) -> str | None:
    return evaluate_fix_policy_common(
        mode=mode,
        branch=branch,
        fix_command=fix_command,
        policy=policy,
        policy_key="mutation_loop",
        env_prefixes_key="MUTATION_LOOP_ALLOWED_PREFIXES",
        loop_label="mutation",
    )
