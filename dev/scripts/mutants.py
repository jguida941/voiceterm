#!/usr/bin/env python3
"""VoiceTerm mutation testing helper."""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mutants_plot import plot_hotspots

MODULES = {
    "audio": {
        "desc": "Audio capture, VAD, resampling",
        "files": ["src/audio/**"],
        "timeout": 120,
    },
    "stt": {"desc": "Whisper transcription", "files": ["src/stt.rs"], "timeout": 120},
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
    "ipc": {"desc": "JSON IPC protocol", "files": ["src/ipc/**"], "timeout": 90},
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

CAUGHT_SUMMARIES = {"CaughtMutant", "Killed"}
MISSED_SUMMARIES = {"MissedMutant", "Survived"}
TIMEOUT_SUMMARIES = {"Timeout"}
UNVIABLE_SUMMARIES = {"Unviable"}

REPO_ROOT = Path(__file__).parent.parent.parent


def resolve_workspace_dir(repo_root: Path) -> Path:
    for candidate in (repo_root / "rust", repo_root / "src"):
        if (candidate / "Cargo.toml").exists():
            return candidate
    return repo_root / "rust"


SRC_DIR = resolve_workspace_dir(REPO_ROOT)
OUTPUT_DIR = SRC_DIR / "mutants.out"


def find_latest_outcomes_file() -> Optional[Path]:
    primary = OUTPUT_DIR / "outcomes.json"
    if primary.exists():
        return primary
    candidates = list(OUTPUT_DIR.rglob("outcomes.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def isoformat_utc(timestamp: float) -> str:
    """Render a POSIX timestamp in stable UTC ISO-8601 format."""
    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def age_hours_from_timestamp(timestamp: float) -> float:
    """Return age in fractional hours from now for a POSIX timestamp."""
    now = datetime.now(timezone.utc).timestamp()
    return max(0.0, (now - timestamp) / 3600.0)


def list_modules():
    """Print available modules."""
    print("\nAvailable modules for mutation testing:\n")
    print(f"{'Module':<12} {'Description':<40} {'Timeout':<10}")
    print("-" * 62)
    for name, info in MODULES.items():
        print(f"{name:<12} {info['desc']:<40} {info['timeout']}s")
    print()


def select_modules_interactive():
    """Interactive module selection."""
    print("\n=== VoiceTerm Mutation Testing ===\n")
    print("Select modules to test (comma-separated numbers, or 'all'):\n")

    module_list = list(MODULES.keys())
    for i, name in enumerate(module_list, 1):
        info = MODULES[name]
        print(f"  {i}. {name:<12} - {info['desc']}")

    print(f"\n  0. ALL modules (slow)")
    print()

    try:
        choice = input("Enter selection: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        sys.exit(0)

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

    return selected if selected else module_list[:1]  # Default to first module


def cargo_home_has_cache(path: Path) -> bool:
    """Detect whether a CARGO_HOME has registry/git cache data."""
    return (path / "registry").exists() or (path / "git").exists()


def parse_shard_spec(shard: Optional[str]) -> Optional[str]:
    """Validate cargo-mutants shard syntax (e.g. 1/8)."""
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


def scenario_fields(outcome: dict) -> dict:
    """Normalize outcome scenario fields across cargo-mutants schema versions."""
    scenario = outcome.get("scenario")
    if not isinstance(scenario, dict):
        return {
            "file": "unknown",
            "line": 0,
            "function": "unknown",
            "mutation": "unknown",
        }

    # Newer cargo-mutants schema nests details under scenario.Mutant.
    mutant = scenario.get("Mutant")
    if isinstance(mutant, dict):
        function = mutant.get("function")
        if isinstance(function, dict):
            function_name = function.get("function_name", "unknown")
        elif isinstance(function, str):
            function_name = function
        else:
            function_name = "unknown"

        line = 0
        span = mutant.get("span")
        if isinstance(span, dict):
            start = span.get("start")
            if isinstance(start, dict):
                line = int(start.get("line", 0) or 0)

        mutation_name = (
            mutant.get("name")
            or mutant.get("replacement")
            or mutant.get("genre")
            or "unknown"
        )
        return {
            "file": mutant.get("file", "unknown"),
            "line": line,
            "function": function_name,
            "mutation": mutation_name,
        }

    # Legacy schema keeps these fields directly in scenario.
    function_value = scenario.get("function", "unknown")
    if isinstance(function_value, dict):
        function_name = function_value.get("function_name", "unknown")
    else:
        function_name = function_value

    return {
        "file": scenario.get("file", "unknown"),
        "line": int(scenario.get("line", 0) or 0),
        "function": function_name,
        "mutation": scenario.get("mutation", "unknown"),
    }


def run_mutants(
    modules,
    timeout=300,
    cargo_home=None,
    cargo_target_dir=None,
    offline=False,
    shard=None,
):
    """Run cargo mutants on selected modules."""
    # Build file filter args
    file_args = []
    for mod in modules:
        if mod in MODULES:
            for f in MODULES[mod]["files"]:
                file_args.extend(["-f", f])

    if not file_args:
        print("No valid modules selected.")
        return None

    cmd = [
        "cargo",
        "mutants",
        "--timeout",
        str(timeout),
        "-o",
        "mutants.out",
        "--json",
    ] + file_args
    if shard:
        cmd.extend(["--shard", shard])

    print(f"\nRunning mutation tests on: {', '.join(modules)}")
    if shard:
        print(f"Shard: {shard}")
    print(f"Command: {' '.join(cmd)}\n")
    print("-" * 60)

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

    os.chdir(SRC_DIR)
    result = subprocess.run(cmd, capture_output=False, env=env)

    return result.returncode


def parse_results():
    """Parse mutation testing results."""
    outcomes_file = find_latest_outcomes_file()

    if outcomes_file is None:
        print(f"No results found under {OUTPUT_DIR}")
        return None

    with open(outcomes_file) as f:
        data = json.load(f)

    outcomes = data.get("outcomes", [])

    # Prefer top-level counters from cargo-mutants when available.
    stats = {
        "killed": int(data.get("caught", 0)),
        "survived": int(data.get("missed", 0)),
        "timeout": int(data.get("timeout", 0)),
        "unviable": int(data.get("unviable", 0)),
        "total": int(data.get("total_mutants", len(outcomes))),
    }
    fallback = {"killed": 0, "survived": 0, "timeout": 0, "unviable": 0}

    survived_mutants = []
    survived_by_file = Counter()
    survived_by_dir = Counter()

    for outcome in outcomes:
        status = outcome.get("summary", "unknown")

        if status in CAUGHT_SUMMARIES:
            fallback["killed"] += 1
        elif status in MISSED_SUMMARIES:
            fallback["survived"] += 1
            fields = scenario_fields(outcome)
            file_path = fields["file"]
            survived_mutants.append(fields)
            survived_by_file[file_path] += 1
            survived_by_dir[str(Path(file_path).parent)] += 1
        elif status in TIMEOUT_SUMMARIES:
            fallback["timeout"] += 1
        elif status in UNVIABLE_SUMMARIES:
            fallback["unviable"] += 1

    if stats["total"] == 0:
        stats["total"] = len(outcomes)

    # Backward-compat fallback when top-level counters are absent.
    if (
        stats["killed"] + stats["survived"] + stats["timeout"] + stats["unviable"]
    ) == 0:
        stats.update(fallback)

    # Calculate score
    testable = stats["killed"] + stats["survived"] + stats["timeout"]
    score = (stats["killed"] / testable * 100) if testable > 0 else 0

    outcomes_stat = outcomes_file.stat()
    outcomes_updated_at = isoformat_utc(outcomes_stat.st_mtime)
    outcomes_age_hours = age_hours_from_timestamp(outcomes_stat.st_mtime)

    return {
        "stats": stats,
        "score": score,
        "survived": survived_mutants,
        "survived_by_file": survived_by_file,
        "survived_by_dir": survived_by_dir,
        "outcomes_path": str(outcomes_file),
        "results_dir": str(outcomes_file.parent),
        "outcomes_updated_at": outcomes_updated_at,
        "outcomes_age_hours": round(outcomes_age_hours, 2),
        "timestamp": datetime.now().isoformat(),
    }


def output_results(results, format="markdown", top_n=5):
    """Output results in specified format."""
    if results is None:
        return

    stats = results["stats"]
    score = results["score"]
    survived = results["survived"]
    survived_by_file = results["survived_by_file"]
    survived_by_dir = results["survived_by_dir"]
    outcomes_path = results["outcomes_path"]
    results_dir = results["results_dir"]
    outcomes_updated_at = results.get("outcomes_updated_at", "unknown")
    outcomes_age_hours = results.get("outcomes_age_hours")

    if format == "json":
        json_results = results.copy()
        json_results["survived_by_file"] = survived_by_file.most_common()
        json_results["survived_by_dir"] = survived_by_dir.most_common()
        print(json.dumps(json_results, indent=2))
        return

    # Markdown format (AI-readable)
    print("\n" + "=" * 60)
    print("MUTATION TESTING RESULTS")
    print("=" * 60)

    print(
        f"""
## Summary

| Metric | Value |
|--------|-------|
| Score | **{score:.1f}%** |
| Killed | {stats['killed']} |
| Survived | {stats['survived']} |
| Timeout | {stats['timeout']} |
| Unviable | {stats['unviable']} |
| Total | {stats['total']} |

Threshold: 80%
Status: {"PASS" if score >= 80 else "FAIL"}

Results dir: {results_dir}
Outcomes: {outcomes_path}
Outcomes updated: {outcomes_updated_at}
Outcomes age (hours): {outcomes_age_hours if outcomes_age_hours is not None else "unknown"}
"""
    )

    if survived:
        print("## Survived Mutants (need better tests)\n")
        print("| File | Line | Function | Mutation |")
        print("|------|------|----------|----------|")
        for m in survived[:20]:  # Limit to 20
            print(
                f"| {m['file']} | {m['line']} | {m['function']} | {m['mutation'][:50]} |"
            )

        if len(survived) > 20:
            print(f"\n... and {len(survived) - 20} more")

        print("\n## Top Files by Survived Mutants\n")
        print("| File | Survived |")
        print("|------|----------|")
        for file_path, count in survived_by_file.most_common(top_n):
            print(f"| {file_path} | {count} |")

        print("\n## Top Directories by Survived Mutants\n")
        print("| Directory | Survived |")
        print("|-----------|----------|")
        for dir_path, count in survived_by_dir.most_common(top_n):
            print(f"| {dir_path} | {count} |")

    print()

    # Save to file
    output_file = OUTPUT_DIR / "summary.md"
    with open(output_file, "w") as f:
        f.write(f"# Mutation Testing Results\n\n")
        f.write(f"Generated: {results['timestamp']}\n\n")
        f.write(f"## Score: {score:.1f}%\n\n")
        f.write(f"- Killed: {stats['killed']}\n")
        f.write(f"- Survived: {stats['survived']}\n")
        f.write(f"- Total: {stats['total']}\n")
        f.write(f"- Results dir: {results_dir}\n")
        f.write(f"- Outcomes: {outcomes_path}\n\n")
        f.write(f"- Outcomes updated: {outcomes_updated_at}\n")
        if outcomes_age_hours is not None:
            f.write(f"- Outcomes age (hours): {outcomes_age_hours}\n\n")
        if survived:
            f.write("## Top Files by Survived Mutants\n\n")
            for file_path, count in survived_by_file.most_common(top_n):
                f.write(f"- {file_path}: {count}\n")
            f.write("\n## Top Directories by Survived Mutants\n\n")
            for dir_path, count in survived_by_dir.most_common(top_n):
                f.write(f"- {dir_path}: {count}\n")

    print(f"Results saved to: {output_file}")


def main():
    """CLI entrypoint for the mutation testing helper."""
    parser = argparse.ArgumentParser(description="VoiceTerm Mutation Testing Helper")
    parser.add_argument("--all", action="store_true", help="Test all modules")
    parser.add_argument("--module", "-m", help="Specific module to test")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available modules"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--timeout", "-t", type=int, default=300, help="Timeout in seconds"
    )
    parser.add_argument(
        "--results-only", action="store_true", help="Just parse existing results"
    )
    parser.add_argument(
        "--offline", action="store_true", help="Set CARGO_NET_OFFLINE=true"
    )
    parser.add_argument("--cargo-home", help="Override CARGO_HOME for cargo mutants")
    parser.add_argument(
        "--cargo-target-dir", help="Override CARGO_TARGET_DIR for cargo mutants"
    )
    parser.add_argument("--shard", help="Run one shard, e.g. 1/8")
    parser.add_argument("--top", type=int, default=5, help="Top N paths to summarize")
    parser.add_argument(
        "--plot", action="store_true", help="Render a matplotlib hotspot plot"
    )
    parser.add_argument(
        "--plot-scope",
        choices=["file", "dir"],
        default="file",
        help="Plot hotspots by file or directory",
    )
    parser.add_argument(
        "--plot-top-pct",
        type=float,
        default=0.25,
        help="Top percentage to plot (0-1 or 0-100)",
    )
    parser.add_argument("--plot-output", help="Output path for the plot image")
    parser.add_argument(
        "--plot-show", action="store_true", help="Display the plot window"
    )

    args = parser.parse_args()

    if args.list:
        list_modules()
        return

    if args.results_only:
        results = parse_results()
        output_results(results, "json" if args.json else "markdown", top_n=args.top)
        if args.plot:
            plot_hotspots(
                results,
                args.plot_scope,
                args.plot_top_pct,
                args.plot_output,
                args.plot_show,
            )
        return

    # Select modules
    if args.all:
        modules = list(MODULES.keys())
    elif args.module:
        modules = [m.strip() for m in args.module.split(",")]
    else:
        modules = select_modules_interactive()

    print(f"\nSelected modules: {', '.join(modules)}")

    try:
        shard = parse_shard_spec(args.shard)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(2)

    # Run mutation tests
    returncode = run_mutants(
        modules,
        args.timeout,
        cargo_home=args.cargo_home,
        cargo_target_dir=args.cargo_target_dir,
        offline=args.offline,
        shard=shard,
    )

    # Parse and output results
    results = parse_results()
    output_results(results, "json" if args.json else "markdown", top_n=args.top)
    if args.plot:
        plot_hotspots(
            results,
            args.plot_scope,
            args.plot_top_pct,
            args.plot_output,
            args.plot_show,
        )

    # Exit with appropriate code
    if returncode is None:
        sys.exit(2)
    if returncode != 0:
        sys.exit(returncode)
    if results and results["score"] < 80:
        sys.exit(1)


if __name__ == "__main__":
    main()
