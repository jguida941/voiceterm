"""Bridge-truth drift detection for cached typed review-state payloads."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


def cached_projection_has_bridge_contract_drift(
    *,
    payload: dict[str, object],
    repo_root: Path,
    governance: "ProjectGovernance | None",
) -> bool:
    """Detect when a cached typed payload disagrees with live bridge truth.

    Phase 0 currently allows a pathological state where the cached
    `review_state.json` is newer than `bridge.md` yet has fallen back to
    `tools_only` / `inactive` while the live bridge still reports a
    single-agent reviewer loop. In that case mtime freshness alone is not
    enough; startup/session consumers must force one bridge-backed refresh
    instead of reusing the drifted projection indefinitely.
    """
    if governance is None:
        return False
    bridge_path = _governed_bridge_path(repo_root, governance=governance)
    if bridge_path is None:
        return False
    try:
        from ..review_channel.handoff import extract_bridge_snapshot
        from ..review_channel.state_status_inputs import build_status_bridge_liveness
        from .review_state_parser import review_state_from_payload
    except ImportError:
        return False
    parsed = review_state_from_payload(payload)
    if parsed is None:
        return False
    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    except OSError:
        return False

    bridge_liveness = build_status_bridge_liveness(
        bridge_snapshot=extract_bridge_snapshot(bridge_text),
        repo_root=repo_root,
        bridge_path=bridge_path,
    )

    expected_mode = _bridge_runtime_text(
        bridge_liveness,
        "effective_reviewer_mode",
    ) or _bridge_runtime_text(
        bridge_liveness,
        "reviewer_mode",
    )
    actual_mode = _runtime_text(
        parsed.reviewer_runtime.effective_reviewer_mode
        or parsed.reviewer_runtime.reviewer_mode
    )
    if expected_mode and actual_mode and expected_mode != actual_mode:
        return True

    expected_state = _bridge_runtime_text(bridge_liveness, "overall_state")
    actual_attention = _runtime_text(
        parsed.authority_snapshot.attention_status
        if parsed.authority_snapshot is not None
        else ""
    ) or _runtime_text(parsed.attention.status if parsed.attention is not None else "")
    return expected_state in {"fresh", "single_agent_active"} and actual_attention in {
        "inactive",
        "runtime_missing",
    }


def _governed_bridge_path(
    repo_root: Path,
    *,
    governance: "ProjectGovernance",
) -> Path | None:
    bridge_rel = str(governance.bridge_config.bridge_path or "").strip()
    if not bridge_rel:
        return None
    bridge_path = repo_root / bridge_rel
    if not bridge_path.is_file():
        return None
    return bridge_path


def _bridge_runtime_text(
    bridge_liveness: dict[str, object],
    field_name: str,
) -> str:
    value = bridge_liveness.get(field_name)
    if isinstance(value, Enum):
        return str(value.value).strip()
    if isinstance(value, str):
        return value.strip()
    return ""


def _runtime_text(value: str | Enum | None) -> str:
    if isinstance(value, Enum):
        return str(value.value).strip()
    if isinstance(value, str):
        return value.strip()
    return ""


__all__ = ["cached_projection_has_bridge_contract_drift"]
