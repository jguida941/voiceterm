#!/usr/bin/env python3
"""Validate host/provider naming consistency across runtime and tooling surfaces."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import naming_consistency_core as _core
except ImportError:  # pragma: no cover
    import naming_consistency_core as _core

_path_for_report = _core._path_for_report
_load_module = _core._load_module
_load_matrix_ids = _core._load_matrix_ids
_parse_enum_ids = _core._parse_enum_ids
_parse_backend_registry_ids = _core._parse_backend_registry_ids
_parse_isolation_provider_tokens = _core._parse_isolation_provider_tokens
_expect_str_set = _core._expect_str_set
_expect_dict_keys = _core._expect_dict_keys
_extract_provider_label_tokens = _core._extract_provider_label_tokens

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
MATRIX_PATH = REPO_ROOT / "dev/config/compat/ide_provider_matrix.yaml"
RUNTIME_COMPAT_PATH = REPO_ROOT / "rust/src/bin/voiceterm/runtime_compat.rs"
BACKEND_REGISTRY_PATH = REPO_ROOT / "rust/src/backend/mod.rs"
IPC_PROTOCOL_PATH = REPO_ROOT / "rust/src/ipc/protocol.rs"
CHECK_COMPAT_MATRIX_PATH = REPO_ROOT / "dev/scripts/checks/check_compat_matrix.py"
COMPAT_MATRIX_SMOKE_PATH = REPO_ROOT / "dev/scripts/checks/compat_matrix_smoke.py"
ISOLATION_CORE_PATH = REPO_ROOT / "dev/scripts/checks/ide_provider_isolation_core.py"


def _collect_runtime_tokens() -> tuple[dict[str, set[str]], list[str]]:
    runtime = {
        "runtime_host_ids": _parse_enum_ids(RUNTIME_COMPAT_PATH, "TerminalHost"),
        "runtime_provider_ids": _parse_enum_ids(RUNTIME_COMPAT_PATH, "BackendFamily")
        - {"other"},
        "runtime_backend_ids": _parse_backend_registry_ids(BACKEND_REGISTRY_PATH),
        "ipc_provider_ids": _parse_enum_ids(IPC_PROTOCOL_PATH, "Provider"),
    }
    errors: list[str] = []
    if not runtime["runtime_host_ids"]:
        errors.append(
            f"no runtime host ids found in {_path_for_report(RUNTIME_COMPAT_PATH)}"
        )
    if not runtime["runtime_provider_ids"]:
        errors.append(
            f"no runtime provider ids found in {_path_for_report(RUNTIME_COMPAT_PATH)}"
        )
    if not runtime["runtime_backend_ids"]:
        errors.append(
            f"no runtime backend ids found in {_path_for_report(BACKEND_REGISTRY_PATH)}"
        )
    if not runtime["ipc_provider_ids"]:
        errors.append(
            f"no IPC provider ids found in {_path_for_report(IPC_PROTOCOL_PATH)}"
        )
    return runtime, errors


def _collect_tooling_tokens() -> tuple[dict[str, set[str]], list[str]]:
    errors: list[str] = []
    compat, compat_error = _load_module(
        CHECK_COMPAT_MATRIX_PATH, "check_naming_consistency_compat_matrix"
    )
    smoke, smoke_error = _load_module(
        COMPAT_MATRIX_SMOKE_PATH, "check_naming_consistency_compat_smoke"
    )
    if compat_error:
        errors.append(compat_error)
    if smoke_error:
        errors.append(smoke_error)

    tooling = {
        "required_host_ids": _expect_str_set(
            getattr(compat, "REQUIRED_HOSTS", None),
            label="REQUIRED_HOSTS",
            source=CHECK_COMPAT_MATRIX_PATH,
            errors=errors,
        ),
        "required_provider_ids": _expect_str_set(
            getattr(compat, "REQUIRED_PROVIDERS", None),
            label="REQUIRED_PROVIDERS",
            source=CHECK_COMPAT_MATRIX_PATH,
            errors=errors,
        ),
        "required_ipc_provider_ids": _expect_str_set(
            getattr(compat, "REQUIRED_IPC_PROVIDERS", None),
            label="REQUIRED_IPC_PROVIDERS",
            source=CHECK_COMPAT_MATRIX_PATH,
            errors=errors,
        ),
        "required_overlay_experimental_provider_ids": _expect_str_set(
            getattr(compat, "REQUIRED_OVERLAY_EXPERIMENTAL_PROVIDERS", None),
            label="REQUIRED_OVERLAY_EXPERIMENTAL_PROVIDERS",
            source=CHECK_COMPAT_MATRIX_PATH,
            errors=errors,
        ),
        "required_overlay_non_ipc_provider_ids": _expect_str_set(
            getattr(compat, "REQUIRED_OVERLAY_NON_IPC_PROVIDERS", None),
            label="REQUIRED_OVERLAY_NON_IPC_PROVIDERS",
            source=CHECK_COMPAT_MATRIX_PATH,
            errors=errors,
        ),
        "expected_non_ipc_mode_provider_ids": _expect_dict_keys(
            getattr(smoke, "EXPECTED_NON_IPC_PROVIDER_MODES", None),
            label="EXPECTED_NON_IPC_PROVIDER_MODES",
            source=COMPAT_MATRIX_SMOKE_PATH,
            errors=errors,
        ),
        "isolation_provider_tokens": _parse_isolation_provider_tokens(
            ISOLATION_CORE_PATH
        ),
    }
    if not tooling["isolation_provider_tokens"]:
        errors.append(
            "failed to parse provider tokens from "
            + _path_for_report(ISOLATION_CORE_PATH)
            + " PROVIDER_LABEL_PATTERN"
        )
    return tooling, errors


def _append_set_diff(
    errors: list[str],
    *,
    label: str,
    left_name: str,
    left: set[str],
    right_name: str,
    right: set[str],
) -> None:
    if left == right:
        return
    missing = sorted(right.difference(left))
    extra = sorted(left.difference(right))
    message = [f"{label}: `{left_name}` != `{right_name}`"]
    if missing:
        message.append(f"missing in {left_name}: {', '.join(missing)}")
    if extra:
        message.append(f"extra in {left_name}: {', '.join(extra)}")
    errors.append(" | ".join(message))


def _evaluate_consistency(
    matrix_host_ids: set[str],
    matrix_provider_ids: set[str],
    runtime: dict[str, set[str]],
    tooling: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    _append_set_diff(
        errors,
        label="host ids",
        left_name="matrix hosts",
        left=matrix_host_ids,
        right_name="runtime host enum",
        right=runtime["runtime_host_ids"],
    )
    _append_set_diff(
        errors,
        label="host ids",
        left_name="matrix hosts",
        left=matrix_host_ids,
        right_name="check_compat_matrix REQUIRED_HOSTS",
        right=tooling["required_host_ids"],
    )
    _append_set_diff(
        errors,
        label="provider ids",
        left_name="matrix providers",
        left=matrix_provider_ids,
        right_name="check_compat_matrix REQUIRED_PROVIDERS",
        right=tooling["required_provider_ids"],
    )
    _append_set_diff(
        errors,
        label="provider ids",
        left_name="matrix providers",
        left=matrix_provider_ids,
        right_name="ide_provider_isolation PROVIDER_LABEL_PATTERN",
        right=tooling["isolation_provider_tokens"],
    )
    _append_set_diff(
        errors,
        label="ipc provider ids",
        left_name="runtime IPC Provider enum",
        left=runtime["ipc_provider_ids"],
        right_name="check_compat_matrix REQUIRED_IPC_PROVIDERS",
        right=tooling["required_ipc_provider_ids"],
    )
    non_ipc_expected = tooling["expected_non_ipc_mode_provider_ids"]
    _append_set_diff(
        errors,
        label="non-IPC provider ids",
        left_name="check_compat_matrix overlay provider sets",
        left=tooling["required_overlay_experimental_provider_ids"].union(
            tooling["required_overlay_non_ipc_provider_ids"]
        ),
        right_name="compat_matrix_smoke EXPECTED_NON_IPC_PROVIDER_MODES",
        right=non_ipc_expected,
    )
    _append_set_diff(
        errors,
        label="non-IPC provider ids",
        left_name="matrix providers minus IPC providers",
        left=matrix_provider_ids.difference(runtime["ipc_provider_ids"]),
        right_name="compat_matrix_smoke EXPECTED_NON_IPC_PROVIDER_MODES",
        right=non_ipc_expected,
    )

    expected_runtime_provider_min = tooling["required_ipc_provider_ids"].union(
        tooling["required_overlay_experimental_provider_ids"]
    )
    missing_runtime_provider_min = sorted(
        expected_runtime_provider_min.difference(runtime["runtime_provider_ids"])
    )
    runtime_provider_extra = sorted(
        runtime["runtime_provider_ids"].difference(matrix_provider_ids)
    )
    if missing_runtime_provider_min:
        errors.append(
            "runtime BackendFamily enum is missing required providers: "
            + ", ".join(missing_runtime_provider_min)
        )
    if runtime_provider_extra:
        errors.append(
            "runtime BackendFamily enum has providers outside matrix set: "
            + ", ".join(runtime_provider_extra)
        )

    backend_ids = runtime["runtime_backend_ids"]
    backend_expected_full = matrix_provider_ids
    backend_expected_without_custom = matrix_provider_ids.difference({"custom"})
    if (
        backend_ids != backend_expected_full
        and backend_ids != backend_expected_without_custom
    ):
        _append_set_diff(
            errors,
            label="provider ids",
            left_name="runtime BackendRegistry",
            left=backend_ids,
            right_name="matrix providers (or matrix minus custom)",
            right=backend_expected_without_custom,
        )
    return errors


def _build_report() -> dict:
    matrix_host_ids, matrix_provider_ids, errors = _load_matrix_ids(MATRIX_PATH)
    runtime, runtime_errors = _collect_runtime_tokens()
    tooling, tooling_errors = _collect_tooling_tokens()
    errors.extend(runtime_errors)
    errors.extend(tooling_errors)
    errors.extend(
        _evaluate_consistency(matrix_host_ids, matrix_provider_ids, runtime, tooling)
    )
    return {
        "command": "check_naming_consistency",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not errors,
        "matrix_path": _path_for_report(MATRIX_PATH),
        "matrix_host_ids": sorted(matrix_host_ids),
        "matrix_provider_ids": sorted(matrix_provider_ids),
        "runtime_host_ids": sorted(runtime["runtime_host_ids"]),
        "runtime_provider_ids": sorted(runtime["runtime_provider_ids"]),
        "runtime_backend_ids": sorted(runtime["runtime_backend_ids"]),
        "ipc_provider_ids": sorted(runtime["ipc_provider_ids"]),
        "isolation_provider_tokens": sorted(tooling["isolation_provider_tokens"]),
        "errors": errors,
    }


def _render_md(report: dict) -> str:
    lines = [
        "# check_naming_consistency",
        "",
        f"- ok: {report['ok']}",
        f"- errors: {len(report['errors'])}",
    ]
    for key in (
        "matrix_host_ids",
        "matrix_provider_ids",
        "runtime_host_ids",
        "runtime_provider_ids",
        "runtime_backend_ids",
        "ipc_provider_ids",
        "isolation_provider_tokens",
    ):
        lines.append(f"- {key}: {', '.join(report[key])}")
    if report["errors"]:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {item}" for item in report["errors"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = _build_report()
    print(json.dumps(report, indent=2) if args.format == "json" else _render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
