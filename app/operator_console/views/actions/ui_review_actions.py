from __future__ import annotations

from typing import Callable, Mapping

from ...workflows import (
    build_launch_command,
    build_rollover_command,
    evaluate_review_channel_launch,
    evaluate_review_channel_rollover,
    evaluate_start_swarm_launch,
    evaluate_start_swarm_preflight,
    parse_review_channel_report,
    render_command,
)


class ReviewLaunchActionsMixin:
    """Review-channel actions, live gating, and chained launch orchestration."""

    def launch_dry_run(self) -> None:
        self._start_command(
            build_launch_command(
                live=False,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
            ),
            context={"flow": "review_channel", "action": "launch", "live": False},
            busy_label="Dry Run...",
            busy_buttons=self._dry_run_action_buttons(),
        )

    def launch_live(self) -> None:
        if not self._live_terminal_supported:
            self._reject_live_terminal_action("Launch Live")
            return
        self._start_command(
            build_launch_command(
                live=True,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
            ),
            context={"flow": "review_channel", "action": "launch", "live": True},
            busy_label="Launch...",
            busy_buttons=(self.launch_live_button,),
        )

    def start_swarm(self) -> None:
        if not self._live_terminal_supported:
            self._reject_live_terminal_action(
                "Launch Review",
                update_swarm_status=True,
            )
            return
        preflight_command = build_launch_command(
            live=False,
            output_format="json",
            refresh_bridge_heartbeat_if_stale=True,
        )
        if not self._start_command(
            preflight_command,
            context={"flow": "start_swarm", "step": "preflight"},
            busy_label="Swarm...",
            busy_buttons=self._review_action_buttons(),
        ):
            return
        detail = (
            "Running review-channel dry-run preflight. The live launch will start "
            "automatically if the preflight stays green."
        )
        self._set_start_swarm_status(
            swarm_level="warning",
            swarm_label="Swarm Preflight",
            swarm_detail=detail,
            command_preview=f"Preflight: {render_command(preflight_command)}",
        )
        self._append_output(
            "[Launch Review] Dry-run preflight started. Live launch will follow automatically if it passes.\n"
        )
        self._record_event(
            "INFO",
            "start_swarm_requested",
            "Operator requested Launch Review chained launch",
            details={"step": "preflight"},
        )

    def rollover_live(self) -> None:
        if not self._live_terminal_supported:
            self._reject_live_terminal_action("Rollover")
            return
        self._start_command(
            build_rollover_command(
                threshold_pct=self.threshold_spin.value(),
                await_ack_seconds=self.ack_wait_spin.value(),
                live=True,
                output_format="json",
                refresh_bridge_heartbeat_if_stale=True,
            ),
            context={"flow": "review_channel", "action": "rollover", "live": True},
            busy_label="Rollover...",
            busy_buttons=(self.rollover_button,),
        )

    def _resolve_start_swarm_result(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
        evaluator: Callable[[Mapping[str, object]], tuple[bool, str]],
        invalid_json_message: str,
        empty_output_message: str,
    ) -> tuple[bool, str]:
        stripped_stdout = stdout.strip()
        if stripped_stdout:
            try:
                report = parse_review_channel_report(stripped_stdout)
            except ValueError:
                detail = self._first_visible_line(stderr) or invalid_json_message
                return False, detail
            return evaluator(report)
        detail = self._first_visible_line(stderr)
        if detail:
            return False, detail
        if exit_code:
            return False, empty_output_message
        return False, invalid_json_message

    def _handle_start_swarm_completion(
        self,
        *,
        step: str,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> bool:
        if step == "preflight":
            return self._handle_swarm_preflight_result(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )
        if step == "live":
            return self._handle_swarm_live_result(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )
        return False

    def _handle_swarm_preflight_result(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> bool:
        ok, message = self._resolve_start_swarm_result(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            evaluator=evaluate_start_swarm_preflight,
            invalid_json_message=(
                "Start Swarm preflight failed: review-channel did not return a JSON status report."
            ),
            empty_output_message=(
                "Start Swarm preflight failed without a readable status payload."
            ),
        )
        if not ok:
            self._set_start_swarm_status(
                swarm_level="stale",
                swarm_label="Swarm Blocked",
                swarm_detail=message,
                command_preview=(
                    "Last command: "
                    + render_command(
                        build_launch_command(
                            live=False,
                            output_format="json",
                            refresh_bridge_heartbeat_if_stale=True,
                        )
                    )
                ),
            )
            self._append_output(f"[Launch Review] {message}\n")
            self._record_event(
                "WARNING" if exit_code == 0 else "ERROR",
                "start_swarm_preflight_failed",
                "Start Swarm preflight blocked live launch",
                details={"exit_code": exit_code, "message": message},
            )
            return False

        launch_detail = f"{message} Launching live review-channel sessions."
        live_command = build_launch_command(
            live=True,
            output_format="json",
            refresh_bridge_heartbeat_if_stale=True,
        )
        if not self._live_terminal_supported:
            self._set_start_swarm_status(
                swarm_level="stale",
                swarm_label="Swarm Live-Gated",
                swarm_detail=self._live_terminal_support_detail,
                command_preview=(
                    "Use Launch Dry Run to execute the review-channel preflight "
                    "without opening Terminal.app sessions."
                ),
            )
            self._append_output(
                f"[Launch Review] {self._live_terminal_support_detail}\n"
            )
            self._record_event(
                "WARNING",
                "start_swarm_live_gated",
                "Start Swarm preflight passed but live launch is Terminal.app-gated",
                details={"message": self._live_terminal_support_detail},
            )
            return False
        self._set_start_swarm_status(
            swarm_level="warning",
            swarm_label="Swarm Launching",
            swarm_detail=launch_detail,
            command_preview=f"Live launch: {render_command(live_command)}",
        )
        self._append_output(f"[Launch Review] {message}\n")
        self._record_event(
            "INFO",
            "start_swarm_preflight_passed",
            "Start Swarm preflight passed; launching live swarm",
            details={"message": message},
        )
        if not self._start_command(
            live_command,
            context={"flow": "start_swarm", "step": "live"},
            busy_label="Swarm...",
            busy_buttons=self._review_action_buttons(),
        ):
            failure = (
                "Start Swarm live launch could not begin because another command is already running."
            )
            self._set_start_swarm_status(
                swarm_level="stale",
                swarm_label="Swarm Failed",
                swarm_detail=failure,
                command_preview=f"Blocked live launch: {render_command(live_command)}",
            )
            self._append_output(f"[Launch Review] {failure}\n")
            self._record_event(
                "ERROR",
                "start_swarm_live_launch_rejected",
                "Start Swarm preflight passed but the live launch could not begin",
                details={"message": failure},
            )
            return False
        return True

    def _handle_swarm_live_result(
        self,
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> bool:
        ok, message = self._resolve_start_swarm_result(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            evaluator=evaluate_start_swarm_launch,
            invalid_json_message=(
                "Start Swarm live launch failed: review-channel did not return a JSON status report."
            ),
            empty_output_message=(
                "Start Swarm live launch failed without a readable status payload."
            ),
        )
        live_command_preview = (
            "Last command: "
            + render_command(
                build_launch_command(
                    live=True,
                    output_format="json",
                    refresh_bridge_heartbeat_if_stale=True,
                )
            )
        )
        if ok:
            self._set_start_swarm_status(
                swarm_level="active",
                swarm_label="Swarm Running",
                swarm_detail=message,
                command_preview=live_command_preview,
            )
            self._record_event(
                "INFO",
                "start_swarm_live_ok",
                "Start Swarm live launch reported success",
                details={"message": message},
            )
        else:
            self._set_start_swarm_status(
                swarm_level="stale",
                swarm_label="Swarm Failed",
                swarm_detail=message,
                command_preview=live_command_preview,
            )
            self._record_event(
                "ERROR" if exit_code else "WARNING",
                "start_swarm_live_failed",
                "Start Swarm live launch reported failure",
                details={"exit_code": exit_code, "message": message},
            )
        self._append_output(f"[Launch Review] {message}\n")
        return False

    def _review_channel_completion_message(
        self,
        *,
        action: str,
        live: bool,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> tuple[bool, str]:
        stripped_stdout = stdout.strip()
        if stripped_stdout:
            try:
                report = parse_review_channel_report(stripped_stdout)
            except ValueError:
                detail = self._first_visible_line(stderr)
                if detail:
                    return False, detail
                command_name = "Live launch" if action == "launch" and live else action.title()
                return False, f"{command_name} did not return a readable status report."
            if action == "rollover":
                return evaluate_review_channel_rollover(report)
            return evaluate_review_channel_launch(report, live=live)
        detail = self._first_visible_line(stderr)
        if detail:
            return False, detail
        if action == "rollover":
            fallback = "Rollover failed." if exit_code else "Rollover completed."
        elif live:
            fallback = "Live launch failed." if exit_code else "Live launch completed."
        else:
            fallback = "Dry run failed." if exit_code else "Dry run completed."
        return exit_code == 0, fallback
