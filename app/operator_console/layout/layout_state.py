"""Layout persistence helpers for Operator Console workspace state."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..state.core.value_coercion import safe_int, safe_text

_DEFAULT_LAYOUT_STATE_REL_PATH = Path(
    "dev/reports/review_channel/operator_console/layout_state.json"
)


@dataclass(frozen=True)
class LayoutStateSnapshot:
    """Serializable layout state used to restore the previous workspace view."""

    layout_mode: str
    workbench_preset: str
    workbench_surface: str | None = None
    monitor_surface: str | None = None
    lane_splitter_sizes: tuple[int, int, int] | None = None
    utility_splitter_sizes: tuple[int, int, int] | None = None


def default_layout_state_path(repo_root: Path) -> Path:
    """Return the default repo-visible layout state file path."""
    return repo_root / _DEFAULT_LAYOUT_STATE_REL_PATH


def load_layout_state(path: Path) -> LayoutStateSnapshot | None:
    """Load persisted layout state from disk, returning ``None`` on failure."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return LayoutStateSnapshot(
        layout_mode=safe_text(payload.get("layout_mode")) or "workbench",
        workbench_preset=safe_text(payload.get("workbench_preset")) or "balanced",
        workbench_surface=safe_text(payload.get("workbench_surface")),
        monitor_surface=safe_text(payload.get("monitor_surface")),
        lane_splitter_sizes=_coerce_splitter_sizes(payload.get("lane_splitter_sizes")),
        utility_splitter_sizes=_coerce_splitter_sizes(
            payload.get("utility_splitter_sizes")
        ),
    )


def save_layout_state(path: Path, snapshot: LayoutStateSnapshot) -> None:
    """Persist layout state to disk as pretty JSON."""
    payload = {
        "layout_mode": snapshot.layout_mode,
        "workbench_preset": snapshot.workbench_preset,
        "workbench_surface": snapshot.workbench_surface,
        "monitor_surface": snapshot.monitor_surface,
        "lane_splitter_sizes": (
            list(snapshot.lane_splitter_sizes)
            if snapshot.lane_splitter_sizes is not None
            else None
        ),
        "utility_splitter_sizes": (
            list(snapshot.utility_splitter_sizes)
            if snapshot.utility_splitter_sizes is not None
            else None
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _coerce_splitter_sizes(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    parsed: list[int] = []
    for item in value:
        size = safe_int(item)
        if size <= 0:
            return None
        parsed.append(size)
    return (parsed[0], parsed[1], parsed[2])
