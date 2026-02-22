"""devctl check command implementation."""

import os
import re
import signal
import subprocess
import time
from datetime import datetime
from typing import List
from types import SimpleNamespace

from ..common import build_env, pipe_output, run_cmd, should_emit_output, write_output
from ..config import REPO_ROOT, SRC_DIR
from ..steps import format_steps_md
from .mutation_score import build_mutation_score_cmd, resolve_outcomes_path
from .mutants import build_mutants_cmd

# Enforced maintainer-lint families (all clean at zero findings):
#   redundant_clone, redundant_closure_for_method_calls, cast_possible_wrap, dead_code
# Deferred (intentional DSP casts in audio pipeline; needs per-site #[allow] sweep first):
#   cast_precision_loss, cast_possible_truncation (20+ usize<->f32/f64 casts in signal processing)
MAINTAINER_LINT_CLIPPY_ARGS = [
    "-W",
    "clippy::redundant_clone",
    "-W",
    "clippy::redundant_closure_for_method_calls",
    "-W",
    "clippy::cast_possible_wrap",
    "-W",
    "dead_code",
]
VOICETERM_TEST_BIN_RE = re.compile(r"target/(?:debug|release)/deps/voiceterm-[0-9a-f]{8,}")
ORPHAN_TEST_MIN_AGE_SECONDS = 60


def _parse_etime_seconds(raw: str) -> int | None:
    trimmed = raw.strip()
    if not trimmed:
        return None

    days = 0
    rest = trimmed
    if "-" in trimmed:
        day_part, rest = trimmed.split("-", 1)
        if not day_part.isdigit():
            return None
        days = int(day_part)

    chunks = rest.split(":")
    if len(chunks) == 2:
        mm, ss = chunks
        if not (mm.isdigit() and ss.isdigit()):
            return None
        seconds = int(mm) * 60 + int(ss)
    elif len(chunks) == 3:
        hh, mm, ss = chunks
        if not (hh.isdigit() and mm.isdigit() and ss.isdigit()):
            return None
        seconds = int(hh) * 3600 + int(mm) * 60 + int(ss)
    else:
        return None

    return days * 86400 + seconds


def _scan_orphaned_voiceterm_test_binaries() -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,etime=,command="],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        warnings.append(f"Process sweep skipped: unable to execute ps ({exc})")
        return [], warnings

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "unknown ps error"
        warnings.append(f"Process sweep skipped: ps returned {result.returncode} ({stderr})")
        return [], warnings

    this_pid = os.getpid()
    orphaned: list[dict] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 3)
        if len(parts) != 4:
            continue

        pid_raw, ppid_raw, etime, command = parts
        if not (pid_raw.isdigit() and ppid_raw.isdigit()):
            continue
        if "ps -axo pid=,ppid=,etime=,command=" in command:
            continue
        if not VOICETERM_TEST_BIN_RE.search(command):
            continue

        pid = int(pid_raw)
        if pid == this_pid:
            continue

        elapsed_seconds = _parse_etime_seconds(etime)
        if elapsed_seconds is None:
            continue
        if int(ppid_raw) != 1:
            continue
        if elapsed_seconds < ORPHAN_TEST_MIN_AGE_SECONDS:
            continue

        orphaned.append(
            {
                "pid": pid,
                "ppid": int(ppid_raw),
                "etime": etime,
                "elapsed_seconds": elapsed_seconds,
                "command": command,
            }
        )

    orphaned.sort(key=lambda row: row["elapsed_seconds"], reverse=True)
    return orphaned, warnings


