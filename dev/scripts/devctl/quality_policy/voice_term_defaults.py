"""VoiceTerm-only quality defaults layered above portable policy."""

from __future__ import annotations

VOICETERM_ONLY_AI_GUARD_IDS = (
    "ide_provider_isolation",
    "compat_matrix",
    "compat_matrix_smoke",
    "naming_consistency",
    "platform_layer_boundaries",
    "python_typed_seams",
    "tandem_consistency",
)

__all__ = ["VOICETERM_ONLY_AI_GUARD_IDS"]
