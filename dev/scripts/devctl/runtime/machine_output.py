"""Helpers for machine-friendly output artifacts and telemetry receipts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Any, TypedDict

from ..common_io import display_path, emit_output, pipe_output, write_output


_last_metrics: list[dict[str, Any] | None] = [None]


def clear_machine_output_metrics() -> None:
    """Reset the in-process machine-output telemetry state."""
    _last_metrics[0] = None


def consume_machine_output_metrics() -> dict[str, Any] | None:
    """Return and clear the latest machine-output telemetry payload."""
    result = _last_metrics[0]
    _last_metrics[0] = None
    return dict(result) if isinstance(result, dict) else None


def _record_machine_output_metrics(payload: dict[str, Any]) -> None:
    _last_metrics[0] = dict(payload)


def _compact_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _estimate_tokens(byte_count: int) -> int:
    if byte_count <= 0:
        return 0
    return ceil(byte_count / 4)


class ArtifactMetrics(TypedDict, total=False):
    """Typed artifact telemetry payload."""

    command: str
    delivery: str
    format: str
    path: str | None
    size_bytes: int
    estimated_tokens: int
    token_estimator: str
    sha256: str
    stdout_receipt_size_bytes: int


class ArtifactReceipt(TypedDict, total=False):
    """Typed machine-output receipt."""

    command: str
    ok: bool
    artifact: dict[str, Any]
    summary: dict[str, Any]


@dataclass(frozen=True)
class ArtifactOutputOptions:
    """Optional delivery controls for artifact-emitting commands."""

    ok: bool = True
    summary: Mapping[str, Any] | None = None
    json_output_path: str | None = None


def _build_artifact_metrics(
    *,
    command: str,
    output_path: str | None,
    content: str,
    delivery: str,
    stdout_receipt_size_bytes: int | None = None,
) -> ArtifactMetrics:
    encoded = content.encode("utf-8")
    size_bytes = len(encoded)
    result = ArtifactMetrics(
        command=command,
        delivery=delivery,
        format="json",
        path=display_path(Path(output_path)) if output_path else None,
        size_bytes=size_bytes,
        estimated_tokens=_estimate_tokens(size_bytes),
        token_estimator="bytes_div_4",
        sha256=hashlib.sha256(encoded).hexdigest(),
    )
    if stdout_receipt_size_bytes is not None:
        result["stdout_receipt_size_bytes"] = stdout_receipt_size_bytes
    return result


def _build_receipt(
    *,
    command: str,
    ok: bool,
    artifact_metrics: Mapping[str, Any],
    summary: Mapping[str, Any] | None,
) -> ArtifactReceipt:
    result = ArtifactReceipt(
        command=command,
        ok=ok,
        artifact=dict(artifact_metrics),
    )
    if summary:
        result["summary"] = dict(summary)
    return result


def _machine_output_path(args, json_output_path: str | None) -> str | None:
    if getattr(args, "format", "") == "json" and getattr(args, "output", None):
        return str(args.output)
    if json_output_path:
        return json_output_path
    return None


def emit_machine_artifact_output(
    args,
    *,
    command: str,
    json_payload: Mapping[str, Any],
    human_output: str,
    options: ArtifactOutputOptions | None = None,
) -> int:
    """Emit compact JSON artifacts plus small machine receipts when applicable."""
    active_options = options or ArtifactOutputOptions()
    payload = dict(json_payload)
    payload.setdefault("command", command)
    json_content = _compact_json(payload)
    extra_json_path = active_options.json_output_path
    if getattr(args, "format", "") == "json" and extra_json_path == getattr(args, "output", None):
        extra_json_path = None
    additional_outputs = [(json_content, extra_json_path)] if extra_json_path else None

    if getattr(args, "format", "") == "json":
        stdout_content = None
        announce_output_path = True
        if getattr(args, "output", None):
            artifact_metrics = _build_artifact_metrics(
                command=command,
                output_path=str(args.output),
                content=json_content,
                delivery="file",
            )
            announce_output_path = False
            stdout_content = _compact_json(
                _build_receipt(
                    command=command,
                    ok=active_options.ok,
                    artifact_metrics=artifact_metrics,
                    summary=active_options.summary,
                )
            )
            _record_machine_output_metrics(
                _build_artifact_metrics(
                    command=command,
                    output_path=str(args.output),
                    content=json_content,
                    delivery="file",
                    stdout_receipt_size_bytes=len(stdout_content.encode("utf-8")),
                )
            )
        else:
            metrics_path = _machine_output_path(args, extra_json_path)
            if metrics_path:
                _record_machine_output_metrics(
                    _build_artifact_metrics(
                        command=command,
                        output_path=metrics_path,
                        content=json_content,
                        delivery="file",
                    )
                )
            else:
                _record_machine_output_metrics(
                    _build_artifact_metrics(
                        command=command,
                        output_path=None,
                        content=json_content,
                        delivery="stdout",
                    )
                )
        pipe_code = emit_output(
            json_content,
            output_path=getattr(args, "output", None),
            pipe_command=getattr(args, "pipe_command", None),
            pipe_args=getattr(args, "pipe_args", None),
            additional_outputs=additional_outputs,
            announce_output_path=announce_output_path,
            stdout_content=stdout_content,
        )
        return 0 if pipe_code == 0 and active_options.ok else pipe_code or 1

    if extra_json_path:
        _record_machine_output_metrics(
            _build_artifact_metrics(
                command=command,
                output_path=extra_json_path,
                content=json_content,
                delivery="file",
            )
        )

    pipe_code = emit_output(
        human_output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        additional_outputs=additional_outputs,
    )
    return 0 if pipe_code == 0 and active_options.ok else pipe_code or 1
