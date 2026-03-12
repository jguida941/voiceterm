"""Policy-file loading and inheritance helpers for quality-policy resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .common import read_json_object, resolve_repo_path
from .config import REPO_ROOT

DEFAULT_POLICY_RELATIVE_PATH = "dev/config/devctl_repo_policy.json"
DEFAULT_POLICY_PATH = REPO_ROOT / DEFAULT_POLICY_RELATIVE_PATH
QUALITY_POLICY_ENV_VAR = "DEVCTL_QUALITY_POLICY"


def resolve_policy_path(
    *,
    repo_root: Path,
    policy_path: str | Path | None,
    default_policy_path: Path,
) -> Path:
    """Resolve the active policy path, honoring the environment override."""
    selected_policy_path = policy_path
    if selected_policy_path is None or not str(selected_policy_path).strip():
        env_path = os.getenv(QUALITY_POLICY_ENV_VAR, "").strip()
        selected_policy_path = env_path or None
    return resolve_repo_path(
        selected_policy_path,
        default=default_policy_path,
        repo_root=repo_root,
    )


def _merge_policy_payloads(
    base_payload: dict[str, Any],
    override_payload: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base_payload)
    for key, value in override_payload.items():
        if key == "extends":
            continue
        if key in {"enabled_ai_guard_ids", "enabled_review_probe_ids"}:
            merged_ids: list[str] = []
            for raw_ids in (merged.get(key), value):
                if not isinstance(raw_ids, list):
                    continue
                for raw_id in raw_ids:
                    script_id = str(raw_id).strip()
                    if script_id and script_id not in merged_ids:
                        merged_ids.append(script_id)
            merged[key] = merged_ids
            continue
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _merge_policy_payloads(existing, value)
            continue
        merged[key] = value
    return merged


def load_policy_payload(
    policy_path: Path,
    *,
    warnings: list[str],
    active_paths: set[Path],
) -> dict[str, Any] | None:
    """Load one policy file plus any inherited parents."""
    resolved_path = policy_path.resolve(strict=False)
    if resolved_path in active_paths:
        warnings.append(f"quality policy cycle detected at {policy_path}")
        return None
    active_paths.add(resolved_path)
    try:
        payload, error = read_json_object(policy_path)
        if error:
            warnings.append(f"quality policy unavailable ({error})")
            return None

        merged_payload: dict[str, Any] = {}
        raw_extends = payload.get("extends")
        if isinstance(raw_extends, str) and raw_extends.strip():
            extends_paths = (raw_extends.strip(),)
        elif isinstance(raw_extends, list):
            extends_paths = tuple(str(item).strip() for item in raw_extends if str(item).strip())
        else:
            extends_paths = ()

        for extended_path in extends_paths:
            parent_policy_path = Path(extended_path).expanduser()
            if not parent_policy_path.is_absolute():
                parent_policy_path = policy_path.parent / parent_policy_path
            parent_payload = load_policy_payload(
                parent_policy_path,
                warnings=warnings,
                active_paths=active_paths,
            )
            if parent_payload is not None:
                merged_payload = _merge_policy_payloads(
                    merged_payload,
                    parent_payload,
                )
        return _merge_policy_payloads(merged_payload, payload)
    finally:
        active_paths.discard(resolved_path)
