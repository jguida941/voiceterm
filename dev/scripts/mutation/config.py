"""Module registry, exclusion lists, and validation helpers for mutation testing."""

from __future__ import annotations

import re
from typing import Optional

MODULES = {
    "audio": {
        "desc": "Audio capture, VAD, resampling",
        "files": ["src/audio/**"],
        "timeout": 120,
    },
    "stt": {
        "desc": "Whisper transcription",
        "files": ["src/stt.rs"],
        "timeout": 120,
    },
    "voice": {
        "desc": "Voice capture orchestration",
        "files": ["src/voice.rs"],
        "timeout": 120,
    },
    "config": {
        "desc": "CLI flags and validation",
        "files": ["src/config/**"],
        "timeout": 60,
    },
    "pty": {
        "desc": "PTY session handling",
        "files": ["src/pty_session/**"],
        "timeout": 120,
    },
    "ipc": {
        "desc": "JSON IPC protocol",
        "files": ["src/ipc/**"],
        "timeout": 90,
    },
    "app": {
        "desc": "Legacy TUI state and logging (compat alias)",
        "files": ["src/legacy_tui/**", "src/legacy_ui.rs"],
        "timeout": 90,
    },
    "legacy_tui": {
        "desc": "Legacy TUI state and logging",
        "files": ["src/legacy_tui/**", "src/legacy_ui.rs"],
        "timeout": 90,
    },
    "overlay": {
        "desc": "Overlay binary (main, writer, status)",
        "files": ["src/bin/voiceterm/**"],
        "timeout": 180,
    },
}

CHANGED_EXCLUDE_GLOBS = {
    "src/bin/test_crash.rs",
    "src/bin/test_utf8_bug.rs",
    "src/bin/voice_benchmark.rs",
    "src/bin/latency_measurement.rs",
    "src/audio/recorder.rs",
}

DEFAULT_BASE_BRANCH = "master"


def parse_shard_spec(shard: Optional[str]) -> Optional[str]:
    """Validate cargo-mutants shard syntax (e.g. ``1/8``)."""
    if shard is None:
        return None
    match = re.fullmatch(r"(\d+)/(\d+)", shard.strip())
    if not match:
        raise ValueError("Invalid shard format. Use N/M, e.g. 1/8.")
    index = int(match.group(1))
    total = int(match.group(2))
    if total <= 0 or index <= 0 or index > total:
        raise ValueError("Invalid shard value. Ensure 1 <= N <= M.")
    return f"{index}/{total}"


def file_args_for_modules(modules: list[str]) -> list[str]:
    """Build ``-f <glob>`` pairs for the given module names."""
    args: list[str] = []
    for mod in modules:
        if mod in MODULES:
            for glob in MODULES[mod]["files"]:
                args.extend(["-f", glob])
    return args


def file_args_for_targets(file_targets: list[str]) -> list[str]:
    """Build ``-f <path>`` pairs for explicit file paths."""
    args: list[str] = []
    for path in file_targets:
        args.extend(["-f", path])
    return args


def list_modules() -> None:
    """Print available modules to stdout."""
    print("\nAvailable modules for mutation testing:\n")
    print(f"{'Module':<12} {'Description':<40} {'Timeout':<10}")
    print("-" * 62)
    for name, info in MODULES.items():
        print(f"{name:<12} {info['desc']:<40} {info['timeout']}s")
    print()


def select_modules_interactive() -> list[str]:
    """Interactive module selection via stdin prompt."""
    print("\n=== VoiceTerm Mutation Testing ===\n")
    print("Select modules to test (comma-separated numbers, or 'all'):\n")

    module_list = list(MODULES.keys())
    for index, name in enumerate(module_list, 1):
        info = MODULES[name]
        print(f"  {index}. {name:<12} - {info['desc']}")

    print("\n  0. ALL modules (slow)")
    print()

    try:
        choice = input("Enter selection: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        raise SystemExit(0) from None

    if choice in ("0", "all"):
        return module_list

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(module_list):
                selected.append(module_list[idx])
        elif part in MODULES:
            selected.append(part)

    return selected if selected else module_list[:1]
