"""Static classification/risk constants used by check-router helpers."""

from __future__ import annotations

BUNDLE_BY_LANE = {
    "docs": "bundle.docs",
    "runtime": "bundle.runtime",
    "tooling": "bundle.tooling",
    "release": "bundle.release",
}

RELEASE_EXACT_PATHS = {
    "rust/Cargo.toml",
    "rust/Cargo.lock",
    "pypi/pyproject.toml",
    "app/macos/VoiceTerm.app/Contents/Info.plist",
}

RELEASE_WORKFLOW_FILES = {
    "release_preflight.yml",
    "publish_pypi.yml",
    "publish_homebrew.yml",
    "publish_release_binaries.yml",
    "release_attestation.yml",
}

TOOLING_EXACT_PATHS = {
    "AGENTS.md",
    "Makefile",
    "dev/ARCHITECTURE.md",
    "dev/DEVELOPMENT.md",
    "dev/MCP_DEVCTL_ALIGNMENT.md",
    "dev/guides/DEVELOPMENT.md",
    "dev/guides/ARCHITECTURE.md",
    "dev/guides/DEVCTL_AUTOGUIDE.md",
    "dev/guides/MCP_DEVCTL_ALIGNMENT.md",
    "dev/scripts/README.md",
    "dev/DEVCTL_AUTOGUIDE.md",
    "dev/history/ENGINEERING_EVOLUTION.md",
}

TOOLING_PREFIXES = (
    "dev/scripts/",
    ".github/workflows/",
    ".github/scripts/",
    "scripts/macro-packs/",
)

RUNTIME_PREFIXES = (
    "rust/src/",
    "rust/tests/",
    "rust/benches/",
)

DOCS_PREFIXES = (
    "guides/",
    "img/",
    "docs/",
)

DOCS_EXACT_PATHS = {
    "README.md",
    "QUICK_START.md",
    "DEV_INDEX.md",
    "dev/README.md",
    "scripts/README.md",
    "pypi/README.md",
    "app/README.md",
}

RISK_ADDONS = (
    {
        "id": "overlay-hud-controls",
        "label": "Overlay/input/status/HUD add-ons",
        "tokens": (
            "/hud/",
            "/status_line/",
            "/overlay",
            "/input/",
            "rust/src/bin/voiceterm/config/cli.rs",
            "rust/src/config/mod.rs",
        ),
        "commands": (
            "python3 dev/scripts/devctl.py check --profile ci",
            "cd rust && cargo test --bin voiceterm",
            "python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel",
        ),
    },
    {
        "id": "performance-latency",
        "label": "Performance/latency add-ons",
        "tokens": (
            "latency",
            "perf",
            "/event_loop/",
            "voice_benchmark",
            "/audio/",
        ),
        "commands": (
            "python3 dev/scripts/devctl.py check --profile prepush",
            "./dev/scripts/tests/measure_latency.sh --voice-only --synthetic",
            "./dev/scripts/tests/measure_latency.sh --ci-guard",
            "python3 dev/scripts/devctl.py process-cleanup --verify --format md",
        ),
    },
    {
        "id": "wake-word",
        "label": "Wake-word add-ons",
        "tokens": (
            "wake_word",
            "voice_control/navigation",
            "voice_control/manager",
        ),
        "commands": (
            "bash dev/scripts/tests/wake_word_guard.sh",
            "python3 dev/scripts/devctl.py check --profile release",
            "python3 dev/scripts/devctl.py process-cleanup --verify --format md",
        ),
    },
    {
        "id": "threading-lifecycle-memory",
        "label": "Threading/lifecycle/memory add-ons",
        "tokens": (
            "pty_session",
            "terminal_restore",
            "/event_loop/",
            "memory_guard",
        ),
        "commands": (
            "cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture",
            "python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel",
        ),
    },
    {
        "id": "unsafe-ffi-lifecycle",
        "label": "Unsafe/FFI lifecycle add-ons",
        "tokens": (
            "pty_session",
            "terminal_restore",
            "rust/src/stt.rs",
        ),
        "commands": (
            "cd rust && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture",
            "cd rust && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture",
            "cd rust && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture",
            "python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel",
        ),
    },
    {
        "id": "parser-ansi-boundary",
        "label": "Parser/ANSI boundary add-ons",
        "tokens": (
            "/ansi",
            "/parser",
            "prompt/strip",
            "pty_session",
        ),
        "commands": (
            "cd rust && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture",
            "cd rust && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture",
            "cd rust && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture",
            "python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel",
        ),
    },
    {
        "id": "dependency-security",
        "label": "Dependency/security-hardening add-ons",
        "tokens": (
            "Cargo.toml",
            "Cargo.lock",
            "pyproject.toml",
            "requirements",
            "dev/security/",
            "security_guard.yml",
        ),
        "commands": ("python3 dev/scripts/devctl.py security",),
    },
)
