"""Typed ``agent_minds/<provider>_latest.json`` projection writer.

The projection is the cross-mind polling surface: other agents, guards,
and bridge renderers read this file to know what a peer was just
reasoning about, without rescanning the raw JSONL or depending on chat
prose. Writes are atomic (tmp + rename) so readers never observe a
half-serialized slice, and the parent directory is created on demand so
fresh clones and headless environments work without manual setup.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ...repo_packs import active_path_config
from ...runtime.agent_mind_slice import AgentMindSlice


_AGENT_MINDS_SUBDIR = "agent_minds"


def resolve_projection_path(agent_provider: str, *, repo_root: Path) -> Path:
    """Return the absolute projection path for ``agent_provider``.

    Path layout is ``<reports_root>/agent_minds/<provider>_latest.json``,
    where the reports root is resolved through :func:`active_path_config`
    so adopting repos that override it transparently inherit the new
    projection location without edits here.
    """
    provider = agent_provider.strip().lower()
    config = active_path_config()
    reports_root = Path(config.reports_root_rel)
    rel = reports_root / _AGENT_MINDS_SUBDIR / f"{provider}_latest.json"
    if rel.is_absolute():
        return rel
    return repo_root / rel


def write_projection(
    slice_: AgentMindSlice,
    *,
    repo_root: Path,
) -> Path:
    """Atomically persist ``slice_`` to the agent-minds projection file.

    Writes happen via ``.tmp`` + ``os.replace`` so a concurrent reader
    always observes a complete JSON document. The target directory is
    created if it does not already exist, which keeps the first run on a
    fresh clone from needing a separate bootstrap step.
    """
    target = resolve_projection_path(slice_.agent_provider, repo_root=repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(slice_.to_dict(), indent=2, sort_keys=True)
    tmp_path = target.with_suffix(target.suffix + ".tmp")
    tmp_path.write_text(payload + "\n", encoding="utf-8")
    os.replace(tmp_path, target)
    return target


__all__ = [
    "resolve_projection_path",
    "write_projection",
]
