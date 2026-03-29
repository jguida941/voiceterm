"""Cargo-mutants execution engine."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.mutation.config import file_args_for_modules, file_args_for_targets


@dataclass(frozen=True)
class MutantsRunConfig:
    """Runtime configuration for one cargo-mutants invocation."""

    workspace_dir: Path
    modules: Optional[list[str]] = None
    file_targets: Optional[list[str]] = None
    timeout: int = 300
    baseline_skip: bool = True
    shard: Optional[str] = None
    cargo_home: Optional[str] = None
    cargo_target_dir: Optional[str] = None
    offline: bool = False


def cargo_home_has_cache(path: Path) -> bool:
    """Detect whether a CARGO_HOME has registry/git cache data."""
    return (path / "registry").exists() or (path / "git").exists()


def run_mutants(config: MutantsRunConfig) -> Optional[int]:
    """Run ``cargo mutants`` against targeted files or module groups."""
    file_args: list[str] = []
    label = ""

    if config.file_targets:
        file_args = file_args_for_targets(config.file_targets)
        label = f"{len(config.file_targets)} changed file(s)"
    elif config.modules:
        file_args = file_args_for_modules(config.modules)
        label = ", ".join(config.modules)

    if not file_args:
        print("No valid targets selected.")
        return None

    cmd = [
        "cargo",
        "mutants",
        "--timeout",
        str(config.timeout),
        "-o",
        "mutants.out",
        "--json",
    ]
    if config.baseline_skip:
        cmd.append("--baseline=skip")
    cmd += file_args
    if config.shard:
        cmd.extend(["--shard", config.shard])

    print(f"\nRunning mutation tests on: {label}")
    if config.file_targets:
        for file_path in config.file_targets:
            print(f"  - {file_path}")
    if config.shard:
        print(f"Shard: {config.shard}")
    if config.baseline_skip:
        print("Baseline: skip (tests assumed green)")
    print(f"Command: {' '.join(cmd)}\n")
    print("-" * 60)

    env = _build_env(config)
    os.chdir(config.workspace_dir)
    result = subprocess.run(cmd, capture_output=False, env=env, check=False)
    return result.returncode


def _build_env(config: MutantsRunConfig) -> dict[str, str]:
    env = os.environ.copy()
    if config.cargo_home:
        cargo_home_path = Path(config.cargo_home).expanduser()
        cargo_home_path.mkdir(parents=True, exist_ok=True)
        env["CARGO_HOME"] = str(cargo_home_path)
        if config.offline and not cargo_home_has_cache(cargo_home_path):
            print(
                f"Warning: CARGO_HOME {cargo_home_path} looks empty while offline. "
                "Seed it from your main cargo cache (e.g., rsync -a ~/.cargo/ /tmp/cargo-home/)."
            )
    if config.cargo_target_dir:
        cargo_target_path = Path(config.cargo_target_dir).expanduser()
        cargo_target_path.mkdir(parents=True, exist_ok=True)
        env["CARGO_TARGET_DIR"] = str(cargo_target_path)
    if config.offline:
        env["CARGO_NET_OFFLINE"] = "true"
    return env
