"""Parser registration for ``devctl peer-spawn`` and ``devctl peer-terminate``."""

from __future__ import annotations


def add_peer_spawn_parser(sub) -> None:
    from ..commands.runtime import peer_spawn

    peer_spawn.add_peer_spawn_parser(sub)


def add_peer_terminate_parser(sub) -> None:
    from ..commands.runtime import peer_spawn

    peer_spawn.add_peer_terminate_parser(sub)


__all__ = ["add_peer_spawn_parser", "add_peer_terminate_parser"]
