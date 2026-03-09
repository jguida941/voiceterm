"""Cargo-mutants execution engine."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from mutants_config import file_args_for_modules, file_args_for_targets


def cargo_home_has_cache(path: Path) -> bool:
    """Detect whether a CARGO_HOME has registry/git cache data."""
    return (path / "registry").exists() or (path / "git").exists()


def run_mutants(
    *,
    workspace_dir: Path,
    modules: Optional[list[str]] = None,
    file_targets: Optional[list[str]] = None,
    timeout: int = 300,
    baseline_skip: bool = True,
    shard: Optional[str] = None,
    cargo_home: Optional[str] = None,
    cargo_target_dir: Optional[str] = None,
    offline: bool = False,
) -> Optional[int]:
    """Run ``cargo mutants`` against targeted files or module groups.

    *file_targets* takes precedence over *modules*.  Returns the process exit
    code, or ``None`` when no valid targets are resolved.
    """
    file_args: list[str] = []
    label = ""

    if file_targets:
        file_args = file_args_for_targets(file_targets)
        label = f"{len(file_targets)} changed file(s)"
    elif modules:
        file_args = file_args_for_modules(modules)
        label = ", ".join(modules)

    if not file_args:
        print("No valid targets selected.")
        return None

    cmd = [
        "cargo", "mutants",
        "--timeout", str(timeout),
        "-o", "mutants.out",
        "--json",
    ]
    if baseline_skip:
        cmd.append("--baseline=skip")
    cmd += file_args
    if shard:
        cmd.extend(["--shard", shard])

    print(f"\nRunning mutation tests on: {label}")
    if file_targets:
        for f in file_targets:
            print(f"  - {f}")
    if shard:
        print(f"Shard: {shard}")
    if baseline_skip:
        print("Baseline: skip (tests assumed green)")
    print(f"Command: {' '.join(cmd)}\n")
    print("-" * 60)

    env = _build_env(cargo_home=cargo_home, cargo_target_dir=cargo_target_dir, offline=offline)

    os.chdir(workspace_dir)
    result = subprocess.run(cmd, capture_output=False, env=env, check=False)
    return result.returncode


def _build_env(
    *,
    cargo_home: Optional[str],
    cargo_target_dir: Optional[str],
    offline: bool,
) -> dict[str, str]:
    env = os.environ.copy()
    if cargo_home:
        cargo_home_path = Path(cargo_home).expanduser()
        cargo_home_path.mkdir(parents=True, exist_ok=True)
        env["CARGO_HOME"] = str(cargo_home_path)
        if offline and not cargo_home_has_cache(cargo_home_path):
            print(
                f"Warning: CARGO_HOME {cargo_home_path} looks empty while offline. "
                "Seed it from your main cargo cache (e.g., rsync -a ~/.cargo/ /tmp/cargo-home/)."
            )
    if cargo_target_dir:
        cargo_target_path = Path(cargo_target_dir).expanduser()
        cargo_target_path.mkdir(parents=True, exist_ok=True)
        env["CARGO_TARGET_DIR"] = str(cargo_target_path)
    if offline:
        env["CARGO_NET_OFFLINE"] = "true"
    return env