def _cleanup_orphaned_voiceterm_test_binaries(step_name: str, dry_run: bool) -> dict:
    start = time.time()
    if dry_run:
        return {
            "name": step_name,
            "cmd": ["internal", "process-sweep", "--dry-run"],
            "cwd": str(REPO_ROOT),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": True,
            "warnings": [],
            "killed_pids": [],
            "detected_orphans": 0,
        }

    orphaned, warnings = _scan_orphaned_voiceterm_test_binaries()
    killed_pids: list[int] = []
    errors: list[str] = []

    for row in orphaned:
        pid = row["pid"]
        try:
            os.kill(pid, signal.SIGKILL)
            killed_pids.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            errors.append(f"pid={pid} permission denied ({exc})")
        except OSError as exc:
            errors.append(f"pid={pid} kill failed ({exc})")

    for warning in warnings:
        print(f"[{step_name}] warning: {warning}")
    if orphaned:
        print(f"[{step_name}] detected {len(orphaned)} orphaned voiceterm test binaries")
    if killed_pids:
        print(f"[{step_name}] killed {len(killed_pids)} orphaned voiceterm test binaries")
    for error in errors:
        print(f"[{step_name}] warning: {error}")

    return {
        "name": step_name,
        "cmd": ["internal", "process-sweep", "--kill-orphans"],
        "cwd": str(REPO_ROOT),
        "returncode": 0,
        "duration_s": round(time.time() - start, 2),
        "skipped": False,
        "warnings": warnings + errors,
        "killed_pids": killed_pids,
        "detected_orphans": len(orphaned),
    }


