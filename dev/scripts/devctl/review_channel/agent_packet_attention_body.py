"""Body-open command helpers for packet attention."""

from __future__ import annotations


def packet_body_open_command(
    *,
    packet_id: str,
    actor: str,
    role: str = "",
    session: str = "",
) -> str:
    command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id} --actor {actor} --terminal none --format md"
    )
    if role:
        command += f" --target-role {role}"
    if session:
        command += f" --target-session-id {session}"
    return command


def packet_semantic_ingestion_command(
    *,
    packet_id: str,
    actor: str,
    role: str = "",
    session: str = "",
) -> str:
    command = (
        "python3 dev/scripts/devctl.py review-channel --action ingest "
        f"--packet-id {packet_id} --actor {actor} --terminal none --format md"
    )
    if role:
        command += f" --target-role {role}"
    if session:
        command += f" --target-session-id {session}"
    return command
