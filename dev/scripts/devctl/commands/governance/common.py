"""Shared machine/human output helpers for governance commands."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Any

from ...runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output


def emit_governance_command_output(
    args,
    *,
    command: str,
    json_payload: Mapping[str, Any],
    markdown_output: str,
    ok: bool = True,
    summary: Mapping[str, Any] | None = None,
) -> int:
    """Emit canonical JSON for automation or markdown for humans."""
    return emit_machine_artifact_output(
        args,
        command=command,
        json_payload=json_payload,
        human_output=markdown_output,
        options=ArtifactOutputOptions(ok=ok, summary=summary),
    )


def render_governance_value_error(exc: ValueError) -> int:
    """Return the standard CLI exit code for invalid command input."""
    print(f"error: {exc}", file=sys.stderr)
    return 2