def run(args) -> int:
    """Run the configured check profile and return exit code."""
    env = build_env(args)
    steps: List[dict] = []

    skip_build = args.skip_build
    skip_tests = args.skip_tests
    with_perf = args.with_perf
    with_mem_loop = args.with_mem_loop
    with_mutants = args.with_mutants
    with_mutation_score = args.with_mutation_score
    with_wake_guard = args.with_wake_guard
    with_ai_guard = args.with_ai_guard
    process_sweep_cleanup = not getattr(args, "no_process_sweep_cleanup", False)
    clippy_cmd = ["cargo", "clippy", "--workspace", "--all-features", "--", "-D", "warnings"]

    if args.profile == "ci":
        skip_build = True
        with_perf = False
        with_mem_loop = False
        with_mutants = False
        with_mutation_score = False
        with_wake_guard = False
        with_ai_guard = False
    elif args.profile == "prepush":
        with_perf = True
        with_mem_loop = True
        with_ai_guard = True
    elif args.profile == "release":
        with_mutation_score = True
        with_wake_guard = True
        with_ai_guard = True
    elif args.profile == "ai-guard":
        skip_build = True
        with_perf = False
        with_mem_loop = False
        with_mutants = False
        with_mutation_score = False
        with_wake_guard = False
        with_ai_guard = True
    elif args.profile == "maintainer-lint":
        skip_tests = True
        skip_build = True
        with_perf = False
        with_mem_loop = False
        with_mutants = False
        with_mutation_score = False
        with_wake_guard = False
        with_ai_guard = False
        clippy_cmd = [
            "cargo",
            "clippy",
            "--workspace",
            "--all-features",
            "--",
            "-D",
            "warnings",
            *MAINTAINER_LINT_CLIPPY_ARGS,
        ]
    elif args.profile == "quick":
        skip_build = True
        skip_tests = True
        with_wake_guard = False
        with_ai_guard = False

    def add_step(name: str, cmd: List[str], cwd=None, step_env=None) -> None:
        result = run_cmd(name, cmd, cwd=cwd, env=step_env or env, dry_run=args.dry_run)
        steps.append(result)
        if result["returncode"] != 0 and not args.keep_going:
            raise RuntimeError(f"{name} failed")

    if process_sweep_cleanup:
        steps.append(
            _cleanup_orphaned_voiceterm_test_binaries(
                step_name="process-sweep-pre",
                dry_run=args.dry_run,
            )
        )

    try:
        if not args.skip_fmt:
            if args.fix:
                add_step("fmt", ["cargo", "fmt", "--all"], cwd=SRC_DIR)
            else:
                add_step(
                    "fmt-check",
                    ["cargo", "fmt", "--all", "--", "--check"],
                    cwd=SRC_DIR,
                )
        if not args.skip_clippy:
            add_step(
                "clippy",
                clippy_cmd,
                cwd=SRC_DIR,
            )
        if with_ai_guard:
            add_step(
                "code-shape-guard",
                ["python3", "dev/scripts/check_code_shape.py"],
                cwd=REPO_ROOT,
            )
            add_step(
                "rust-lint-debt-guard",
                ["python3", "dev/scripts/check_rust_lint_debt.py"],
                cwd=REPO_ROOT,
            )
            add_step(
                "rust-best-practices-guard",
                ["python3", "dev/scripts/check_rust_best_practices.py"],
                cwd=REPO_ROOT,
            )
        if not skip_tests:
            add_step("test", ["cargo", "test", "--workspace", "--all-features"], cwd=SRC_DIR)
        if not skip_build:
            add_step(
                "build-release",
                ["cargo", "build", "--release", "--bin", "voiceterm"],
                cwd=SRC_DIR,
            )
        if with_wake_guard:
            wake_guard_env = dict(env)
            wake_guard_env["WAKE_WORD_SOAK_ROUNDS"] = str(args.wake_soak_rounds)
            add_step(
                "wake-guard",
                ["bash", "dev/scripts/tests/wake_word_guard.sh"],
                cwd=REPO_ROOT,
                step_env=wake_guard_env,
            )
        if with_perf:
            add_step(
                "perf-smoke",
                [
                    "cargo",
                    "test",
                    "--no-default-features",
                    "legacy_tui::tests::perf_smoke_emits_voice_metrics",
                    "--",
                    "--nocapture",
                ],
                cwd=SRC_DIR,
            )
            if not args.dry_run:
                log_path = subprocess.check_output(
                    [
                        "python3",
                        "-c",
                        "import os, tempfile; print(os.path.join(tempfile.gettempdir(), 'voiceterm_tui.log'))",
                    ],
                    text=True,
                ).strip()
                add_step(
                    "perf-verify",
                    ["python3", ".github/scripts/verify_perf_metrics.py", log_path],
                    cwd=REPO_ROOT,
                )
        if with_mem_loop:
            iterations = args.mem_iterations
            for i in range(iterations):
                add_step(
                    f"mem-guard-{i+1}",
                    [
                        "cargo",
                        "test",
                        "--no-default-features",
                        "legacy_tui::tests::memory_guard_backend_threads_drop",
                        "--",
                        "--nocapture",
                    ],
                    cwd=SRC_DIR,
                )
        if with_mutants:
            mutants_args = SimpleNamespace(
                all=args.mutants_all,
                module=args.mutants_module,
                timeout=args.mutants_timeout,
                shard=args.mutants_shard,
                results_only=False,
                json=False,
                offline=args.mutants_offline,
                cargo_home=args.mutants_cargo_home,
                cargo_target_dir=args.mutants_cargo_target_dir,
                plot=args.mutants_plot,
                plot_scope=args.mutants_plot_scope,
                plot_top_pct=args.mutants_plot_top_pct,
                plot_output=args.mutants_plot_output,
                plot_show=args.mutants_plot_show,
                top=None,
            )
            add_step("mutants", build_mutants_cmd(mutants_args), cwd=REPO_ROOT)
        if with_mutation_score:
            outcomes_path = resolve_outcomes_path(args.mutation_score_path)
            if outcomes_path is None:
                raise RuntimeError("mutation outcomes.json not found")
            add_step(
                "mutation-score",
                build_mutation_score_cmd(
                    outcomes_path,
                    args.mutation_score_threshold,
                    args.mutation_score_max_age_hours,
                    args.mutation_score_warn_age_hours,
                ),
                cwd=REPO_ROOT,
            )
    except RuntimeError:
        pass
    finally:
        if process_sweep_cleanup:
            steps.append(
                _cleanup_orphaned_voiceterm_test_binaries(
                    step_name="process-sweep-post",
                    dry_run=args.dry_run,
                )
            )

    success = all(step["returncode"] == 0 for step in steps)
    report = {
        "command": "check",
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "steps": steps,
    }

    output = None
    if should_emit_output(args):
        if args.format == "json":
            output = json_dumps(report)
        elif args.format == "md":
            output = "# devctl check\n\n" + format_steps_md(steps)
        else:
            output = json_dumps(report)
        if args.output or args.format != "text":
            write_output(output, args.output)
        if args.pipe_command:
            pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
            if pipe_rc != 0:
                return pipe_rc
    return 0 if success else 1


def json_dumps(payload: dict) -> str:
    import json

    return json.dumps(payload, indent=2)
