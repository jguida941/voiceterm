"""Parser registration for ``devctl agent-supervise``."""

from __future__ import annotations


def add_agent_supervise_parser(sub) -> None:
    from ..commands.runtime import agent_supervise

    agent_supervise.add_parser(sub)


__all__ = ["add_agent_supervise_parser"]
