"""Shared fix-policy helpers for bounded remediation loops."""

from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
from typing import Any

POLICY_RELATIVE_PATH = "dev/config/control_plane_policy.json"


def load_policy(repo_root: Path) -> dict[str, Any]:
    policy_path = repo_root / POLICY_RELATIVE_PATH
    if not policy_path.exists():
        return {}
    try:
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _parse_prefix_env(raw: str | None) -> list[list[str]]:
    value = str(raw or "").strip()
    if not value:
        return []
    prefixes: list[list[str]] = []
    for chunk in value.split(";"):
        tokens = shlex.split(chunk.strip(), posix=True)
        if tokens:
            prefixes.append(tokens)
    return prefixes


def _coerce_prefixes(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    prefixes: list[list[str]] = []
    for row in value:
        if isinstance(row, list):
            tokens = [str(token).strip() for token in row if str(token).strip()]
            if tokens:
                prefixes.append(tokens)
    return prefixes


def _command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def _matches_prefix(tokens: list[str], prefixes: list[list[str]]) -> bool:
    if not tokens:
        return False
    for prefix in prefixes:
        if len(prefix) > len(tokens):
            continue
        if tokens[: len(prefix)] == prefix:
            return True
    return False


def _branch_allowed(branch: str, policy: dict[str, Any], policy_key: str) -> bool:
    loop_cfg = policy.get(policy_key, {})
    if not isinstance(loop_cfg, dict):
        return branch == "develop"
    allowed = loop_cfg.get("allowed_branches")
    if not isinstance(allowed, list):
        return branch == "develop"
    normalized = {str(item).strip() for item in allowed if str(item).strip()}
    if not normalized:
        return branch == "develop"
    return branch in normalized


def evaluate_fix_policy(
    *,
    mode: str,
    branch: str,
    fix_command: str | None,
    policy: dict[str, Any],
    policy_key: str,
    env_prefixes_key: str,
    loop_label: str,
) -> str | None:
    if mode == "report-only" or not fix_command:
        return None

    default_autonomy_mode = str(policy.get("autonomy_mode_default") or "read-only")
    autonomy_mode = str(os.getenv("AUTONOMY_MODE") or default_autonomy_mode).strip()
    if autonomy_mode != "operate":
        return (
            f"AUTONOMY_MODE={autonomy_mode} blocks "
            f"{loop_label} fix execution (requires operate)"
        )

    if not _branch_allowed(branch, policy, policy_key):
        return f"branch {branch} is not allowlisted for {loop_label} fix execution"

    loop_cfg = policy.get(policy_key, {})
    configured_prefixes: list[list[str]] = []
    if isinstance(loop_cfg, dict):
        configured_prefixes = _coerce_prefixes(loop_cfg.get("allowed_fix_command_prefixes"))
    env_prefixes = _parse_prefix_env(os.getenv(env_prefixes_key))
    allowed_prefixes = env_prefixes or configured_prefixes
    if not allowed_prefixes:
        return f"no allowed {loop_label} fix command prefixes configured"

    tokens = _command_tokens(fix_command)
    if not tokens:
        return "invalid --fix-command tokenization"
    if not _matches_prefix(tokens, allowed_prefixes):
        return "fix command blocked by allowlist policy"
    return None
