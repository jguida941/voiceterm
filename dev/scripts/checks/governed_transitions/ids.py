"""Stable node ids for governed transition graph checks."""

from __future__ import annotations

import re


def transition_node_id(transition_id: str) -> str:
    return f"transition:{_node_token(transition_id)}"


def state_node_id(transition_id: str, role: str, state: str) -> str:
    return f"state:{_node_token(transition_id)}:{role}:{_node_token(state)}"


def graph_path_node_id(transition_id: str, index: int, label: str) -> str:
    return f"graph_path:{_node_token(transition_id)}:{index}:{_node_token(label)}"


def emit_node_id(transition_id: str, emitted: str) -> str:
    return f"emit:{_node_token(transition_id)}:{_node_token(emitted)}"


def _node_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", value.strip())[:160] or "missing"
