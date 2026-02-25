"""Static command catalog for the desktop command center.

The catalog intentionally reuses existing repo command surfaces (`devctl`,
checks, `git`, `cargo`, and selected workflow commands) so the desktop app
acts as an operator shell over existing guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    """Describes one runnable command in the catalog."""

    id: str
    group: str
    label: str
    description: str
    command: str


def all_commands() -> list[CommandSpec]:
    """Return the full command catalog."""

    return [
        CommandSpec(
            id="bootstrap_status",
            group="Bootstrap",
            label="Git Status (short)",
            description="Quick workspace dirty-tree check.",
            command="git status --short",
        ),
        CommandSpec(
            id="bootstrap_branch",
            group="Bootstrap",
            label="Current Branch",
            description="Show current git branch name.",
            command="git branch --show-current",
        ),
        CommandSpec(
            id="bootstrap_remote",
            group="Bootstrap",
            label="Git Remotes",
            description="List configured remotes.",
            command="git remote -v",
        ),
        CommandSpec(
            id="bootstrap_log",
            group="Bootstrap",
            label="Recent Commits",
            description="Show recent commit history.",
            command="git log --oneline --decorate -n 10",
        ),
        CommandSpec(
            id="bootstrap_active_index",
            group="Bootstrap",
            label="Active Index",
            description="Read active-doc registry.",
            command="sed -n '1,220p' dev/active/INDEX.md",
        ),
        CommandSpec(
            id="bootstrap_devctl_list",
            group="Bootstrap",
            label="devctl list",
            description="List devctl command surfaces.",
            command="python3 dev/scripts/devctl.py list",
        ),
        CommandSpec(
            id="bootstrap_args_files",
            group="Bootstrap",
            label="Root --* Files",
            description="Guard against accidental root argument files.",
            command="find . -maxdepth 1 -type f -name '--*'",
        ),
        CommandSpec(
            id="runtime_ci",
            group="Checks",
            label="devctl check (ci)",
            description="Primary runtime check profile.",
            command="python3 dev/scripts/devctl.py check --profile ci",
        ),
        CommandSpec(
            id="runtime_release",
            group="Checks",
            label="devctl check (release)",
            description="Full release preflight bundle.",
            command="python3 dev/scripts/devctl.py check --profile release",
        ),
        CommandSpec(
            id="docs_user",
            group="Checks",
            label="docs-check (user-facing)",
            description="Validate user docs coverage for changed behavior.",
            command="python3 dev/scripts/devctl.py docs-check --user-facing",
        ),
        CommandSpec(
            id="docs_strict",
            group="Checks",
            label="docs-check (strict tooling)",
            description="Validate tooling/process docs governance.",
            command="python3 dev/scripts/devctl.py docs-check --strict-tooling",
        ),
        CommandSpec(
            id="hygiene",
            group="Checks",
            label="devctl hygiene",
            description="Archive/ADR/scripts governance and process sweep.",
            command="python3 dev/scripts/devctl.py hygiene",
        ),
        CommandSpec(
            id="check_active_plan",
            group="Checks",
            label="check_active_plan_sync",
            description="Ensure active plan docs are synchronized.",
            command="python3 dev/scripts/checks/check_active_plan_sync.py",
        ),
        CommandSpec(
            id="check_multi_agent",
            group="Checks",
            label="check_multi_agent_sync",
            description="Validate multi-agent coordination ledger consistency.",
            command="python3 dev/scripts/checks/check_multi_agent_sync.py",
        ),
        CommandSpec(
            id="check_cli_flags",
            group="Checks",
            label="check_cli_flags_parity",
            description="Ensure docs/CLI flags parity.",
            command="python3 dev/scripts/checks/check_cli_flags_parity.py",
        ),
        CommandSpec(
            id="check_screenshots",
            group="Checks",
            label="check_screenshot_integrity",
            description="Validate screenshot references and staleness.",
            command="python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120",
        ),
        CommandSpec(
            id="check_code_shape",
            group="Checks",
            label="check_code_shape",
            description="Guard source-file size/shape boundaries.",
            command="python3 dev/scripts/checks/check_code_shape.py",
        ),
        CommandSpec(
            id="check_rust_debt",
            group="Checks",
            label="check_rust_lint_debt",
            description="Guard Rust lint debt growth.",
            command="python3 dev/scripts/checks/check_rust_lint_debt.py",
        ),
        CommandSpec(
            id="check_rust_best",
            group="Checks",
            label="check_rust_best_practices",
            description="Guard Rust best-practice regressions.",
            command="python3 dev/scripts/checks/check_rust_best_practices.py",
        ),
        CommandSpec(
            id="orchestrate_status",
            group="Control Plane",
            label="orchestrate-status",
            description="Single-view orchestrator summary.",
            command="python3 dev/scripts/devctl.py orchestrate-status --format md",
        ),
        CommandSpec(
            id="orchestrate_watch",
            group="Control Plane",
            label="orchestrate-watch",
            description="Stale-lane watchdog for orchestrator.",
            command="python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md",
        ),
        CommandSpec(
            id="devctl_status_ci",
            group="Control Plane",
            label="devctl status --ci",
            description="CI-oriented status summary.",
            command="python3 dev/scripts/devctl.py status --ci --format md",
        ),
        CommandSpec(
            id="triage_loop_report",
            group="Control Plane",
            label="triage-loop (report-only)",
            description="Run bounded CodeRabbit triage loop in report mode.",
            command=(
                "python3 dev/scripts/devctl.py triage-loop --repo jguida941/voiceterm "
                "--branch develop --mode report-only --source-event workflow_dispatch "
                "--notify summary-only --comment-target auto --max-attempts 1 --format md"
            ),
        ),
        CommandSpec(
            id="controller_action_refresh",
            group="Control Plane",
            label="controller-action refresh-status",
            description="Execute guarded controller refresh action.",
            command="python3 dev/scripts/devctl.py controller-action --action refresh-status --format md",
        ),
        CommandSpec(
            id="controller_action_dispatch",
            group="Control Plane",
            label="controller-action dispatch-report-only (dry-run)",
            description="Preview guarded report-only dispatch action.",
            command=(
                "python3 dev/scripts/devctl.py controller-action "
                "--action dispatch-report-only --dry-run --format md"
            ),
        ),
        CommandSpec(
            id="phone_status",
            group="Control Plane",
            label="phone-status (compact)",
            description="Render phone-safe control-plane projection.",
            command="python3 dev/scripts/devctl.py phone-status --view compact --format md",
        ),
        CommandSpec(
            id="autonomy_report",
            group="Control Plane",
            label="autonomy-report",
            description="Generate autonomy digest bundle.",
            command=(
                "python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy "
                "--library-root dev/reports/autonomy/library --run-label command-center --format md"
            ),
        ),
        CommandSpec(
            id="coderabbit_gate_develop",
            group="GitHub",
            label="CodeRabbit Gate (develop)",
            description="Verify triage gate on current HEAD.",
            command="python3 dev/scripts/checks/check_coderabbit_gate.py --branch develop",
        ),
        CommandSpec(
            id="coderabbit_ralph_gate_develop",
            group="GitHub",
            label="CodeRabbit Ralph Gate (develop)",
            description="Verify Ralph loop gate on current HEAD.",
            command="python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch develop",
        ),
        CommandSpec(
            id="dispatch_ralph_report",
            group="GitHub",
            label="Dispatch Ralph Loop (report-only)",
            description="Start workflow-dispatch Ralph loop on develop.",
            command=(
                "gh workflow run coderabbit_ralph_loop.yml --ref develop "
                "-f branch=develop -f execution_mode=report-only "
                "-f notify_mode=summary-only -f comment_target=commit"
            ),
        ),
        CommandSpec(
            id="release_preflight_dispatch",
            group="GitHub",
            label="Dispatch Release Preflight",
            description="Trigger release preflight workflow manually.",
            command='gh workflow run release_preflight.yml -f version="1.0.93"',
        ),
        CommandSpec(
            id="rust_tests_bin",
            group="Rust",
            label="cargo test --bin voiceterm",
            description="Run full voiceterm binary test suite.",
            command="cd rust && cargo test --bin voiceterm",
        ),
        CommandSpec(
            id="rust_build_release",
            group="Rust",
            label="cargo build --release --bin voiceterm",
            description="Build release binary for voiceterm.",
            command="cd rust && cargo build --release --bin voiceterm",
        ),
        CommandSpec(
            id="rust_fmt",
            group="Rust",
            label="cargo fmt --all",
            description="Format Rust workspace sources.",
            command="cd rust && cargo fmt --all",
        ),
        CommandSpec(
            id="rust_clippy",
            group="Rust",
            label="cargo clippy --all-targets",
            description="Run clippy lint checks.",
            command="cd rust && cargo clippy --all-targets -- -D warnings",
        ),
        CommandSpec(
            id="git_fetch",
            group="Git",
            label="git fetch origin",
            description="Fetch latest remote refs.",
            command="git fetch origin",
        ),
        CommandSpec(
            id="git_pull_develop",
            group="Git",
            label="git pull --ff-only origin develop",
            description="Fast-forward local develop branch.",
            command="git pull --ff-only origin develop",
        ),
        CommandSpec(
            id="git_push_develop",
            group="Git",
            label="git push origin develop",
            description="Push local develop to origin.",
            command="git push origin develop",
        ),
        CommandSpec(
            id="git_log_20",
            group="Git",
            label="git log -n 20",
            description="Show 20 recent commits with refs.",
            command="git log --oneline --decorate -n 20",
        ),
        CommandSpec(
            id="markdownlint_docs",
            group="Docs",
            label="markdownlint docs set",
            description="Run markdownlint on canonical docs scope.",
            command=(
                "markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore "
                "README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md "
                "scripts/README.md pypi/README.md app/README.md"
            ),
        ),
        CommandSpec(
            id="release_version_parity",
            group="Release",
            label="check_release_version_parity",
            description="Validate version parity across release metadata.",
            command="python3 dev/scripts/checks/check_release_version_parity.py",
        ),
        CommandSpec(
            id="security_scan",
            group="Security",
            label="devctl security",
            description="Run security policy checks.",
            command="python3 dev/scripts/devctl.py security",
        ),
    ]

