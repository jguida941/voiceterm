#!/usr/bin/env python3
"""Deterministic Claude HUD stress runner with frame snapshots + anomaly summary.

Usage:
  python3 dev/scripts/tests/claude_hud_stress.py

This script runs voiceterm in a detached `screen` session so we can capture the
rendered terminal framebuffer without relying on manual screenshots.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


DEFAULT_STRESS_PROMPT = (
    "run exactly 5 bash commands and exactly 5 web searches in parallel to stress test "
    "the terminal; if approvals are needed ask once and continue; then summarize results"
)

HUD_MARKERS = ("VoiceTerm", "PTT", "[rec]", "[ptt]", "[send]", "[hud]", "[back")
APPROVAL_MARKERS = (
    "Do you want to proceed?",
    "This command requires approval",
    "1. Yes",
    "2. Yes",
    "2. No",
    "don't ask again",
)

LOG_PATTERNS = {
    "suppression_transition": "[claude-hud-debug] suppression transition",
    "approval_overlap_risk": "[claude-hud-anomaly] prompt overlap risk",
    "hud_missing_unsuppressed": "[claude-hud-anomaly] unsuppressed HUD committed with zero banner height",
    "hud_missing_input": "[claude-hud-anomaly] user input observed unsuppressed HUD with zero banner height",
    "zero_geometry_skip": "[claude-hud-anomaly] apply_pty_winsize skipped due zero geometry",
    "redraw_committed": "[claude-hud-debug] redraw committed",
    "repair_redraw": "[claude-hud-debug] scheduled cursor+claude HUD repair redraw fired",
    "user_input_activity": "[claude-hud-debug] user input activity",
}

SUPPRESSION_TRANSITION_RE = re.compile(
    r"^\[(?P<ts>\d+)\].*\[claude-hud-debug\] suppression transition (?P<prev>true|false) -> (?P<next>true|false)"
)
REDRAW_COMMITTED_RE = re.compile(
    r"^\[(?P<ts>\d+)\].*\[claude-hud-debug\] redraw committed .*banner_height=(?P<banner>\d+).*prompt_suppressed=Some\((?P<supp>true|false)\)"
)


@dataclass
class FrameResult:
    index: int
    captured_at_epoch_s: float
    path: str
    hud_visible: bool
    hud_visible_bottom: bool
    approval_visible: bool
    hud_marker_rows: List[int]
    approval_marker_rows: List[int]
    text_excerpt: str


class StressRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.repo_root = Path(args.repo_root).resolve()
        self.rust_dir = self.repo_root / "rust"
        self.artifacts_dir = Path(args.artifacts_dir).resolve()
        self.frames_dir = self.artifacts_dir / "frames"
        self.session = f"vt_hud_stress_{os.getpid()}"
        self.log_path = Path(tempfile.gettempdir()) / "voiceterm_tui.log"
        self.frames: List[FrameResult] = []
        self.approvals_sent = 0
        self.commands = []

    def run(self) -> int:
        self._ensure_prereqs()
        self._prepare_artifacts()

        if self.args.build:
            self._run_checked(["cargo", "build", "--bin", "voiceterm"], cwd=self.rust_dir)

        if self.log_path.exists():
            self.log_path.unlink()

        try:
            self._start_screen_session()
            self._collect_startup_frames()
            self._drive_stress_prompt()
            self._snapshot_final()
        finally:
            self._shutdown_session()

        summary = self._summarize()
        self._write_outputs(summary)
        self._print_summary(summary)

        # Non-zero exit on anomalies for CI/scriptability.
        if self.args.fail_on_anomaly and summary["anomaly_total"] > 0:
            return 2
        return 0

    def _ensure_prereqs(self) -> None:
        if shutil.which("screen") is None:
            raise RuntimeError("screen is required but was not found in PATH")
        if not self.rust_dir.exists():
            raise RuntimeError(f"rust workspace not found: {self.rust_dir}")
        binary = self.rust_dir / "target" / "debug" / "voiceterm"
        if not binary.exists() and not self.args.build:
            raise RuntimeError(
                f"voiceterm binary missing at {binary}; run with --build or build first"
            )

    def _prepare_artifacts(self) -> None:
        self.frames_dir.mkdir(parents=True, exist_ok=True)

    def _run_checked(self, cmd: List[str], cwd: Path | None = None) -> None:
        self.commands.append({"cmd": cmd, "cwd": str(cwd) if cwd else None})
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

    def _run_best_effort(self, cmd: List[str]) -> None:
        self.commands.append({"cmd": cmd, "cwd": None})
        subprocess.run(cmd, check=False)

    def _start_screen_session(self) -> None:
        launch = (
            f'cd "{self.rust_dir}"; '
            "export TERM_PROGRAM=cursor; "
            "export VOICETERM_DEBUG_CLAUDE_HUD=1; "
            "./target/debug/voiceterm --logs --claude"
        )
        self._run_checked(["screen", "-dmS", self.session, "bash", "-lc", launch])

    def _hardcopy(self, index: int) -> FrameResult:
        path = self.frames_dir / f"frame_{index:03d}.txt"
        captured_at_epoch_s = time.time()
        self._run_checked([
            "screen",
            "-S",
            self.session,
            "-p",
            "0",
            "-X",
            "hardcopy",
            str(path),
        ])
        text = path.read_text(errors="ignore") if path.exists() else ""
        viewport_lines = self._viewport_lines(text)
        viewport_text = "\n".join(viewport_lines)
        hud_marker_rows = self._marker_rows(viewport_lines, HUD_MARKERS)
        approval_marker_rows = self._marker_rows(viewport_lines, APPROVAL_MARKERS)
        hud_visible = len(hud_marker_rows) > 0
        approval_visible = len(approval_marker_rows) > 0
        bottom_rows = max(1, int(self.args.hud_bottom_rows))
        bottom_start_row = max(1, len(viewport_lines) - bottom_rows + 1)
        hud_visible_bottom = any(row >= bottom_start_row for row in hud_marker_rows)
        excerpt = "\n".join(viewport_lines[-14:])
        frame = FrameResult(
            index=index,
            captured_at_epoch_s=captured_at_epoch_s,
            path=str(path),
            hud_visible=hud_visible,
            hud_visible_bottom=hud_visible_bottom,
            approval_visible=approval_visible,
            hud_marker_rows=hud_marker_rows,
            approval_marker_rows=approval_marker_rows,
            text_excerpt=excerpt,
        )
        self.frames.append(frame)
        return frame

    def _viewport_lines(self, text: str) -> List[str]:
        # `screen -X hardcopy` can include stale scrollback depending on host
        # profile. Limit anomaly checks to the visible viewport tail so we
        # report what the operator can currently see.
        cleaned = text.replace("\x00", "")
        lines = cleaned.splitlines()
        if not lines:
            return [cleaned] if cleaned else []
        viewport_rows = max(1, int(self.args.viewport_rows))
        return lines[-viewport_rows:]

    def _marker_rows(self, lines: List[str], markers: tuple[str, ...]) -> List[int]:
        rows: List[int] = []
        for index, line in enumerate(lines, start=1):
            if any(marker in line for marker in markers):
                rows.append(index)
        return rows

    def _stuff(self, text: str) -> None:
        self._run_checked(
            ["screen", "-S", self.session, "-p", "0", "-X", "stuff", text]
        )

    def _collect_startup_frames(self) -> None:
        time.sleep(self.args.startup_wait_s)
        self._hardcopy(0)

        if self.args.keyprobe:
            self._stuff(self.args.keyprobe)
            time.sleep(self.args.keyprobe_wait_s)
            self._hardcopy(1)

    def _drive_stress_prompt(self) -> None:
        self._stuff(self.args.prompt)
        self._stuff("\n")
        started = time.time()

        frame_idx = 2
        while time.time() - started < self.args.run_seconds:
            time.sleep(self.args.poll_interval_s)
            frame = self._hardcopy(frame_idx)
            frame_idx += 1

            # Auto-approve prompt cards.
            if frame.approval_visible:
                self._stuff("1\n")
                self.approvals_sent += 1

    def _snapshot_final(self) -> None:
        self._hardcopy(999)

    def _shutdown_session(self) -> None:
        self._run_best_effort(
            ["screen", "-S", self.session, "-p", "0", "-X", "stuff", "\x03"]
        )
        time.sleep(1.0)
        self._run_best_effort(["screen", "-S", self.session, "-X", "quit"])

    def _count_log_patterns(self) -> Dict[str, int]:
        counts = {key: 0 for key in LOG_PATTERNS}
        if not self.log_path.exists():
            return counts

        with self.log_path.open("r", errors="ignore") as handle:
            for line in handle:
                for key, pattern in LOG_PATTERNS.items():
                    if pattern in line:
                        counts[key] += 1
        return counts

    def _parse_log_events(self) -> Dict[str, List[Dict[str, object]]]:
        events: Dict[str, List[Dict[str, object]]] = {
            "suppression_transitions": [],
            "redraw_commits": [],
        }
        if not self.log_path.exists():
            return events

        with self.log_path.open("r", errors="ignore") as handle:
            for line in handle:
                suppression_match = SUPPRESSION_TRANSITION_RE.search(line)
                if suppression_match:
                    events["suppression_transitions"].append(
                        {
                            "timestamp": float(suppression_match.group("ts")),
                            "from_suppressed": suppression_match.group("prev") == "true",
                            "to_suppressed": suppression_match.group("next") == "true",
                        }
                    )
                redraw_match = REDRAW_COMMITTED_RE.search(line)
                if redraw_match:
                    events["redraw_commits"].append(
                        {
                            "timestamp": float(redraw_match.group("ts")),
                            "banner_height": int(redraw_match.group("banner")),
                            "prompt_suppressed": redraw_match.group("supp") == "true",
                        }
                    )
        return events

    def _latest_event_before_or_at(
        self, events: List[Dict[str, object]], timestamp: float
    ) -> Dict[str, object] | None:
        latest: Dict[str, object] | None = None
        for event in events:
            event_ts = float(event["timestamp"])
            if event_ts <= timestamp:
                latest = event
                continue
            break
        return latest

    def _first_event_after_or_at(
        self, events: List[Dict[str, object]], timestamp: float
    ) -> Dict[str, object] | None:
        for event in events:
            event_ts = float(event["timestamp"])
            if event_ts >= timestamp:
                return event
        return None

    def _correlate_frames_with_logs(
        self, log_events: Dict[str, List[Dict[str, object]]]
    ) -> List[Dict[str, object]]:
        transitions = log_events["suppression_transitions"]
        redraw_commits = log_events["redraw_commits"]
        correlations: List[Dict[str, object]] = []

        for frame in self.frames:
            prev_transition = self._latest_event_before_or_at(
                transitions, frame.captured_at_epoch_s
            )
            next_transition = self._first_event_after_or_at(
                transitions, frame.captured_at_epoch_s
            )
            latest_redraw = self._latest_event_before_or_at(
                redraw_commits, frame.captured_at_epoch_s
            )

            correlations.append(
                {
                    "index": frame.index,
                    "captured_at_epoch_s": round(frame.captured_at_epoch_s, 3),
                    "prev_transition_epoch_s": prev_transition["timestamp"]
                    if prev_transition
                    else None,
                    "prev_transition_to_suppressed": prev_transition["to_suppressed"]
                    if prev_transition
                    else None,
                    "next_transition_epoch_s": next_transition["timestamp"]
                    if next_transition
                    else None,
                    "next_transition_to_suppressed": next_transition["to_suppressed"]
                    if next_transition
                    else None,
                    "latest_redraw_epoch_s": latest_redraw["timestamp"]
                    if latest_redraw
                    else None,
                    "latest_redraw_banner_height": latest_redraw["banner_height"]
                    if latest_redraw
                    else None,
                    "latest_redraw_prompt_suppressed": latest_redraw["prompt_suppressed"]
                    if latest_redraw
                    else None,
                }
            )
        return correlations

    def _summarize(self) -> Dict[str, object]:
        log_counts = self._count_log_patterns()
        log_events = self._parse_log_events()
        frame_correlations = self._correlate_frames_with_logs(log_events)
        frame_correlation_by_index = {
            int(correlation["index"]): correlation for correlation in frame_correlations
        }

        hud_missing_frames = [
            f.index for f in self.frames if not f.hud_visible_bottom and not f.approval_visible
        ]
        approval_with_hud_frames = [
            f.index for f in self.frames if f.approval_visible and f.hud_visible_bottom
        ]
        approval_with_hud_suppressed_commit_frames = []
        hud_missing_unsuppressed_commit_frames = []
        frames_without_redraw_context = []

        for frame in self.frames:
            correlation = frame_correlation_by_index.get(frame.index, {})
            latest_redraw_prompt_suppressed = correlation.get(
                "latest_redraw_prompt_suppressed"
            )
            latest_redraw_banner_height = correlation.get("latest_redraw_banner_height")
            if correlation.get("latest_redraw_epoch_s") is None:
                frames_without_redraw_context.append(frame.index)
            if (
                frame.approval_visible
                and frame.hud_visible_bottom
                and latest_redraw_prompt_suppressed is True
            ):
                approval_with_hud_suppressed_commit_frames.append(frame.index)
            if (
                not frame.approval_visible
                and not frame.hud_visible_bottom
                and latest_redraw_prompt_suppressed is False
                and int(latest_redraw_banner_height or 0) > 0
            ):
                hud_missing_unsuppressed_commit_frames.append(frame.index)

        anomalies = {
            "hud_missing_frames": hud_missing_frames,
            "approval_with_hud_frames": approval_with_hud_frames,
            "approval_with_hud_suppressed_commit_frames": approval_with_hud_suppressed_commit_frames,
            "hud_missing_unsuppressed_commit_frames": hud_missing_unsuppressed_commit_frames,
            "frames_without_redraw_context": frames_without_redraw_context,
            "approval_overlap_risk_logs": log_counts["approval_overlap_risk"],
            "hud_missing_unsuppressed_logs": log_counts["hud_missing_unsuppressed"],
            "hud_missing_input_logs": log_counts["hud_missing_input"],
            "zero_geometry_skip_logs": log_counts["zero_geometry_skip"],
            "input_not_observed_in_logs": log_counts["user_input_activity"] == 0,
        }
        anomaly_total = sum(
            [
                len(hud_missing_frames),
                len(approval_with_hud_frames),
                len(approval_with_hud_suppressed_commit_frames),
                len(hud_missing_unsuppressed_commit_frames),
                anomalies["approval_overlap_risk_logs"],
                anomalies["hud_missing_unsuppressed_logs"],
                anomalies["hud_missing_input_logs"],
                anomalies["zero_geometry_skip_logs"],
                1 if anomalies["input_not_observed_in_logs"] else 0,
            ]
        )

        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(self.repo_root),
            "rust_dir": str(self.rust_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "session": self.session,
            "log_path": str(self.log_path),
            "run_seconds": self.args.run_seconds,
            "poll_interval_s": self.args.poll_interval_s,
            "approvals_sent": self.approvals_sent,
            "frame_count": len(self.frames),
            "log_counts": log_counts,
            "log_event_counts": {
                "suppression_transitions": len(log_events["suppression_transitions"]),
                "redraw_commits": len(log_events["redraw_commits"]),
            },
            "anomalies": anomalies,
            "anomaly_total": anomaly_total,
            "commands": self.commands,
            "frames": [
                {
                    "index": frame.index,
                    "captured_at_epoch_s": round(frame.captured_at_epoch_s, 3),
                    "path": frame.path,
                    "hud_visible": frame.hud_visible,
                    "hud_visible_bottom": frame.hud_visible_bottom,
                    "approval_visible": frame.approval_visible,
                    "hud_marker_rows": frame.hud_marker_rows,
                    "approval_marker_rows": frame.approval_marker_rows,
                    "text_excerpt": frame.text_excerpt,
                    "correlation": frame_correlation_by_index.get(frame.index, {}),
                }
                for frame in self.frames
            ],
        }

    def _write_outputs(self, summary: Dict[str, object]) -> None:
        summary_json = self.artifacts_dir / "summary.json"
        summary_md = self.artifacts_dir / "summary.md"

        summary_json.write_text(json.dumps(summary, indent=2) + "\n")

        lines = [
            "# Claude HUD Stress Summary",
            "",
            f"- timestamp_utc: `{summary['timestamp_utc']}`",
            f"- artifacts_dir: `{summary['artifacts_dir']}`",
            f"- log_path: `{summary['log_path']}`",
            f"- frame_count: `{summary['frame_count']}`",
            f"- approvals_sent: `{summary['approvals_sent']}`",
            f"- anomaly_total: `{summary['anomaly_total']}`",
            "",
            "## Log Counts",
        ]
        for key, value in summary["log_counts"].items():
            lines.append(f"- {key}: `{value}`")
        lines.append(
            f"- suppression_transition_events: `{summary['log_event_counts']['suppression_transitions']}`"
        )
        lines.append(
            f"- redraw_commit_events: `{summary['log_event_counts']['redraw_commits']}`"
        )

        lines.extend(
            [
                "",
                "## Anomalies",
                f"- hud_missing_frames: `{summary['anomalies']['hud_missing_frames']}`",
                f"- approval_with_hud_frames: `{summary['anomalies']['approval_with_hud_frames']}`",
                f"- approval_with_hud_suppressed_commit_frames: `{summary['anomalies']['approval_with_hud_suppressed_commit_frames']}`",
                f"- hud_missing_unsuppressed_commit_frames: `{summary['anomalies']['hud_missing_unsuppressed_commit_frames']}`",
                f"- frames_without_redraw_context: `{summary['anomalies']['frames_without_redraw_context']}`",
                f"- approval_overlap_risk_logs: `{summary['anomalies']['approval_overlap_risk_logs']}`",
                f"- hud_missing_unsuppressed_logs: `{summary['anomalies']['hud_missing_unsuppressed_logs']}`",
                f"- hud_missing_input_logs: `{summary['anomalies']['hud_missing_input_logs']}`",
                f"- zero_geometry_skip_logs: `{summary['anomalies']['zero_geometry_skip_logs']}`",
                f"- input_not_observed_in_logs: `{summary['anomalies']['input_not_observed_in_logs']}`",
                "",
                "## Artifacts",
                "- frame snapshots: `frames/frame_*.txt`",
                "- structured summary: `summary.json`",
            ]
        )

        summary_md.write_text("\n".join(lines) + "\n")

        if self.log_path.exists():
            shutil.copy2(self.log_path, self.artifacts_dir / "voiceterm_tui.log")

    def _print_summary(self, summary: Dict[str, object]) -> None:
        print("artifacts_dir:", summary["artifacts_dir"])
        print("log_path:", summary["log_path"])
        print("frame_count:", summary["frame_count"])
        print("approvals_sent:", summary["approvals_sent"])
        print("anomaly_total:", summary["anomaly_total"])
        print("anomalies:", json.dumps(summary["anomalies"], indent=2))


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default_artifacts = (
        repo_root / "dev" / "reports" / "audits" / "claude_hud_stress" / timestamp
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root), help="Repository root path")
    parser.add_argument(
        "--artifacts-dir",
        default=str(default_artifacts),
        help="Directory to write stress artifacts",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_STRESS_PROMPT,
        help="Prompt sent to Claude after startup",
    )
    parser.add_argument(
        "--run-seconds",
        type=int,
        default=120,
        help="Duration for stress polling loop after prompt send",
    )
    parser.add_argument(
        "--poll-interval-s",
        type=float,
        default=2.0,
        help="Frame capture polling interval",
    )
    parser.add_argument(
        "--startup-wait-s",
        type=float,
        default=10.0,
        help="Initial wait before first snapshot",
    )
    parser.add_argument(
        "--keyprobe",
        default="d",
        help="Single key sent after startup to test keypress HUD behavior",
    )
    parser.add_argument(
        "--keyprobe-wait-s",
        type=float,
        default=2.0,
        help="Wait after keyprobe before second snapshot",
    )
    parser.add_argument(
        "--viewport-rows",
        type=int,
        default=24,
        help="Visible terminal viewport rows used for anomaly marker detection",
    )
    parser.add_argument(
        "--hud-bottom-rows",
        type=int,
        default=6,
        help="Bottom viewport rows considered authoritative for HUD visibility checks",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run `cargo build --bin voiceterm` before stress execution",
    )
    parser.add_argument(
        "--fail-on-anomaly",
        action="store_true",
        help="Exit non-zero when anomaly_total > 0",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = StressRunner(args)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
