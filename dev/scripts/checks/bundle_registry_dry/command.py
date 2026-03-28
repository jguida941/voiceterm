#!/usr/bin/env python3
"""Guard bundle registry DRY compliance: flag copy-paste command sharing."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REGISTRY_PATH: Final[str] = "dev/scripts/devctl/bundle_registry.py"
DEFAULT_MAX_SHARED: Final[int] = 5


def _resolve_registry_module_path(module_path: Path) -> Path:
    try:
        text = module_path.read_text(encoding="utf-8")
    except OSError:
        return module_path
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("# shim-target:"):
            continue
        target = line.split(":", 1)[1].strip()
        if target:
            resolved = (REPO_ROOT / target).resolve()
            repo_root_resolved = REPO_ROOT.resolve()
            try:
                resolved.relative_to(repo_root_resolved)
            except ValueError as exc:
                raise RuntimeError(
                    f"shim-target for {module_path} escapes repo root: {target}"
                ) from exc
            if not resolved.is_file():
                raise RuntimeError(
                    f"shim-target for {module_path} does not resolve to a file: {target}"
                )
            return resolved
    return module_path


def _load_registry():
    module_path = _resolve_registry_module_path(REPO_ROOT / REGISTRY_PATH)
    spec = importlib.util.spec_from_file_location("bundle_registry", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def build_report(max_shared: int = DEFAULT_MAX_SHARED) -> dict:
    registry = _load_registry()
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
    if len(widely_shared) > max_shared and not uses_composition:
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
        "max_shared": max_shared,
        "bundle_count": len(bundles),
        "widely_shared_count": len(widely_shared),
        "composition_layers_declared": [name for name, _ in declared_layers],
        "composition_layers_used": used_layers,
        "uses_composition": uses_composition,
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# check_bundle_registry_dry",
        "",
        f"- ok: {report['ok']}",
        f"- max_shared: {report['max_shared']}",
        f"- bundle_count: {report['bundle_count']}",
        f"- widely_shared_count: {report['widely_shared_count']}",
        f"- composition_layers_declared: {len(report['composition_layers_declared'])}",
        f"- composition_layers_used: {', '.join(report['composition_layers_used']) or 'none'}",
        f"- uses_composition: {report['uses_composition']}",
        f"- violations: {len(report['violations'])}",
    ]
    violations = report.get("violations", [])
    if violations:
        lines.extend(["", "## Violations"])
        for violation in violations:
            lines.append(
                "- [{rule}] `{command_text}` appears in {bundle_count} bundles -> {hint}".format(
                    rule=violation["rule"],
                    command_text=violation["command_text"],
                    bundle_count=violation["bundle_count"],
                    hint=violation["hint"],
                )
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--max-shared",
        type=int,
        default=DEFAULT_MAX_SHARED,
        help=(
            "Max commands allowed to be shared across more than two bundles "
            "before composition becomes mandatory (default: 5)."
        ),
    )
    args = parser.parse_args()
    report = build_report(max_shared=args.max_shared)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
