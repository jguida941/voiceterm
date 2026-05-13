"""Shared approval-policy helpers for control-plane and launcher surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .runtime.lifetime_bypass_mode import BypassLifecycle

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


class BypassLifecycleRequired(ValueError):
    """Raised when no-prompt provider mode lacks typed bypass authority."""


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


def auto_elevated_approval_mode(
    *,
    explicit_mode: str | None,
    interaction_mode: str,
) -> str | None:
    """Return the approval-mode after typed-state-driven auto-elevation.

    When `explicit_mode` is None and the typed launcher state indicates a
    headless `interaction_mode == "remote_control"` (which cannot render
    local sandbox-escalation prompts), upgrade to `trusted` so the codex
    binary does not silently deadlock on permission requests. All other
    cases fall through to the explicit mode (or None for downstream
    callers to normalize via DEFAULT_APPROVAL_MODE).

    Empirical motivation: `rev_pkt_1510` + `rev_pkt_1512` reproduced the
    deadlock under `--approval-mode balanced --terminal none`; switching
    to `--approval-mode trusted` cleared it. Codex `rev_pkt_1521` flagged
    that this elevation must fire under the real argparse parser (default
    `None`, not `balanced`), and `rev_pkt_1522` flagged that the recover
    path also needs the elevation, so the helper is shared across all
    launcher entry points.
    """
    if explicit_mode is not None:
        return explicit_mode
    if interaction_mode == "remote_control":
        return "trusted"
    return None


def provider_args_for_approval_mode(
    *,
    provider: str,
    repo_root: Path,
    approval_mode: str,
    bypass_lifecycle: "BypassLifecycle | None" = None,
) -> list[str]:
    """Return provider CLI args for the requested approval mode."""
    if provider == "codex":
        if approval_mode == "trusted":
            _require_active_bypass_lifecycle(bypass_lifecycle)
            return [
                "-C",
                str(repo_root),
                "--dangerously-bypass-approvals-and-sandbox",
            ]
        approval_policy = "untrusted" if approval_mode == "strict" else "on-request"
        return [
            "-C",
            str(repo_root),
            "--ask-for-approval",
            approval_policy,
            "--sandbox",
            "workspace-write",
        ]
    if provider == "claude":
        if approval_mode == "trusted":
            _require_active_bypass_lifecycle(bypass_lifecycle)
            return ["--dangerously-skip-permissions"]
        # Claude's `auto` mode is subscription-gated. Review-channel launches
        # must stay portable across operator plans, so non-trusted sessions use
        # the provider-default permission posture instead of failing during
        # terminal bootstrap on plans without auto mode.
        return ["--permission-mode", "default"]
    if provider == "cursor":
        return ["--composer", str(repo_root)]
    raise ValueError(f"Unsupported provider: {provider}")


def _require_active_bypass_lifecycle(
    bypass_lifecycle: "BypassLifecycle | None",
) -> None:
    from .runtime.lifetime_bypass_mode import (
        BypassAuthorityScope,
        BypassLifecycleState,
        bypass_receipt_active,
        bypass_receipt_grants_scope,
    )
    from .runtime.receipt_state_gate import require_receipt_state

    def grants_edit_scope(lifecycle: "BypassLifecycle") -> bool:
        if lifecycle.receipt is None:
            return False
        return bypass_receipt_active(lifecycle.receipt) and bypass_receipt_grants_scope(
            lifecycle.receipt,
            BypassAuthorityScope.EDIT_ONLY,
        )

    require_receipt_state(
        bypass_lifecycle,
        state_getter=lambda lifecycle: lifecycle.state,
        required_state=BypassLifecycleState.ACTIVE,
        is_usable=grants_edit_scope,
        error_factory=lambda: BypassLifecycleRequired(
            "trusted approval mode requires an active BypassLifecycle receipt "
            "with edit_only authority"
        ),
    )


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
