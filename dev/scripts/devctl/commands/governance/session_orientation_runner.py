"""Command runner for ``SessionOrientationPacket`` assembly."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from ...common import resolve_repo_python_command
from ...common_io import cmd_str
from ...cli_parser.artifact_suppression import ARTIFACT_WRITES_ENV
from ...time_utils import utc_timestamp
from .session_orientation_models import (
    DEFAULT_TIMEOUT_SECONDS,
    OrientationStepSpec,
    SessionOrientationPacket,
    SessionOrientationStep,
)
from .session_orientation_summary import (
    context_graph_summary,
    final_summary,
    first_text,
    review_status_summary,
    session_resume_summary,
    startup_summary,
)


def build_session_orientation(
    args: Any,
    repo_root: Path,
    *,
    role: str,
) -> SessionOrientationPacket:
    """Build a typed orientation packet from authoritative child commands."""
    normalized_role = _normalize_role(role)
    payloads: dict[str, dict[str, object]] = {}
    step_results: list[SessionOrientationStep] = []

    for spec in _step_specs(args, normalized_role):
        result, payload = _run_json_step(
            spec,
            repo_root,
            timeout_seconds=_timeout_seconds(args),
        )
        step_results.append(result)
        if payload is not None:
            payloads[spec.name] = payload

    final = final_summary(payloads, steps=step_results, role=normalized_role)
    return SessionOrientationPacket(
        schema_version=1,
        contract_id="SessionOrientationPacket",
        command="session",
        role=normalized_role,
        generated_at_utc=utc_timestamp(),
        branch=first_text(
            payloads,
            ("session_resume", "branch"),
            ("context_graph", "branch"),
        ),
        head_sha=first_text(
            payloads,
            ("session_resume", "head_sha"),
            ("startup", "startup_receipt", "head_commit_sha"),
            ("context_graph", "snapshot", "commit_hash"),
        ),
        steps=tuple(step_results),
        startup=startup_summary(payloads.get("startup", {})),
        session_resume=session_resume_summary(payloads.get("session_resume", {})),
        review_status=review_status_summary(payloads.get("review_status", {})),
        context_graph=context_graph_summary(payloads.get("context_graph", {})),
        final=final,
    )


def _step_specs(args: Any, role: str) -> tuple[OrientationStepSpec, ...]:
    specs = [
        OrientationStepSpec(
            "startup",
            (
                "python3",
                "dev/scripts/devctl.py",
                "startup-context",
                "--role",
                role,
                "--format",
                "json",
            ),
        ),
        OrientationStepSpec("session_resume", _session_resume_command(args, role)),
    ]
    if getattr(args, "include_review_status", "always") != "never":
        specs.append(
            OrientationStepSpec(
                "review_status",
                (
                    "python3",
                    "dev/scripts/devctl.py",
                    "review-channel",
                    "--action",
                    "status",
                    "--terminal",
                    "none",
                    "--format",
                    "json",
                ),
            )
        )
    specs.append(
        OrientationStepSpec(
            "context_graph",
            (
                "python3",
                "dev/scripts/devctl.py",
                "context-graph",
                "--mode",
                "bootstrap",
                "--format",
                "json",
            ),
            suppress_artifact_writes=False,
        )
    )
    return tuple(specs)


def _session_resume_command(args: Any, role: str) -> tuple[str, ...]:
    cmd = [
        "python3",
        "dev/scripts/devctl.py",
        "session-resume",
        "--role",
        role,
        "--format",
        "json",
    ]
    provider = str(getattr(args, "provider", "") or "").strip()
    if provider:
        cmd.extend(["--provider", provider])
    transcript = str(getattr(args, "session_id_or_transcript_path", "") or "").strip()
    if transcript:
        cmd.extend(["--session-id-or-transcript-path", transcript])
    if getattr(args, "write_resume_receipt", False):
        cmd.append("--write-resume-receipt")
    resume_result = str(getattr(args, "resume_result", "") or "").strip()
    if resume_result and resume_result != "loaded":
        cmd.extend(["--resume-result", resume_result])
    authority_result = str(getattr(args, "authority_result", "") or "").strip()
    if authority_result:
        cmd.extend(["--authority-result", authority_result])
    return tuple(cmd)


def _run_json_step(
    spec: OrientationStepSpec,
    repo_root: Path,
    *,
    timeout_seconds: int,
) -> tuple[SessionOrientationStep, dict[str, object] | None]:
    started = time.monotonic()
    output = ""
    exit_code = 1
    error = ""
    try:
        completed = _run_subprocess(
            list(spec.command),
            repo_root,
            timeout_seconds=timeout_seconds,
            suppress_artifact_writes=spec.suppress_artifact_writes,
        )
        output = completed.stdout or ""
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
        error = f"timed out after {timeout_seconds}s"
    except OSError as exc:
        error = str(exc)

    payload: dict[str, object] | None = None
    if output:
        payload, parse_error = _json_object_from_output(output)
        if parse_error and not error:
            error = parse_error
    elif not error:
        error = "no output"
    duration_ms = int((time.monotonic() - started) * 1000)
    step = SessionOrientationStep(
        name=spec.name,
        source_command=cmd_str(spec.command),
        exit_code=exit_code,
        ok=exit_code == 0,
        parsed=payload is not None,
        duration_ms=duration_ms,
        error=error,
    )
    return step, payload


def _run_subprocess(
    cmd: list[str],
    repo_root: Path,
    *,
    timeout_seconds: int,
    suppress_artifact_writes: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if suppress_artifact_writes:
        env[ARTIFACT_WRITES_ENV] = "1"
    return subprocess.run(
        resolve_repo_python_command(cmd, cwd=repo_root),
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        text=True,
        timeout=timeout_seconds,
        env=env,
    )


def _json_object_from_output(output: str) -> tuple[dict[str, object] | None, str]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        start = output.find("{")
        end = output.rfind("}")
        if start < 0 or end <= start:
            return None, "output was not JSON"
        try:
            data = json.loads(output[start : end + 1])
        except json.JSONDecodeError as exc:
            return None, f"invalid JSON: {exc}"
    if not isinstance(data, dict):
        return None, "expected JSON object"
    return data, ""


def _timeout_seconds(args: Any) -> int:
    raw = getattr(args, "timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS
    return max(1, value)


def _normalize_role(role: str) -> str:
    return "observer" if role == "dashboard" else role
