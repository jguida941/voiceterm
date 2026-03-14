"""devctl platform-contracts command implementation."""

from __future__ import annotations

import json
from dataclasses import asdict

from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from .blueprint import build_platform_blueprint
from .render import render_platform_blueprint_markdown


def run(args) -> int:
    """Render the reusable AI-governance platform contract blueprint."""
    blueprint = build_platform_blueprint()
    payload = asdict(blueprint)
    return emit_machine_artifact_output(
        args,
        command="platform-contracts",
        json_payload=payload,
        human_output=render_platform_blueprint_markdown(blueprint),
        options=ArtifactOutputOptions(
            summary={
                "shared_contract_count": len(payload.get("shared_contracts", [])),
                "layer_count": len(payload.get("layers", [])),
            }
        ),
    )
