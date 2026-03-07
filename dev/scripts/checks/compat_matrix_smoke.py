#!/usr/bin/env python3
"""Smoke-check compatibility matrix coverage against runtime enums."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
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
RUNTIME_COMPAT_PATH = REPO_ROOT / "rust/src/bin/voiceterm/runtime_compat.rs"
IPC_PROTOCOL_PATH = REPO_ROOT / "rust/src/ipc/protocol.rs"
BACKEND_REGISTRY_PATH = REPO_ROOT / "rust/src/backend/mod.rs"
EXPECTED_NON_IPC_PROVIDER_MODES = {
    "gemini": "overlay-only-experimental",
    "aider": "overlay-only-non-ipc",
    "opencode": "overlay-only-non-ipc",
    "custom": "overlay-only-non-ipc",
}
EXPECTED_RUNTIME_HOST_IDS = {"cursor", "jetbrains", "other"}
EXPECTED_RUNTIME_PROVIDER_IDS = {"codex", "claude", "gemini"}
EXPECTED_IPC_PROVIDER_IDS = {"codex", "claude"}
EXPECTED_RUNTIME_BACKEND_CORE_IDS = {"codex", "claude", "gemini"}


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _emit_report(report: dict, report_format: str) -> None:
    if report_format == "json":
        print(json.dumps(report, indent=2))
        return
    print(_render_md(report))


def _class_name_to_backend_id(class_name: str) -> str:
    base_name = class_name.removesuffix("Backend")
    snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name).lower()
    return snake_name.replace("_", "")


def _parse_backend_registry_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    backend_classes = re.findall(
        r"\bBox::new\(\s*([A-Za-z_][A-Za-z0-9_]*)::new\s*\(",
        text,
    )
    if not backend_classes:
        backend_classes = re.findall(
            r"\b([A-Za-z_][A-Za-z0-9_]*)Backend::new\s*\(",
            text,
        )
    return sorted({_class_name_to_backend_id(name) for name in backend_classes})


def _parse_enum_variants(path: Path, enum_name: str) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf"enum\s+{enum_name}\s*\{{(.*?)\}}", text, re.S)
    if not match:
        return []
    body = match.group(1)
    variants: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.split("//", 1)[0].strip()
        if not line or line.startswith("#["):
            continue
        line = line.rstrip(",")
        name_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", line)
        if name_match:
            variants.append(name_match.group(1))
    return variants


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


def _render_md(report: dict) -> str:
    lines = ["# compat_matrix_smoke", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- matrix_path: {report.get('matrix_path')}")
    lines.append(f"- runtime_hosts: {', '.join(report.get('runtime_hosts', []))}")
    lines.append(
        f"- runtime_providers: {', '.join(report.get('runtime_providers', []))}"
    )
    lines.append("- runtime_backends: " + ", ".join(report.get("runtime_backends", [])))
    lines.append(f"- ipc_providers: {', '.join(report.get('ipc_providers', []))}")
    lines.append(
        f"- missing_runtime_cells: {len(report.get('missing_runtime_cells', []))}"
    )
    lines.append(
        f"- missing_runtime_backends: {len(report.get('missing_runtime_backends', []))}"
    )
    lines.append(
        f"- runtime_non_ipc_provider_labels: {len(report.get('runtime_non_ipc_provider_labels', []))}"
    )
    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for item in report.get("errors", []):
            lines.append(f"- {item}")
    if report.get("warnings"):
        lines.append("")
        lines.append("## Warnings")
        for item in report.get("warnings", []):
            lines.append(f"- {item}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def _coerce_list_field(payload: dict, field_name: str, errors: list[str]) -> list:
    value = payload.get(field_name, [])
    if isinstance(value, list):
        return value
    errors.append(f"`{field_name}` must be a list")
    return []


def _extract_ids(items: list[object]) -> set[str]:
    return {
        item["id"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _extract_provider_modes(items: list[object]) -> dict[str, object]:
    return {
        item["id"]: item.get("ipc_mode")
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _extract_matrix_cells(items: list[object]) -> set[tuple[str, str]]:
    return {
        (item.get("host"), item.get("provider"))
        for item in items
        if isinstance(item, dict)
        and isinstance(item.get("host"), str)
        and isinstance(item.get("provider"), str)
    }


def _collect_runtime_state() -> tuple[list[str], list[str], list[str], list[str]]:
    runtime_hosts = sorted(
        {
            value.lower()
            for value in _parse_enum_variants(RUNTIME_COMPAT_PATH, "TerminalHost")
        }
    )
    runtime_provider_variants = {
        value.lower()
        for value in _parse_enum_variants(RUNTIME_COMPAT_PATH, "BackendFamily")
    }
    # `BackendFamily::Other` is a fallback sentinel, not a matrix provider id.
    runtime_providers = sorted(runtime_provider_variants.difference({"other"}))
    runtime_backends = sorted(
        {
            value.lower()
            for value in _parse_backend_registry_names(BACKEND_REGISTRY_PATH)
        }
    )
    ipc_providers = sorted(
        {value.lower() for value in _parse_enum_variants(IPC_PROTOCOL_PATH, "Provider")}
    )
    return runtime_hosts, runtime_providers, runtime_backends, ipc_providers


def _validate_runtime_discovery_contract(
    *,
    runtime_hosts: list[str],
    runtime_providers: list[str],
    runtime_backends: list[str],
    ipc_providers: list[str],
) -> list[str]:
    errors: list[str] = []

    if not runtime_hosts:
        errors.append(
            "failed to discover runtime host variants from "
            f"{_path_for_report(RUNTIME_COMPAT_PATH)}"
        )
    if not runtime_providers:
        errors.append(
            "failed to discover runtime provider variants from "
            f"{_path_for_report(RUNTIME_COMPAT_PATH)}"
        )
    if not runtime_backends:
        errors.append(
            "failed to discover backend registry entries from "
            f"{_path_for_report(BACKEND_REGISTRY_PATH)}"
        )
    if not ipc_providers:
        errors.append(
            "failed to discover IPC provider variants from "
            f"{_path_for_report(IPC_PROTOCOL_PATH)}"
        )

    missing_hosts = sorted(EXPECTED_RUNTIME_HOST_IDS.difference(runtime_hosts))
    if missing_hosts:
        errors.append(
            "runtime host discovery missing required ids: " + ", ".join(missing_hosts)
        )

    missing_providers = sorted(
        EXPECTED_RUNTIME_PROVIDER_IDS.difference(runtime_providers)
    )
    if missing_providers:
        errors.append(
            "runtime provider discovery missing required ids: "
            + ", ".join(missing_providers)
        )

    missing_ipc_providers = sorted(EXPECTED_IPC_PROVIDER_IDS.difference(ipc_providers))
    if missing_ipc_providers:
        errors.append(
            "ipc provider discovery missing required ids: "
            + ", ".join(missing_ipc_providers)
        )

    missing_core_backends = sorted(
        EXPECTED_RUNTIME_BACKEND_CORE_IDS.difference(runtime_backends)
    )
    if missing_core_backends:
        errors.append(
            "backend discovery missing required core backend ids: "
            + ", ".join(missing_core_backends)
        )

    return errors


def _validate_non_ipc_mode_policy(
    *,
    runtime_backends: list[str],
    ipc_providers: list[str],
    provider_modes: dict[str, object],
    errors: list[str],
    warnings: list[str],
) -> list[str]:
    runtime_non_ipc_provider_labels = sorted(
        set(runtime_backends).difference(ipc_providers)
    )
    ipc_provider_set = set(ipc_providers)
    for provider in runtime_non_ipc_provider_labels:
        mode = provider_modes.get(provider)
        expected_mode = EXPECTED_NON_IPC_PROVIDER_MODES.get(provider)
        if expected_mode is None:
            if mode not in {"overlay-only-experimental", "overlay-only-non-ipc"}:
                errors.append(
                    f"provider `{provider}` is runtime-visible but lacks explicit non-IPC matrix mode"
                )
            else:
                warnings.append(
                    f"provider `{provider}` is runtime-visible but uses untracked non-IPC mode (`{mode}`)"
                )
            continue
        if provider in ipc_provider_set:
            errors.append(
                f"provider `{provider}` is marked non-IPC in matrix policy but still appears in IPC provider enum"
            )
            continue
        if mode != expected_mode:
            errors.append(
                f"provider `{provider}` must declare ipc_mode `{expected_mode}` (found: `{mode}`)"
            )
        else:
            warnings.append(
                f"provider `{provider}` is runtime-visible but non-IPC by policy (`{mode}`)"
            )
    return runtime_non_ipc_provider_labels


def main() -> int:
    args = _build_parser().parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    matrix, load_error = _load_matrix(MATRIX_PATH)
    if load_error is not None:
        report = {
            "command": "compat_matrix_smoke",
            "timestamp": datetime.now().isoformat(),
            "ok": False,
            "matrix_path": _path_for_report(MATRIX_PATH),
            "errors": [load_error],
        }
        _emit_report(report, args.format)
        return 1

    hosts = _coerce_list_field(matrix, "hosts", errors)
    providers = _coerce_list_field(matrix, "providers", errors)
    matrix_rows = _coerce_list_field(matrix, "matrix", errors)

    host_ids = _extract_ids(hosts)
    provider_ids = _extract_ids(providers)
    provider_modes = _extract_provider_modes(providers)
    matrix_cells = _extract_matrix_cells(matrix_rows)

    runtime_hosts, runtime_providers, runtime_backends, ipc_providers = (
        _collect_runtime_state()
    )
    errors.extend(
        _validate_runtime_discovery_contract(
            runtime_hosts=runtime_hosts,
            runtime_providers=runtime_providers,
            runtime_backends=runtime_backends,
            ipc_providers=ipc_providers,
        )
    )

    missing_runtime_hosts = sorted(set(runtime_hosts).difference(host_ids))
    if missing_runtime_hosts:
        errors.append(
            "matrix missing runtime host ids: " + ", ".join(missing_runtime_hosts)
        )

    missing_runtime_providers = sorted(set(runtime_providers).difference(provider_ids))
    if missing_runtime_providers:
        errors.append(
            "matrix missing runtime provider ids: "
            + ", ".join(missing_runtime_providers)
        )

    missing_runtime_backends = sorted(set(runtime_backends).difference(provider_ids))
    if missing_runtime_backends:
        errors.append(
            "matrix missing runtime backend ids: " + ", ".join(missing_runtime_backends)
        )

    missing_runtime_cells = sorted(
        f"{host}::{provider}"
        for host in runtime_hosts
        for provider in runtime_backends
        if (host, provider) not in matrix_cells
    )
    if missing_runtime_cells:
        errors.append(
            "matrix missing runtime host/provider cells (sample): "
            + ", ".join(missing_runtime_cells[:10])
        )

    runtime_non_ipc_provider_labels = _validate_non_ipc_mode_policy(
        runtime_backends=runtime_backends,
        ipc_providers=ipc_providers,
        provider_modes=provider_modes,
        errors=errors,
        warnings=warnings,
    )

    report = {
        "command": "compat_matrix_smoke",
        "timestamp": datetime.now().isoformat(),
        "ok": not errors,
        "matrix_path": _path_for_report(MATRIX_PATH),
        "runtime_hosts": runtime_hosts,
        "runtime_providers": runtime_providers,
        "runtime_backends": runtime_backends,
        "ipc_providers": ipc_providers,
        "missing_runtime_cells": missing_runtime_cells,
        "missing_runtime_backends": missing_runtime_backends,
        "runtime_non_ipc_provider_labels": runtime_non_ipc_provider_labels,
        "warnings": warnings,
        "errors": errors,
    }

    _emit_report(report, args.format)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
