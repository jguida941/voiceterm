"""Body-open command helpers for packet attention."""

from __future__ import annotations

import json
import shlex
from collections.abc import Mapping, Sequence


def packet_body_open_command(
    *,
    packet_id: str,
    actor: str,
    role: str = "",
    session: str = "",
    control_decision_input: str = "",
) -> str:
    command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id} --actor {actor} --terminal none --format md"
    )
    if role:
        command += f" --target-role {role}"
    if session:
        command += f" --target-session-id {session}"
    if control_decision_input:
        command += f" --control-decision-input {shlex.quote(control_decision_input)}"
    return command


def packet_semantic_ingestion_command(
    *,
    packet_id: str,
    actor: str,
    role: str = "",
    session: str = "",
    control_decision_input: str = "",
    action_item_rows: Sequence[Mapping[str, object]] = (),
) -> str:
    command = (
        "python3 dev/scripts/devctl.py review-channel --action ingest "
        f"--packet-id {packet_id} --actor {actor} --terminal none --format md"
    )
    if role:
        command += f" --target-role {role}"
    if session:
        command += f" --target-session-id {session}"
    if control_decision_input:
        command += f" --control-decision-input {shlex.quote(control_decision_input)}"
    for row in action_item_rows:
        encoded = json.dumps(dict(row), sort_keys=True, separators=(",", ":"))
        command += f" --semantic-action-item {shlex.quote(encoded)}"
    return command


def packet_absorption_command(
    *,
    packet_id: str,
    actor: str,
    role: str = "",
    session: str = "",
    control_decision_input: str = "",
) -> str:
    command = (
        "python3 dev/scripts/devctl.py review-channel --action absorb "
        f"--packet-id {packet_id} --actor {actor} --terminal none --format md"
    )
    if role:
        command += f" --target-role {role}"
    if session:
        command += f" --target-session-id {session}"
    if control_decision_input:
        command += f" --control-decision-input {shlex.quote(control_decision_input)}"
    return command
