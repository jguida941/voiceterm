#!/usr/bin/env python3
"""Scoring helpers for the bundle-registry DRY guard."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .loader import load_registry

DEFAULT_MAX_WIDELY_SHARED_COMMANDS = 5
DEFAULT_MAX_SHARED = DEFAULT_MAX_WIDELY_SHARED_COMMANDS


def _declared_composition_layers(module) -> list[tuple[str, tuple[str, ...]]]:
    layer_names = tuple(getattr(module, "COMPOSITION_LAYER_NAMES", ()))
    layers: list[tuple[str, tuple[str, ...]]] = []
    for name in layer_names:
        value = getattr(module, name, None)
        if (
            not isinstance(name, str)
            or not name.startswith("_")
            or not isinstance(value, tuple)
            or not value
            or not all(isinstance(command, str) for command in value)
        ):
            raise RuntimeError(
                f"Invalid composition layer contract in bundle registry: {name!r}"
            )
        layers.append((name, value))
    return layers


def _uses_composition_layer(
    bundle_commands: tuple[str, ...],
    layer_commands: tuple[str, ...],
) -> bool:
    if len(layer_commands) > len(bundle_commands):
        return False

    window = len(layer_commands)
    for index in range(len(bundle_commands) - window + 1):
        if bundle_commands[index : index + window] == layer_commands:
            return True
    return False


def _used_composition_layers(
    bundles: dict[str, tuple[str, ...]],
    declared_layers: list[tuple[str, tuple[str, ...]]],
) -> list[str]:
    used_layers: list[str] = []
    for name, layer_commands in declared_layers:
        reuse_count = sum(
            1
            for bundle_commands in bundles.values()
            if _uses_composition_layer(bundle_commands, layer_commands)
        )
        if reuse_count >= 2:
            used_layers.append(name)
    return used_layers


def build_report(
    max_widely_shared_commands: int = DEFAULT_MAX_WIDELY_SHARED_COMMANDS,
) -> dict:
    registry = load_registry()
    bundles: dict[str, tuple[str, ...]] = registry.BUNDLE_REGISTRY
    declared_layers = _declared_composition_layers(registry)
    used_layers = _used_composition_layers(bundles, declared_layers)
    uses_composition = bool(used_layers)

    cmd_counts: Counter[str] = Counter()
    for commands in bundles.values():
        for cmd in commands:
            cmd_counts[cmd] += 1

    widely_shared = [cmd for cmd, count in cmd_counts.items() if count > 2]

    violations: list[dict[str, object]] = []
    if len(widely_shared) > max_widely_shared_commands and not uses_composition:
        for cmd in widely_shared:
            violations.append(
                {
                    "rule": "dry-violation",
                    "command_text": cmd,
                    "bundle_count": cmd_counts[cmd],
                    "hint": "Extract shared commands into a composition tuple in bundle_registry.py.",
                }
            )

    return {
        "command": "check_bundle_registry_dry",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not violations,
        "max_widely_shared_commands": max_widely_shared_commands,
        "max_shared": max_widely_shared_commands,
        "bundle_count": len(bundles),
        "widely_shared_count": len(widely_shared),
        "composition_layers_declared": [name for name, _ in declared_layers],
        "composition_layers_used": used_layers,
        "uses_composition": uses_composition,
        "violations": violations,
    }
