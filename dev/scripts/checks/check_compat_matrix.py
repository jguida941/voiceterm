#!/usr/bin/env python3
"""Validate IDE/provider compatibility matrix metadata."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - guarded fallback for minimal envs
    yaml = None

try:
    from .yaml_json_loader import load_yaml_or_json
except ImportError:  # pragma: no cover
    from yaml_json_loader import load_yaml_or_json

REPO_ROOT = Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO_ROOT / "dev/config/compat/ide_provider_matrix.yaml"
REQUIRED_HOSTS = {"cursor", "jetbrains", "other"}
REQUIRED_PROVIDERS = {"codex", "claude", "gemini", "aider", "opencode", "custom"}
REQUIRED_IPC_PROVIDERS = {"codex", "claude"}
REQUIRED_OVERLAY_EXPERIMENTAL_PROVIDERS = {"gemini"}
REQUIRED_OVERLAY_NON_IPC_PROVIDERS = {"aider", "opencode", "custom"}
ALLOWED_COMPAT = {
    "supported",
    "stabilizing",
    "experimental",
    "decision-pending",
    "unsupported",
}
ALLOWED_PROVIDER_IPC_MODES = {
    "ipc",
    "overlay-only-experimental",
    "overlay-only-non-ipc",
    "non-ipc-experimental",
}


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_matrix(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"missing matrix file: {_path_for_report(path)}"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"failed to parse matrix file: {exc}"
    try:
        payload = load_yaml_or_json(raw, yaml_module=yaml)
    except Exception as exc:
        return None, f"failed to parse matrix file: {exc}"
    if not isinstance(payload, dict):
        return None, "matrix root must be an object"
    return payload, None


def _emit_report(report: dict, report_format: str) -> None:
    if report_format == "json":
        print(json.dumps(report, indent=2))
        return
    print(_render_md(report))


def _coerce_list_field(payload: dict, field_name: str, errors: list[str]) -> list:
    value = payload.get(field_name, [])
    if isinstance(value, list):
        return value
    errors.append(f"`{field_name}` must be a list")
    return []


def _extract_string_ids(
    items: list[object], section_name: str, errors: list[str]
) -> list[str]:
    ids: list[str] = []
    invalid_entries = 0
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            invalid_entries += 1
            continue
        ids.append(item["id"])
    if invalid_entries:
        errors.append(
            f"`{section_name}` contains {invalid_entries} entries without a string `id`"
        )
    return ids


def _find_duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _collect_provider_modes(
    providers: list[object],
) -> tuple[dict[str, str], list[str]]:
    provider_mode_by_id: dict[str, str] = {}
    invalid_provider_modes: list[str] = []
    for item in providers:
        if not isinstance(item, dict):
            continue
        provider_id = item.get("id")
        mode = item.get("ipc_mode")
        if not isinstance(provider_id, str):
            continue
        if isinstance(mode, str):
            provider_mode_by_id[provider_id] = mode
        if not isinstance(mode, str) or mode not in ALLOWED_PROVIDER_IPC_MODES:
            invalid_provider_modes.append(provider_id)
    return provider_mode_by_id, invalid_provider_modes


def _validate_provider_mode_policy(
    provider_ids: set[str], provider_mode_by_id: dict[str, str]
) -> list[str]:
    policy_errors: list[str] = []
    for provider in REQUIRED_IPC_PROVIDERS:
        if provider in provider_ids and provider_mode_by_id.get(provider) != "ipc":
            policy_errors.append(f"{provider} must declare ipc_mode=`ipc`")
    for provider in REQUIRED_OVERLAY_EXPERIMENTAL_PROVIDERS:
        if (
            provider in provider_ids
            and provider_mode_by_id.get(provider) != "overlay-only-experimental"
        ):
            policy_errors.append(
                f"{provider} must declare ipc_mode=`overlay-only-experimental`"
            )
    for provider in REQUIRED_OVERLAY_NON_IPC_PROVIDERS:
        if (
            provider in provider_ids
            and provider_mode_by_id.get(provider) != "overlay-only-non-ipc"
        ):
            policy_errors.append(
                f"{provider} must declare ipc_mode=`overlay-only-non-ipc`"
            )
    for provider, mode in provider_mode_by_id.items():
        if provider not in REQUIRED_IPC_PROVIDERS and mode == "ipc":
            policy_errors.append(
                f"{provider} must not declare ipc_mode=`ipc`; classify it as overlay-only non-IPC"
            )
    return policy_errors


def _collect_declared_cells(
    matrix_rows: list[object], host_ids: set[str], provider_ids: set[str]
) -> tuple[dict[tuple[str, str], int], list[str]]:
    declared_cells: dict[tuple[str, str], int] = {}
    invalid_cells: list[str] = []
    for item in matrix_rows:
        if not isinstance(item, dict):
            invalid_cells.append("<non-object>")
            continue
        host = item.get("host")
        provider = item.get("provider")
        compat = item.get("compat")
        if not isinstance(host, str) or not isinstance(provider, str):
            invalid_cells.append(str(item))
            continue
        if host not in host_ids or provider not in provider_ids:
            invalid_cells.append(f"{host}::{provider}")
            continue
        if not isinstance(compat, str) or compat not in ALLOWED_COMPAT:
            invalid_cells.append(f"{host}::{provider}")
            continue
        key = (host, provider)
        declared_cells[key] = declared_cells.get(key, 0) + 1
    return declared_cells, invalid_cells


def _render_md(report: dict) -> str:
    lines = ["# check_compat_matrix", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- matrix_path: {report.get('matrix_path')}")
    lines.append(f"- hosts_declared: {report.get('hosts_declared', 0)}")
    lines.append(f"- providers_declared: {report.get('providers_declared', 0)}")
    lines.append(f"- matrix_cells_declared: {report.get('matrix_cells_declared', 0)}")
    lines.append(f"- matrix_cells_expected: {report.get('matrix_cells_expected', 0)}")
    lines.append(
        f"- missing_required_hosts: {len(report.get('missing_required_hosts', []))}"
    )
    lines.append(
        f"- missing_required_providers: {len(report.get('missing_required_providers', []))}"
    )
    lines.append(f"- duplicate_host_ids: {len(report.get('duplicate_host_ids', []))}")
    lines.append(
        f"- duplicate_provider_ids: {len(report.get('duplicate_provider_ids', []))}"
    )
    lines.append(f"- missing_cells: {len(report.get('missing_cells', []))}")
    lines.append(f"- duplicate_cells: {len(report.get('duplicate_cells', []))}")
    lines.append(f"- invalid_cells: {len(report.get('invalid_cells', []))}")
    lines.append(
        f"- invalid_provider_modes: {len(report.get('invalid_provider_modes', []))}"
    )
    lines.append(
        f"- provider_mode_policy_errors: {len(report.get('provider_mode_policy_errors', []))}"
    )
    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for item in report.get("errors", []):
            lines.append(f"- {item}")
    if report.get("provider_mode_policy_errors"):
        lines.append("")
        lines.append("## Provider Mode Policy Errors")
        for item in report.get("provider_mode_policy_errors", []):
            lines.append(f"- {item}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    payload, load_error = _load_matrix(MATRIX_PATH)
    if load_error is not None:
        report = {
            "command": "check_compat_matrix",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "ok": False,
            "matrix_path": _path_for_report(MATRIX_PATH),
            "errors": [load_error],
        }
        _emit_report(report, args.format)
        return 1

    errors: list[str] = []
    hosts = _coerce_list_field(payload, "hosts", errors)
    providers = _coerce_list_field(payload, "providers", errors)
    matrix_rows = _coerce_list_field(payload, "matrix", errors)

    host_id_values = _extract_string_ids(hosts, "hosts", errors)
    provider_id_values = _extract_string_ids(providers, "providers", errors)
    duplicate_host_ids = _find_duplicate_values(host_id_values)
    duplicate_provider_ids = _find_duplicate_values(provider_id_values)
    if duplicate_host_ids:
        errors.append("duplicate host ids: " + ", ".join(duplicate_host_ids))
    if duplicate_provider_ids:
        errors.append("duplicate provider ids: " + ", ".join(duplicate_provider_ids))

    host_ids = set(host_id_values)
    provider_ids = set(provider_id_values)
    missing_required_hosts = sorted(REQUIRED_HOSTS.difference(host_ids))
    missing_required_providers = sorted(REQUIRED_PROVIDERS.difference(provider_ids))

    provider_mode_by_id, invalid_provider_modes = _collect_provider_modes(providers)
    provider_mode_policy_errors = _validate_provider_mode_policy(
        provider_ids, provider_mode_by_id
    )

    declared_cells, invalid_cells = _collect_declared_cells(
        matrix_rows, host_ids, provider_ids
    )

    duplicate_cells = sorted(
        f"{host}::{provider}"
        for (host, provider), count in declared_cells.items()
        if count > 1
    )
    expected_cells = {
        (host, provider) for host in host_ids for provider in provider_ids
    }
    missing_cells = sorted(
        f"{host}::{provider}"
        for (host, provider) in expected_cells.difference(declared_cells)
    )

    report = {
        "command": "check_compat_matrix",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not (
            errors
            or missing_required_hosts
            or missing_required_providers
            or missing_cells
            or duplicate_cells
            or invalid_cells
            or invalid_provider_modes
            or provider_mode_policy_errors
        ),
        "matrix_path": _path_for_report(MATRIX_PATH),
        "hosts_declared": len(host_ids),
        "providers_declared": len(provider_ids),
        "matrix_cells_declared": len(declared_cells),
        "matrix_cells_expected": len(expected_cells),
        "missing_required_hosts": missing_required_hosts,
        "missing_required_providers": missing_required_providers,
        "duplicate_host_ids": duplicate_host_ids,
        "duplicate_provider_ids": duplicate_provider_ids,
        "missing_cells": missing_cells,
        "duplicate_cells": duplicate_cells,
        "invalid_cells": sorted(set(invalid_cells)),
        "invalid_provider_modes": sorted(set(invalid_provider_modes)),
        "provider_mode_policy_errors": sorted(set(provider_mode_policy_errors)),
        "errors": errors,
    }

    _emit_report(report, args.format)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
