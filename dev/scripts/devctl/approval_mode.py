"""Shared approval-policy helpers for control-plane and launcher surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

APPROVAL_MODE_CHOICES = ("strict", "balanced", "trusted")
DEFAULT_APPROVAL_MODE = "balanced"
LEGACY_DANGEROUS_APPROVAL_MODE = "trusted"

REQUIRES_CONFIRMATION = [
    "rm / destructive deletes",
    "git push / publish / release",
    "GitHub write operations",
    "device install / signing",
    "networked destructive operations",
]

AUTO_ALLOWED = [
    "repo reads",
    "status/report commands",
    "local non-destructive checks",
    "normal test runs",
    "repo-local file edits",
]


def normalize_approval_mode(
    approval_mode: str | None = None,
    *,
    dangerous: bool = False,
) -> str:
    """Resolve compatibility flags into one explicit approval mode."""
    if dangerous:
        return LEGACY_DANGEROUS_APPROVAL_MODE
    normalized = str(approval_mode or DEFAULT_APPROVAL_MODE).strip().lower()
    if normalized not in APPROVAL_MODE_CHOICES:
        choices = ", ".join(APPROVAL_MODE_CHOICES)
        raise ValueError(f"approval mode must be one of: {choices}")
    return normalized


def provider_args_for_approval_mode(
    *,
    provider: str,
    repo_root: Path,
    approval_mode: str,
) -> list[str]:
    """Return provider CLI args for the requested approval mode."""
    if provider == "codex":
        if approval_mode == "trusted":
            return [
                "-C",
                str(repo_root),
                "--dangerously-bypass-approvals-and-sandbox",
            ]
        return ["-C", str(repo_root), "--full-auto"]
    if provider == "claude":
        if approval_mode == "trusted":
            return ["--dangerously-skip-permissions"]
        return ["--permission-mode", "auto"]
    if provider == "cursor":
        return ["--composer", str(repo_root)]
    raise ValueError(f"Unsupported provider: {provider}")


def build_approval_policy_payload(approval_mode: str) -> dict[str, Any]:
    """Build a user-facing policy payload for phone/PyQt/controller projections."""
    mode = normalize_approval_mode(approval_mode)
    summary = {
        "strict": "Prompt on bounded actions and keep dangerous work explicit.",
        "balanced": "Auto-allow safe local work and escalate dangerous actions.",
        "trusted": "Allow more automation, but still require explicit approval for destructive or publish-class actions.",
    }[mode]
    return {
        "mode": mode,
        "summary": summary,
        "auto_allowed": AUTO_ALLOWED,
        "requires_confirmation": REQUIRES_CONFIRMATION,
    }
