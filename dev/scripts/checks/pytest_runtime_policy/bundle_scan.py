"""Bundle-registry scanning for pytest runtime-policy checks."""

from __future__ import annotations

from .shell_command import is_unbounded_pytest_command


def bundle_violations() -> list[dict[str, str]]:
    return [
        violation
        for bundle, commands in bundle_registry().items()
        for command in commands
        if (violation := bundle_violation(bundle, command)) is not None
    ]


def bundle_registry() -> dict[str, tuple[str, ...]]:
    from dev.scripts.devctl.bundle_registry import BUNDLE_REGISTRY

    return BUNDLE_REGISTRY


def bundle_violation(bundle: str, command: str) -> dict[str, str] | None:
    if not is_unbounded_pytest_command(command):
        return None
    return {
        "kind": "raw_pytest_bundle_command",
        "bundle": bundle,
        "command": command,
    }
