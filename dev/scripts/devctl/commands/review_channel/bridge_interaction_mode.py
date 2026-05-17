"""Launch interaction-mode resolution for review-channel bridge actions."""

from __future__ import annotations

from pathlib import Path

from ...runtime.governance_scan import scan_repo_governance_safely


def resolve_launch_interaction_mode(
    *,
    repo_root: Path,
    args_fallback: str = "",
) -> str:
    """Delegate to the canonical operator interaction-mode reducer."""
    from ...runtime.operator_context import derive_operator_interaction_mode
    from ...runtime.review_state_locator import load_current_review_state_payload

    governance = scan_repo_governance_safely(repo_root)
    try:
        payload = load_current_review_state_payload(repo_root, governance=governance)
    except Exception:  # broad-except: allow reason=launch-path-state-read fallback=governance-default
        payload = None
    reviewer_mode = ""
    if isinstance(payload, dict):
        bridge = payload.get("bridge")
        if isinstance(bridge, dict):
            reviewer_mode = str(bridge.get("reviewer_mode") or "")
    mode = derive_operator_interaction_mode(
        governance=governance,
        review_state_payload=payload if isinstance(payload, dict) else None,
        receipt=None,
        reviewer_mode=reviewer_mode,
    )
    if mode and mode != "unresolved":
        return mode
    return args_fallback.strip() or ""


def launch_interaction_mode_fallback(args) -> str:
    """Return the CLI fallback interaction mode for bridge launch callers."""
    explicit = str(getattr(args, "operator_interaction_mode", "") or "").strip()
    if explicit:
        return explicit
    if str(getattr(args, "terminal", "") or "") == "terminal-app":
        return "local_terminal"
    return ""


def normalize_visible_terminal_interaction_mode(args, interaction_mode: str) -> str:
    """Treat explicit Terminal.app launch as local when mode is only topology."""
    if str(getattr(args, "terminal", "") or "") != "terminal-app":
        return interaction_mode
    if str(getattr(args, "operator_interaction_mode", "") or "").strip():
        return interaction_mode
    if str(interaction_mode or "").strip() == "dual_agent":
        return "local_terminal"
    return interaction_mode


__all__ = [
    "launch_interaction_mode_fallback",
    "normalize_visible_terminal_interaction_mode",
    "resolve_launch_interaction_mode",
]
