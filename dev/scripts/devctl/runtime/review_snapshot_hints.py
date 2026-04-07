"""Classification helpers for ReviewSnapshot reviewer hints and bundle routing.

These helpers answer three questions the external reviewer needs:
1. Which bundle class does each changed file belong to? (runtime/docs/tooling/release)
2. Do any changed files trip risk-sensitive rules (unsafe, parser, threading, ...)?
3. Do any changed files touch typed-authority surfaces that need special care?

All rules are table-driven so adopter repos can swap them via repo-pack policy.
"""

from __future__ import annotations

from dataclasses import dataclass

# Prefix tables mirror the canonical router in
# ``dev/scripts/devctl/commands/check/router_constants.py`` but are replicated
# here so the snapshot builder stays importable without pulling the full
# check-router stack. Adopter repos override these via repo-pack.
_RUNTIME_PREFIXES: tuple[str, ...] = (
    "rust/src/",
    "rust/tests/",
    "rust/benches/",
)
_RUNTIME_EXACT: frozenset[str] = frozenset(
    {
        "rust/Cargo.toml",
        "rust/Cargo.lock",
        "rust/clippy.toml",
    }
)
_DOCS_PREFIXES: tuple[str, ...] = (
    "guides/",
    "docs/",
    "img/",
)
_DOCS_EXACT: frozenset[str] = frozenset(
    {
        "README.md",
        "QUICK_START.md",
        "dev/README.md",
    }
)
_TOOLING_PREFIXES: tuple[str, ...] = (
    "dev/scripts/",
    ".github/workflows/",
    ".github/scripts/",
    "scripts/",
    "dev/config/",
    "dev/active/",
    "dev/history/",
    "dev/audits/",
    "dev/reports/",
)
_RELEASE_EXACT: frozenset[str] = frozenset(
    {
        "rust/Cargo.toml",
        "rust/Cargo.lock",
        "pypi/pyproject.toml",
    }
)


@dataclass(frozen=True, slots=True)
class RiskRule:
    """One risk-sensitive classification rule."""

    rule_id: str
    label: str
    tokens: tuple[str, ...]


_RISK_RULES: tuple[RiskRule, ...] = (
    RiskRule(
        rule_id="parser-ansi-boundary",
        label="Parser / ANSI boundary",
        tokens=("/ansi", "/parser", "prompt/strip", "pty_session"),
    ),
    RiskRule(
        rule_id="unsafe-ffi-lifecycle",
        label="Unsafe / FFI lifecycle",
        tokens=("pty_session", "terminal_restore", "rust/src/stt.rs", "unsafe"),
    ),
    RiskRule(
        rule_id="threading-lifecycle-memory",
        label="Threading / lifecycle / memory",
        tokens=(
            "pty_session",
            "terminal_restore",
            "/event_loop/",
            "memory_guard",
            "threading",
        ),
    ),
    RiskRule(
        rule_id="performance-latency",
        label="Performance / latency",
        tokens=("latency", "perf", "/event_loop/", "voice_benchmark", "/audio/"),
    ),
    RiskRule(
        rule_id="wake-word",
        label="Wake word",
        tokens=("wake_word", "voice_control/navigation", "voice_control/manager"),
    ),
    RiskRule(
        rule_id="overlay-hud-controls",
        label="Overlay / HUD / controls",
        tokens=("/hud/", "/status_line/", "/overlay", "/input/", "config/cli.rs"),
    ),
    RiskRule(
        rule_id="dependency-security",
        label="Dependency / security",
        tokens=(
            "Cargo.toml",
            "Cargo.lock",
            "pyproject.toml",
            "requirements",
            "dev/security/",
        ),
    ),
)

# Paths that carry typed-authority state in this repo. A change under one of
# these globs is a reviewer flag: expect contract-level scrutiny.
_AUTHORITY_SURFACE_SUBSTRINGS: tuple[str, ...] = (
    "startup_context.py",
    "startup_receipt.py",
    "startup_gate.py",
    "startup_push_decision.py",
    "startup_authority",
    "governed_executor",
    "reviewer_runtime",
    "reviewer_follow",
    "review_channel/bridge_",
    "review_state_contract",
    "remote_commit_pipeline",
    "project_governance",
    "task_router_contract",
    "contract_definitions.py",
    "platform/contracts.py",
    "check_router",
    "review_snapshot",
)

