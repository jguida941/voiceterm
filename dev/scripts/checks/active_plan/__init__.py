"""Active-plan validation helpers for check entrypoints and tests."""

from .contract import EXECUTION_PLAN_MARKER, validate_execution_plan_contract
from .snapshot import latest_git_semver_tag, read_cargo_release_tag

__all__ = [
    "EXECUTION_PLAN_MARKER",
    "latest_git_semver_tag",
    "read_cargo_release_tag",
    "validate_execution_plan_contract",
]
