"""Config loading and comparison helpers for check_mobile_relay_protocol."""

from __future__ import annotations

from pathlib import Path

_DEFAULT_RUST_TYPES = "rust/src/bin/voiceterm/daemon/types.rs"
_DEFAULT_SWIFT_RELAY = "app/ios/VoiceTermMobile/Sources/VoiceTermMobileCore/MobileRelayModels.swift"
_DEFAULT_SWIFT_DAEMON = "app/ios/VoiceTermMobile/Sources/VoiceTermMobileCore/DaemonWebSocketClient.swift"

RUST_TO_SWIFT_NAME_MAP: dict[str, str] = {}
IGNORED_STRUCTS: set[str] = {"SessionId", "ClientId", "DaemonConfig"}


def load_protocol_boundary(repo_root: Path) -> dict[str, object]:
    """Load protocol_boundary config from repo policy, falling back to defaults."""
    policy_path = repo_root / "dev" / "config" / "devctl_repo_policy.json"
    if policy_path.is_file():
        try:
            import json as _json_policy

            policy = _json_policy.loads(policy_path.read_text(encoding="utf-8"))
            boundary = policy.get("protocol_boundary")
            if isinstance(boundary, dict):
                return boundary
        except (OSError, ValueError):
            pass
    return {}


def resolve_protocol_paths(
    repo_root: Path,
) -> tuple[Path, Path, Path, dict[str, str], set[str]]:
    """Return (rust, swift_relay, swift_daemon, name_map, computed) from config."""
    boundary = load_protocol_boundary(repo_root)
    rust = Path(boundary.get("rust_daemon_types") or _DEFAULT_RUST_TYPES)
    swift_relay = Path(boundary.get("swift_relay_models") or _DEFAULT_SWIFT_RELAY)
    swift_daemon = Path(boundary.get("swift_daemon_models") or _DEFAULT_SWIFT_DAEMON)
    raw_map = boundary.get("name_map") or {}
    computed = set(boundary.get("swift_computed_properties") or [])
    return rust, swift_relay, swift_daemon, raw_map if isinstance(raw_map, dict) else {}, computed


def match_struct_pairs(
    rust_structs: dict[str, dict],
    swift_structs: dict[str, dict],
    *,
    name_map: dict[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Return (rust_name, swift_name) pairs for structs present on both sides."""
    effective_map = {**RUST_TO_SWIFT_NAME_MAP, **(name_map or {})}
    pairs: list[tuple[str, str]] = []
    for rust_name in sorted(rust_structs):
        if rust_name in IGNORED_STRUCTS:
            continue
        mapped_name = effective_map.get(rust_name)
        if mapped_name and mapped_name in swift_structs:
            pairs.append((rust_name, mapped_name))
        elif rust_name in swift_structs:
            pairs.append((rust_name, rust_name))
    return pairs


def compare_fields(
    rust_fields: dict[str, str],
    swift_fields: dict[str, str],
    *,
    computed_properties: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Compare wire-name sets. Returns (rust_only, swift_only)."""
    exclude = computed_properties or set()
    rust_wires = set(rust_fields.keys())
    swift_wires = set(swift_fields.keys()) - exclude
    return sorted(rust_wires - swift_wires), sorted(swift_wires - rust_wires)