# Files that by name/location contain typed contract rows or models. A change
# under one of these is a signal that "a contract was mutated" — which is
# the highest-priority reviewer hint.
_CONTRACT_SUBSTRINGS: tuple[str, ...] = (
    "_contract_rows.py",
    "_contract.py",
    "_models.py",
    "contract_definitions",
    "contracts.py",
)


def classify_bundle_lane(path: str) -> str:
    """Return the bundle lane for a repo-relative path."""
    if not path:
        return "unknown"
    if path in _RELEASE_EXACT and (
        "cargo" in path.lower() or "pyproject" in path.lower()
    ):
        return "release"
    if path in _RUNTIME_EXACT or path.startswith(_RUNTIME_PREFIXES):
        return "runtime"
    if path in _DOCS_EXACT or path.startswith(_DOCS_PREFIXES):
        return "docs"
    if path.startswith(_TOOLING_PREFIXES):
        return "tooling"
    if path.endswith(".md"):
        return "docs"
    return "tooling"


def detect_risk_addons(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Return the risk rule labels triggered by any of the given paths."""
    if not paths:
        return ()
    triggered: list[str] = []
    lowered = [p.lower() for p in paths]
    for rule in _RISK_RULES:
        if rule.label in triggered:
            continue
        for token in rule.tokens:
            token_lower = token.lower()
            if any(token_lower in candidate for candidate in lowered):
                triggered.append(rule.label)
                break
    return tuple(triggered)


def detect_authority_surfaces(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Return the subset of ``paths`` that touch typed-authority surfaces."""
    if not paths:
        return ()
    matches: list[str] = []
    for path in paths:
        normalized = path.replace("\\", "/")
        for marker in _AUTHORITY_SURFACE_SUBSTRINGS:
            if marker in normalized:
                if path not in matches:
                    matches.append(path)
                break
    return tuple(matches)


def detect_contract_mutations(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Return the subset of ``paths`` that look like typed contract definitions."""
    if not paths:
        return ()
    matches: list[str] = []
    for path in paths:
        name = path.split("/")[-1]
        for marker in _CONTRACT_SUBSTRINGS:
            if marker in name or marker in path:
                if path not in matches:
                    matches.append(path)
                break
    return tuple(matches)


def build_suggested_commands(
    *,
    bundle_classes_touched: tuple[str, ...],
    risk_addons_triggered: tuple[str, ...],
    authority_surfaces_touched: tuple[str, ...],
) -> tuple[str, ...]:
    """Return deterministic verification commands for the reviewer."""
    commands: list[str] = []
    if "runtime" in bundle_classes_touched:
        commands.append("cd rust && cargo test --bin voiceterm")
        commands.append("cd rust && cargo clippy --all-targets -- -D warnings")
    if "tooling" in bundle_classes_touched or authority_surfaces_touched:
        commands.append("python3 dev/scripts/devctl.py check --profile ci")
        commands.append("python3 dev/scripts/devctl.py probe-report --format md")
    if "docs" in bundle_classes_touched or authority_surfaces_touched:
        commands.append("python3 dev/scripts/devctl.py docs-check --strict-tooling")
    if risk_addons_triggered or authority_surfaces_touched:
        commands.append(
            "python3 dev/scripts/devctl.py governance-review --format md"
        )
    # Always include the cross-surface consistency check so the reviewer can
    # confirm every typed projection (this snapshot included) agrees on the
    # same generation stamp.
    commands.append(
        "python3 dev/scripts/devctl.py check-router --format md"
    )
    # Dedupe preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for command in commands:
        if command in seen:
            continue
        seen.add(command)
        deduped.append(command)
    return tuple(deduped)


__all__ = [
    "RiskRule",
    "build_suggested_commands",
    "classify_bundle_lane",
    "detect_authority_surfaces",
    "detect_contract_mutations",
    "detect_risk_addons",
]
