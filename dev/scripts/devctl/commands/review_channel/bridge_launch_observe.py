"""Post-launch liveness observation for bridge launch."""

from __future__ import annotations

from ...review_channel.handoff import extract_bridge_snapshot, summarize_bridge_liveness
from ...review_channel.launch_truth import build_launch_probe_state, classify_launch_truth
from ...review_channel.session_probe import active_conductor_providers


def observe_launch_state(
    *,
    args,
    context,
    warnings: list[str],
    refresh_snapshot_fn,
    active_conductor_providers_fn=active_conductor_providers,
) -> dict[str, object]:
    """Project the post-launch liveness fields used by launch-time waiting."""
    try:
        snapshot = extract_bridge_snapshot(context.bridge_path.read_text(encoding="utf-8"))
        bridge_liveness = summarize_bridge_liveness(snapshot)
        active_providers = active_conductor_providers_fn(
            session_output_root=context.status_dir,
        )
        codex_active = "codex" in active_providers
        claude_active = "claude" in active_providers
        launch_state = build_launch_probe_state(
            bridge_liveness, active_providers, context.status_dir,
        )
        truth = classify_launch_truth(launch_state).value
        return {
            "launch_truth": truth,
            "codex_conductor_active": codex_active,
            "claude_conductor_active": claude_active,
        }
    except OSError:
        bridge_liveness = refresh_snapshot_fn(
            args=args,
            context=context,
            warnings=warnings,
        ).bridge_liveness
    return {
        "launch_truth": bridge_liveness.get("launch_truth"),
        "codex_conductor_active": bridge_liveness.get("codex_conductor_active"),
        "claude_conductor_active": bridge_liveness.get("claude_conductor_active"),
    }


__all__ = ["observe_launch_state"]
