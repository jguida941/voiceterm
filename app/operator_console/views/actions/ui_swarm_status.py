"""Shared Start Swarm and live-terminal status helpers for the Operator Console."""

from __future__ import annotations


class SwarmStatusMixin:
    """Mirror swarm status across surfaces and gate live-only controls."""

    def _set_start_swarm_status(
        self,
        *,
        swarm_level: str,
        swarm_label: str,
        swarm_detail: str,
        command_preview: str | None = None,
    ) -> None:
        """Mirror Start Swarm state across the visible command surfaces."""
        self.home_workspace.set_start_swarm_status(
            level=swarm_level,
            label=swarm_label,
            detail=swarm_detail,
            command_preview=command_preview,
        )
        self.activity_workspace.set_start_swarm_status(
            status_level=swarm_level,
            status_label=swarm_label,
            detail=swarm_detail,
            command_preview=command_preview,
        )

    def _reject_live_terminal_action(
        self,
        action_label: str,
        *,
        update_swarm_status: bool = False,
    ) -> None:
        """Fail closed when Terminal.app-backed live controls are unavailable."""
        message = self._live_terminal_support_detail
        if action_label == "Launch Review":
            message += " Use Launch Dry Run to execute the repo-visible preflight only."
        self._append_output(f"[{action_label}] {message}\n")
        self._reveal_output_surface("command_output")
        self._record_event(
            "WARNING",
            "live_terminal_gated",
            f"{action_label} blocked because Terminal.app live launch is unavailable",
            details={"action": action_label},
        )
        self.statusBar().showMessage(message)
        if update_swarm_status:
            self._set_start_swarm_status(
                swarm_level="stale",
                swarm_label="Swarm Live-Gated",
                swarm_detail=message,
                command_preview=(
                    "Use Launch Dry Run to execute the review-channel preflight "
                    "without opening Terminal.app sessions."
                ),
            )

    def _refresh_live_terminal_controls(self) -> None:
        """Keep Terminal.app-only controls aligned with platform support."""
        if self._live_terminal_supported:
            return

        detail = self._live_terminal_support_detail
        for button in (
            self.launch_live_button,
            self.rollover_button,
            self.home_workspace.start_swarm_button,
            self.activity_workspace.activity_start_swarm_button,
        ):
            button.setEnabled(False)
            button.setToolTip(detail)
        self._set_start_swarm_status(
            swarm_level="stale",
            swarm_label="Swarm Live-Gated",
            swarm_detail=detail,
            command_preview=(
                "Use Launch Dry Run to execute the review-channel preflight "
                "without opening Terminal.app sessions."
            ),
        )
