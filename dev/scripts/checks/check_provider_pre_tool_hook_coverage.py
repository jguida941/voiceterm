#!/usr/bin/env python3
"""A16 G19 guard: provider pre-tool hook coverage.

Per delete_after_ingest.md A16 G19, this guard verifies that every
mutation-capable provider/role lane has a proven pre-tool interception path
for file mutation tools. The guard:

- Inspects ``.claude/settings.json`` for Claude's PreToolUse coverage of
  ``Edit|Write|MultiEdit``, invocation of ``check_role_lane_mutation_authority.py``,
  ``--mode pre_mutation``, and ``--tool-input-stdin``.
- Inspects typed provider metadata (``dev/config/devctl_policies/launcher.json``
  and ``dev/state/provider_pre_tool_hook_coverage.jsonl`` when present) for
  other providers — Codex, Cursor, Gemini, future providers.
- Distinguishes four hook states:
    ``hook_tested`` — configured AND a typed execution receipt exists.
    ``hook_configured`` — config present but no execution proof yet.
    ``hook_missing`` — no configuration and no typed blocker.
    ``hook_unavailable_blocker`` — typed blocker explains absence.

The guard fails closed for any provider that is not ``hook_tested`` or
``hook_unavailable_blocker`` (with an accepted typed blocker).

Machine reasons (stable across releases):
    provider_pre_tool_hook_missing
    provider_pre_tool_hook_unproven
    provider_pre_tool_hook_not_pre_mutation
    provider_hook_claim_without_test
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.value_coercion import (  # noqa: E402
    coerce_bool,
    coerce_string,
)


COMMAND = "check_provider_pre_tool_hook_coverage"
CONTRACT_ID = "ProviderPreToolHookCoverageGuard"

PROVIDER_HOOK_MISSING_REASON = "provider_pre_tool_hook_missing"
PROVIDER_HOOK_UNPROVEN_REASON = "provider_pre_tool_hook_unproven"
PROVIDER_HOOK_NOT_PRE_MUTATION_REASON = "provider_pre_tool_hook_not_pre_mutation"
PROVIDER_HOOK_CLAIM_WITHOUT_TEST_REASON = "provider_hook_claim_without_test"

HOOK_STATE_TESTED = "hook_tested"
HOOK_STATE_CONFIGURED = "hook_configured"
HOOK_STATE_MISSING = "hook_missing"
HOOK_STATE_UNAVAILABLE_BLOCKER = "hook_unavailable_blocker"

# rev_pkt_4819: per-provider state precedence used by _dedupe_provider_states
# so a typed tested evidence override (via provider_metadata) wins over a
# weaker config-layer derivation (.claude/settings.json, .codex/hooks.json,
# registry.agents). Higher number = stronger evidence.
HOOK_STATE_PRECEDENCE = {
    HOOK_STATE_TESTED: 4,
    HOOK_STATE_UNAVAILABLE_BLOCKER: 3,
    HOOK_STATE_CONFIGURED: 2,
    HOOK_STATE_MISSING: 1,
}

REQUIRED_TOOL_MATCHER = "Edit|Write|MultiEdit"
REQUIRED_GUARD_SCRIPT = "check_role_lane_mutation_authority.py"
REQUIRED_MODE_FLAG = "--mode pre_mutation"
REQUIRED_STDIN_FLAG = "--tool-input-stdin"

DEFAULT_CLAUDE_SETTINGS_PATH = REPO_ROOT / ".claude/settings.json"
DEFAULT_CODEX_HOOKS_PATH = REPO_ROOT / ".codex/hooks.json"
DEFAULT_PROVIDER_METADATA_PATH = (
    REPO_ROOT / "dev/state/provider_pre_tool_hook_coverage.jsonl"
)
DEFAULT_LAUNCHER_POLICY_PATH = (
    REPO_ROOT / "dev/config/devctl_policies/launcher.json"
)
DEFAULT_REVIEW_CHANNEL_STATE_PATH = (
    REPO_ROOT / "dev/reports/review_channel/state/latest.json"
)


@dataclass(frozen=True, slots=True)
class ProviderHookState:
    provider: str
    state: str
    source: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class HookCoverageViolation:
    reason: str
    detail: str
    provider: str
    severity: str = "blocking"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProviderHookCoverageReport:
    ok: bool
    provider_states: tuple[dict[str, str], ...]
    violations: tuple[dict[str, str], ...] = field(default_factory=tuple)
    checked_surfaces: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    command: str = COMMAND
    timestamp: str = ""
    schema_version: int = 1
    contract_id: str = CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["provider_states"] = list(self.provider_states)
        payload["violations"] = list(self.violations)
        payload["checked_surfaces"] = list(self.checked_surfaces)
        payload["warnings"] = list(self.warnings)
        return payload


def build_report(
    *,
    report_override: Mapping[str, object] | None = None,
    claude_settings_path: Path = DEFAULT_CLAUDE_SETTINGS_PATH,
    codex_hooks_path: Path = DEFAULT_CODEX_HOOKS_PATH,
    provider_metadata_path: Path = DEFAULT_PROVIDER_METADATA_PATH,
    launcher_policy_path: Path = DEFAULT_LAUNCHER_POLICY_PATH,
    review_channel_state_path: Path = DEFAULT_REVIEW_CHANNEL_STATE_PATH,
) -> dict[str, object]:
    if report_override is not None:
        states = _states_from_fixture(report_override)
        checked = ("fixture",)
        warnings: tuple[str, ...] = ()
    else:
        states, checked, warnings = _states_from_live(
            claude_settings_path=claude_settings_path,
            codex_hooks_path=codex_hooks_path,
            provider_metadata_path=provider_metadata_path,
            launcher_policy_path=launcher_policy_path,
            review_channel_state_path=review_channel_state_path,
        )
    # rev_pkt_4819: dedupe per-provider using HOOK_STATE_PRECEDENCE so typed
    # tested evidence overrides the weaker config-layer derivation.
    states = _dedupe_provider_states(states)
    return evaluate_provider_hook_coverage(
        provider_states=states,
        checked_surfaces=checked,
        warnings=warnings,
    ).to_dict()


def _dedupe_provider_states(
    states: Sequence[ProviderHookState],
) -> list[ProviderHookState]:
    """Collapse multiple states for the same provider down to the strongest.

    The provider is identified by ``ProviderHookState.provider``. Strength is
    defined by ``HOOK_STATE_PRECEDENCE`` (higher wins). Insertion order of the
    surviving entries is preserved so the output remains deterministic.
    """
    chosen: dict[str, ProviderHookState] = {}
    order: list[str] = []
    for state in states:
        key = state.provider
        if not key:
            continue
        existing = chosen.get(key)
        if existing is None:
            chosen[key] = state
            order.append(key)
            continue
        if (
            HOOK_STATE_PRECEDENCE.get(state.state, 0)
            > HOOK_STATE_PRECEDENCE.get(existing.state, 0)
        ):
            chosen[key] = state
    return [chosen[k] for k in order]


def evaluate_provider_hook_coverage(
    *,
    provider_states: Sequence[ProviderHookState],
    checked_surfaces: Iterable[str] = (),
    warnings: Iterable[str] = (),
) -> ProviderHookCoverageReport:
    violations: list[HookCoverageViolation] = []
    for state in provider_states:
        violations.extend(_violations_for_state(state))
    ok = not violations
    return ProviderHookCoverageReport(
        ok=ok,
        provider_states=tuple(s.to_dict() for s in provider_states),
        violations=tuple(v.to_dict() for v in violations),
        checked_surfaces=tuple(checked_surfaces),
        warnings=tuple(warnings),
        timestamp=utc_timestamp(),
    )


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    states = report.get("provider_states") or []
    if isinstance(states, Sequence) and not isinstance(states, (str, bytes)):
        for state in states:
            if isinstance(state, Mapping):
                lines.append(
                    f"- {state.get('provider')}: {state.get('state')} "
                    f"(source={state.get('source')})"
                )
    violations = report.get("violations") or []
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        if violations:
            lines.extend(("", "## Violations", ""))
        for v in violations:
            if isinstance(v, Mapping):
                lines.append(f"- {v.get('reason')}: {v.get('detail', '')}")
    return "\n".join(lines)


def evaluate_claude_settings(settings: Mapping[str, object]) -> ProviderHookState:
    """Public helper: classify Claude provider hook coverage from a parsed
    ``.claude/settings.json`` document. Returns a ProviderHookState.
    """
    return _classify_claude_settings(settings, source=".claude/settings.json")


def evaluate_codex_hooks(hooks_doc: Mapping[str, object]) -> ProviderHookState:
    """Public helper: classify Codex provider hook coverage from a parsed
    ``.codex/hooks.json`` document. Returns a ProviderHookState.
    """
    return _classify_codex_hooks(hooks_doc, source=".codex/hooks.json")


def derive_provider_hook_state_map(
    *,
    claude_settings_path: Path = DEFAULT_CLAUDE_SETTINGS_PATH,
    codex_hooks_path: Path = DEFAULT_CODEX_HOOKS_PATH,
    provider_metadata_path: Path = DEFAULT_PROVIDER_METADATA_PATH,
    launcher_policy_path: Path = DEFAULT_LAUNCHER_POLICY_PATH,
    review_channel_state_path: Path = DEFAULT_REVIEW_CHANNEL_STATE_PATH,
    fixture: Mapping[str, object] | None = None,
) -> dict[str, str]:
    """Per rev_pkt_4820: return effective provider->hook_state mapping for
    cross-guard consumption (e.g. check_active_topology_liveness G20).

    The returned mapping reflects the same precedence/dedup logic as
    ``build_report`` so callers see one canonical state per provider. Pass
    ``fixture`` to derive from a fixture payload instead of live files.
    """
    if fixture is not None:
        states = _states_from_fixture(fixture)
    else:
        states, _, _ = _states_from_live(
            claude_settings_path=claude_settings_path,
            codex_hooks_path=codex_hooks_path,
            provider_metadata_path=provider_metadata_path,
            launcher_policy_path=launcher_policy_path,
            review_channel_state_path=review_channel_state_path,
        )
    deduped = _dedupe_provider_states(states)
    return {s.provider: s.state for s in deduped if s.provider}


def _states_from_fixture(
    override: Mapping[str, object],
) -> list[ProviderHookState]:
    states: list[ProviderHookState] = []
    raw = override.get("provider_states")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for entry in raw:
            if isinstance(entry, Mapping):
                states.append(
                    ProviderHookState(
                        provider=coerce_string(entry.get("provider")).strip(),
                        state=coerce_string(entry.get("state")).strip(),
                        source=coerce_string(entry.get("source")).strip(),
                        detail=coerce_string(entry.get("detail")).strip(),
                    )
                )
    claude_settings = override.get("claude_settings")
    if isinstance(claude_settings, Mapping):
        states.append(_classify_claude_settings(claude_settings, source="fixture"))
    codex_hooks = override.get("codex_hooks")
    if isinstance(codex_hooks, Mapping):
        states.append(_classify_codex_hooks(codex_hooks, source="fixture"))
    metadata = override.get("provider_metadata")
    if isinstance(metadata, Sequence) and not isinstance(metadata, (str, bytes)):
        for entry in metadata:
            if isinstance(entry, Mapping):
                states.append(_classify_provider_metadata(entry, source="fixture"))
    # rev_pkt_4816 — fixture may also declare live-shape review-channel state
    review_channel_state = override.get("review_channel_state")
    if isinstance(review_channel_state, Mapping):
        seen = {s.provider for s in states}
        for provider in _providers_from_review_channel_state(review_channel_state):
            if provider in seen:
                continue
            states.append(
                ProviderHookState(
                    provider=provider,
                    state=HOOK_STATE_MISSING,
                    source="fixture:review_channel_state.registry.agents",
                    detail=(
                        f"Provider {provider!r} is active in review-channel "
                        "registry.agents but has no pre-tool hook coverage."
                    ),
                )
            )
    return states


def _providers_from_review_channel_state(
    state: Mapping[str, object],
) -> list[str]:
    """Extract distinct provider identifiers from ``registry.agents`` so the
    G19 guard emits one row per active provider/role/session gap.
    """
    registry = state.get("registry")
    if not isinstance(registry, Mapping):
        return []
    agents = registry.get("agents")
    providers: list[str] = []
    seen: set[str] = set()
    if not isinstance(agents, Sequence) or isinstance(agents, (str, bytes)):
        return providers
    for entry in agents:
        if not isinstance(entry, Mapping):
            continue
        name = coerce_string(entry.get("provider")).strip()
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        providers.append(name)
    return providers


def _states_from_live(
    *,
    claude_settings_path: Path,
    codex_hooks_path: Path,
    provider_metadata_path: Path,
    launcher_policy_path: Path,
    review_channel_state_path: Path,
) -> tuple[list[ProviderHookState], tuple[str, ...], tuple[str, ...]]:
    states: list[ProviderHookState] = []
    checked: list[str] = []
    warnings: list[str] = []

    checked.append(str(claude_settings_path))
    if claude_settings_path.exists():
        try:
            settings = json.loads(claude_settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"{claude_settings_path}: parse error: {exc}")
            settings = {}
        if not isinstance(settings, Mapping):
            settings = {}
        states.append(
            _classify_claude_settings(settings, source=str(claude_settings_path))
        )
    else:
        states.append(
            ProviderHookState(
                provider="claude",
                state=HOOK_STATE_MISSING,
                source=str(claude_settings_path),
                detail="Claude settings file does not exist.",
            )
        )

    # rev_pkt_4818: codex provider has a native PreToolUse hook surface at
    # .codex/hooks.json (declared by extension_bundle_defaults.py codex_hooks).
    # Read it before the typed-metadata source so the typed config-layer file
    # takes precedence over the looser registry.agents observation.
    checked.append(str(codex_hooks_path))
    if codex_hooks_path.exists():
        try:
            hooks_doc = json.loads(codex_hooks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            warnings.append(f"{codex_hooks_path}: parse error: {exc}")
            hooks_doc = {}
        if not isinstance(hooks_doc, Mapping):
            hooks_doc = {}
        states.append(_classify_codex_hooks(hooks_doc, source=str(codex_hooks_path)))

    checked.append(str(provider_metadata_path))
    metadata_entries = _read_provider_metadata(provider_metadata_path)
    for entry in metadata_entries:
        states.append(_classify_provider_metadata(entry, source=str(provider_metadata_path)))

    checked.append(str(launcher_policy_path))
    declared_providers = _read_declared_providers(launcher_policy_path)
    seen = {s.provider for s in states}
    for provider in declared_providers:
        if provider in seen or not provider:
            continue
        states.append(
            ProviderHookState(
                provider=provider,
                state=HOOK_STATE_MISSING,
                source=str(launcher_policy_path),
                detail=(
                    f"Provider {provider!r} is declared by launcher policy but "
                    "has no pre-tool hook metadata at "
                    f"{provider_metadata_path}."
                ),
            )
        )
        seen.add(provider)

    # rev_pkt_4816: live review-channel state's registry.agents is the
    # authoritative live source of active provider/role/session lanes.
    # Any provider active there but missing from hook-coverage sources gets a
    # hook_missing entry so the guard never silently omits a real provider.
    checked.append(str(review_channel_state_path))
    live_providers = _read_review_channel_active_providers(review_channel_state_path)
    for provider in live_providers:
        if provider in seen or not provider:
            continue
        states.append(
            ProviderHookState(
                provider=provider,
                state=HOOK_STATE_MISSING,
                source=str(review_channel_state_path),
                detail=(
                    f"Provider {provider!r} is active in review-channel "
                    "registry.agents but has no pre-tool hook metadata in "
                    f"{provider_metadata_path} or {claude_settings_path}."
                ),
            )
        )
        seen.add(provider)
    return states, tuple(checked), tuple(warnings)


def _read_review_channel_active_providers(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, Mapping):
        return []
    return _providers_from_review_channel_state(payload)


def _classify_claude_settings(
    settings: Mapping[str, object],
    *,
    source: str,
) -> ProviderHookState:
    hooks = _mapping(settings.get("hooks"))
    pre_tool = hooks.get("PreToolUse")
    if not isinstance(pre_tool, Sequence) or isinstance(pre_tool, (str, bytes)):
        return ProviderHookState(
            provider="claude",
            state=HOOK_STATE_MISSING,
            source=source,
            detail="No PreToolUse hooks declared in Claude settings.",
        )
    target = None
    for entry in pre_tool:
        if not isinstance(entry, Mapping):
            continue
        if coerce_string(entry.get("matcher")).strip() == REQUIRED_TOOL_MATCHER:
            target = entry
            break
    if target is None:
        return ProviderHookState(
            provider="claude",
            state=HOOK_STATE_MISSING,
            source=source,
            detail=(
                f"No PreToolUse entry matches required tool set "
                f"{REQUIRED_TOOL_MATCHER!r}."
            ),
        )
    commands = []
    inner = target.get("hooks")
    if isinstance(inner, Sequence) and not isinstance(inner, (str, bytes)):
        for hook in inner:
            if isinstance(hook, Mapping):
                cmd = coerce_string(hook.get("command")).strip()
                if cmd:
                    commands.append(cmd)
    if not commands:
        return ProviderHookState(
            provider="claude",
            state=HOOK_STATE_MISSING,
            source=source,
            detail="PreToolUse entry has no command.",
        )
    missing_pieces: list[str] = []
    if not any(REQUIRED_GUARD_SCRIPT in cmd for cmd in commands):
        missing_pieces.append(REQUIRED_GUARD_SCRIPT)
    if not any(REQUIRED_MODE_FLAG in cmd for cmd in commands):
        missing_pieces.append(REQUIRED_MODE_FLAG)
    if not any(REQUIRED_STDIN_FLAG in cmd for cmd in commands):
        missing_pieces.append(REQUIRED_STDIN_FLAG)
    if missing_pieces:
        return ProviderHookState(
            provider="claude",
            state=HOOK_STATE_CONFIGURED,
            source=source,
            detail=(
                "PreToolUse command is present but missing required pieces: "
                f"{', '.join(missing_pieces)}."
            ),
        )
    return ProviderHookState(
        provider="claude",
        state=HOOK_STATE_CONFIGURED,
        source=source,
        detail=(
            "PreToolUse Edit|Write|MultiEdit invokes "
            "check_role_lane_mutation_authority with --mode pre_mutation and "
            "--tool-input-stdin. No execution receipt observed yet."
        ),
    )


def _classify_codex_hooks(
    hooks_doc: Mapping[str, object],
    *,
    source: str,
) -> ProviderHookState:
    """Classify Codex provider hook coverage from a ``.codex/hooks.json`` doc.

    Mirrors ``_classify_claude_settings`` structure since codex hooks share
    the ``hooks.PreToolUse[].matcher + hooks[].command`` shape per its
    documented hooks=stable feature.
    """
    hooks = _mapping(hooks_doc.get("hooks"))
    pre_tool = hooks.get("PreToolUse")
    if not isinstance(pre_tool, Sequence) or isinstance(pre_tool, (str, bytes)):
        return ProviderHookState(
            provider="codex",
            state=HOOK_STATE_MISSING,
            source=source,
            detail="No PreToolUse hooks declared in Codex hooks file.",
        )
    target = None
    for entry in pre_tool:
        if not isinstance(entry, Mapping):
            continue
        matcher = coerce_string(entry.get("matcher")).strip().lower()
        # Codex matchers are typically lowercase ("edit|write|multiedit"),
        # Claude uses CamelCase ("Edit|Write|MultiEdit"). Accept either by
        # normalizing to lowercase before comparison.
        if matcher == REQUIRED_TOOL_MATCHER.lower():
            target = entry
            break
    if target is None:
        return ProviderHookState(
            provider="codex",
            state=HOOK_STATE_MISSING,
            source=source,
            detail=(
                f"No PreToolUse entry matches required tool set "
                f"{REQUIRED_TOOL_MATCHER.lower()!r}."
            ),
        )
    commands = []
    inner = target.get("hooks")
    if isinstance(inner, Sequence) and not isinstance(inner, (str, bytes)):
        for hook in inner:
            if isinstance(hook, Mapping):
                cmd = coerce_string(hook.get("command")).strip()
                if cmd:
                    commands.append(cmd)
    if not commands:
        return ProviderHookState(
            provider="codex",
            state=HOOK_STATE_MISSING,
            source=source,
            detail="PreToolUse entry has no command.",
        )
    missing_pieces: list[str] = []
    if not any(REQUIRED_GUARD_SCRIPT in cmd for cmd in commands):
        missing_pieces.append(REQUIRED_GUARD_SCRIPT)
    if not any(REQUIRED_MODE_FLAG in cmd for cmd in commands):
        missing_pieces.append(REQUIRED_MODE_FLAG)
    if not any(REQUIRED_STDIN_FLAG in cmd for cmd in commands):
        missing_pieces.append(REQUIRED_STDIN_FLAG)
    if missing_pieces:
        return ProviderHookState(
            provider="codex",
            state=HOOK_STATE_CONFIGURED,
            source=source,
            detail=(
                "PreToolUse command is present but missing required pieces: "
                f"{', '.join(missing_pieces)}."
            ),
        )
    return ProviderHookState(
        provider="codex",
        state=HOOK_STATE_CONFIGURED,
        source=source,
        detail=(
            "PreToolUse edit|write|multiedit invokes "
            "check_role_lane_mutation_authority with --mode pre_mutation and "
            "--tool-input-stdin. No execution receipt observed yet."
        ),
    )


def _classify_provider_metadata(
    entry: Mapping[str, object],
    *,
    source: str,
) -> ProviderHookState:
    provider = coerce_string(entry.get("provider")).strip()
    state = coerce_string(entry.get("state")).strip().lower()
    detail = coerce_string(entry.get("detail")).strip()
    blocker_ref = coerce_string(entry.get("blocker_ref")).strip()
    if state in {
        HOOK_STATE_TESTED,
        HOOK_STATE_CONFIGURED,
        HOOK_STATE_MISSING,
        HOOK_STATE_UNAVAILABLE_BLOCKER,
    }:
        if state == HOOK_STATE_UNAVAILABLE_BLOCKER and not blocker_ref:
            return ProviderHookState(
                provider=provider,
                state=HOOK_STATE_MISSING,
                source=source,
                detail=(
                    "Provider declared hook_unavailable_blocker without "
                    "blocker_ref; downgrading to hook_missing."
                ),
            )
        return ProviderHookState(
            provider=provider,
            state=state,
            source=source,
            detail=detail,
        )
    return ProviderHookState(
        provider=provider,
        state=HOOK_STATE_MISSING,
        source=source,
        detail=f"Provider metadata declares unknown state {state!r}.",
    )


def _read_provider_metadata(path: Path) -> list[Mapping[str, object]]:
    if not path.exists():
        return []
    entries: list[Mapping[str, object]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                entries.append(payload)
    except OSError:
        return []
    return entries


def _read_declared_providers(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    providers = set()
    if isinstance(payload, Mapping):
        for key in ("providers", "supported_providers", "known_providers"):
            value = payload.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    text = coerce_string(item).strip()
                    if text:
                        providers.add(text)
    return sorted(providers)


def _violations_for_state(state: ProviderHookState) -> list[HookCoverageViolation]:
    if state.state == HOOK_STATE_TESTED:
        return []
    if state.state == HOOK_STATE_UNAVAILABLE_BLOCKER:
        return []
    if state.state == HOOK_STATE_MISSING:
        return [
            HookCoverageViolation(
                reason=PROVIDER_HOOK_MISSING_REASON,
                detail=state.detail or "Provider lacks any pre-tool hook configuration.",
                provider=state.provider,
            )
        ]
    if state.state == HOOK_STATE_CONFIGURED:
        # Distinguish "configured but missing required pieces" from
        # "configured but no execution receipt." Per A16 G19 the former is
        # not_pre_mutation; the latter is unproven.
        if "missing required pieces" in state.detail.lower():
            return [
                HookCoverageViolation(
                    reason=PROVIDER_HOOK_NOT_PRE_MUTATION_REASON,
                    detail=state.detail,
                    provider=state.provider,
                )
            ]
        return [
            HookCoverageViolation(
                reason=PROVIDER_HOOK_UNPROVEN_REASON,
                detail=state.detail or "Configured but no execution receipt found.",
                provider=state.provider,
            )
        ]
    # Unknown state value
    return [
        HookCoverageViolation(
            reason=PROVIDER_HOOK_CLAIM_WITHOUT_TEST_REASON,
            detail=f"Provider declared unrecognized hook state {state.state!r}.",
            provider=state.provider,
        )
    ]


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude-settings", type=Path, default=DEFAULT_CLAUDE_SETTINGS_PATH)
    parser.add_argument(
        "--provider-metadata",
        type=Path,
        default=DEFAULT_PROVIDER_METADATA_PATH,
    )
    parser.add_argument(
        "--launcher-policy",
        type=Path,
        default=DEFAULT_LAUNCHER_POLICY_PATH,
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        report = build_report(
            claude_settings_path=args.claude_settings,
            provider_metadata_path=args.provider_metadata,
            launcher_policy_path=args.launcher_policy,
        )
    except Exception as exc:  # broad-except: guards emit typed error reports
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if bool(report.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
