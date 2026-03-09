"""Helpers for the transitional review-channel launcher.

This bridge-gated helper follows the current markdown coordination path owned
by:

- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/review_channel.md`
- `code_audit.md`

Developers changing this file should keep the generated prompts aligned with
the repo-owned `devctl` guidance in `dev/scripts/README.md` and
`dev/guides/DEVCTL_AUTOGUIDE.md`, plus the execution contract in
`dev/active/continuous_swarm.md`.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .common import display_path
from .config import REPO_ROOT
from .review_channel_launch import (
    build_launch_sessions as _build_launch_sessions,
    build_rollover_command as _build_rollover_command,
    launch_terminal_sessions as _launch_terminal_sessions,
    list_terminal_profiles,
    resolve_cli_path as _resolve_cli_path,
    resolve_terminal_profile_name,
)
from .review_channel_prompt import build_conductor_prompt as _build_conductor_prompt
from .review_channel_handoff import (
    BRIDGE_LIVENESS_KEYS,
    expected_rollover_ack_line,
    expected_rollover_ack_section,
)

DEFAULT_REVIEW_CHANNEL_REL = "dev/active/review_channel.md"
DEFAULT_BRIDGE_REL = "code_audit.md"
DEFAULT_TERMINAL_PROFILE = "auto-dark"
DEFAULT_ROLLOVER_DIR_REL = "dev/reports/review_channel/rollovers"
DEFAULT_ROLLOVER_THRESHOLD_PCT = 50
DEFAULT_ROLLOVER_ACK_WAIT_SECONDS = 180
BRIDGE_GUARD_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "checks/check_review_channel_bridge.py"
)
TRANSITIONAL_BRIDGE_HEADING = "## Transitional Markdown Bridge (Current Operating Mode)"
REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE = (
    "Transitional launcher: keep this path bridge-gated and retire or migrate it "
    "once the markdown bridge is inactive or the overlay-native review-channel "
    "launcher becomes canonical."
)
AUTO_DARK_TERMINAL_PROFILES = ("Pro", "Homebrew", "Clear Dark")

LANE_ROW_RE = re.compile(
    r"^\|\s*`(?P<agent>AGENT-\d+)`\s*\|"
    r"\s*(?P<lane>.+?)\s*\|"
    r"\s*(?P<docs>.+?)\s*\|"
    r"\s*(?P<scope>.+?)\s*\|"
    r"\s*(?P<worktree>.+?)\s*\|"
    r"\s*(?P<branch>.+?)\s*\|$"
)


@dataclass(frozen=True)
class LaneAssignment:
    """One parsed lane assignment from the review-channel swarm table."""

    agent_id: str
    provider: str
    lane: str
    docs: str
    mp_scope: str
    worktree: str
    branch: str


def load_text(path: Path) -> str:
    """Read UTF-8 text from disk."""
    return path.read_text(encoding="utf-8")


def bridge_is_active(review_channel_text: str) -> bool:
    """Return True when the transitional markdown bridge remains active."""
    return TRANSITIONAL_BRIDGE_HEADING in review_channel_text


def parse_lane_assignments(review_channel_text: str) -> list[LaneAssignment]:
    """Parse the merged 8+8 lane table from review_channel markdown."""
    lanes: list[LaneAssignment] = []
    for line in review_channel_text.splitlines():
        match = LANE_ROW_RE.match(line.strip())
        if match is None:
            continue
        lane = match.group("lane").strip()
        try:
            provider = _provider_from_lane(lane=lane, agent_id=match.group("agent"))
        except ValueError:
            continue
        lanes.append(
            LaneAssignment(
                agent_id=match.group("agent"),
                provider=provider,
                lane=lane,
                docs=match.group("docs").strip(),
                mp_scope=match.group("scope").strip(),
                worktree=match.group("worktree").strip(),
                branch=match.group("branch").strip(),
            )
        )
    return lanes


def _provider_from_lane(*, lane: str, agent_id: str) -> str:
    lowered = lane.lower()
    if lowered.startswith("codex "):
        return "codex"
    if lowered.startswith("claude "):
        return "claude"
    raise ValueError(f"Unable to infer provider for {agent_id}: {lane}")


def filter_provider_lanes(
    lanes: list[LaneAssignment],
    *,
    provider: str,
) -> list[LaneAssignment]:
    """Return lane assignments for one provider."""
    return [lane for lane in lanes if lane.provider == provider]


def ensure_launcher_prereqs(
    *,
    review_channel_path: Path,
    bridge_path: Path,
    execution_mode: str,
) -> tuple[str, list[LaneAssignment]]:
    """Validate transitional-launch prerequisites and return parsed state."""
    if execution_mode == "overlay":
        raise ValueError(
            "Overlay-native launch is not implemented yet. This launcher is "
            "bridge-gated for the current markdown-bridge cycle only."
        )
    if not review_channel_path.exists():
        raise ValueError(f"Missing review-channel plan: {review_channel_path}")
    review_channel_text = load_text(review_channel_path)
    if not bridge_is_active(review_channel_text):
        raise ValueError(
            "The transitional markdown bridge is inactive in review_channel.md. "
            "Retire or migrate this launcher instead of using it against a "
            "structured/overlay-native checkout."
        )
    if not bridge_path.exists():
        raise ValueError(
            f"Bridge mode is active but the live bridge file is missing: {bridge_path}"
        )
    lanes = parse_lane_assignments(review_channel_text)
    if not lanes:
        raise ValueError(
            "No AGENT lane assignments were found in review_channel.md."
        )
    return review_channel_text, lanes


def build_bridge_guard_report(
    *,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
) -> dict[str, object]:
    """Execute the repo-owned bridge guard against explicit bridge paths."""
    spec = importlib.util.spec_from_file_location(
        "review_channel_bridge_guard_runtime",
        BRIDGE_GUARD_SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise ValueError(
            f"Unable to load review-channel bridge guard: {BRIDGE_GUARD_SCRIPT_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPO_ROOT = repo_root
    module.CODE_AUDIT_PATH = bridge_path
    module.REVIEW_CHANNEL_PATH = review_channel_path
    if not (repo_root / ".git").exists():
        module._is_tracked_by_git = lambda _path: True
    return module.build_report()


def summarize_bridge_guard_failures(report: dict[str, object]) -> str:
    """Reduce a bridge-guard report into a compact human-readable error string."""
    issues: list[str] = []
    for key in ("code_audit", "review_channel"):
        section = report.get(key)
        if not isinstance(section, dict):
            continue
        path = section.get("path", key)
        error = section.get("error")
        if isinstance(error, str) and error:
            issues.append(f"{path}: {error}")
        missing_h2 = section.get("missing_h2")
        if isinstance(missing_h2, list) and missing_h2:
            issues.append(f"{path}: missing headings {', '.join(missing_h2)}")
        missing_markers = section.get("missing_markers")
        if isinstance(missing_markers, list) and missing_markers:
            issues.append(f"{path}: missing markers {', '.join(missing_markers)}")
        metadata_errors = section.get("metadata_errors")
        if isinstance(metadata_errors, list):
            issues.extend(f"{path}: {error}" for error in metadata_errors)
        state_errors = section.get("state_errors")
        if isinstance(state_errors, list):
            issues.extend(f"{path}: {error}" for error in state_errors)
    return "; ".join(issues) if issues else "bridge guard reported unknown errors"


def build_conductor_prompt(
    *,
    provider: str,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    lanes: list[LaneAssignment],
    codex_workers: int,
    claude_workers: int,
    dangerous: bool,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    bridge_liveness: dict[str, object] | None = None,
    handoff_bundle: dict[str, str] | None = None,
) -> str:
    """Render the initial conductor prompt for Codex or Claude."""
    provider_name = "Codex" if provider == "codex" else "Claude"
    other_name = "Claude" if provider == "codex" else "Codex"
    rollover_command = _build_rollover_command(
        dangerous=dangerous,
        rollover_threshold_pct=rollover_threshold_pct,
        await_ack_seconds=await_ack_seconds,
    )
    return _build_conductor_prompt(
        provider=provider,
        provider_name=provider_name,
        other_name=other_name,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        lanes=lanes,
        codex_workers=codex_workers,
        claude_workers=claude_workers,
        dangerous=dangerous,
        rollover_threshold_pct=rollover_threshold_pct,
        await_ack_seconds=await_ack_seconds,
        retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        rollover_command=rollover_command,
        bridge_liveness=bridge_liveness,
        handoff_bundle=handoff_bundle,
    )
def build_launch_sessions(
    *,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    codex_lanes: list[LaneAssignment],
    claude_lanes: list[LaneAssignment],
    codex_workers: int,
    claude_workers: int,
    dangerous: bool,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    bridge_liveness: dict[str, object] | None = None,
    handoff_bundle: dict[str, str] | None = None,
    script_dir: Path | None = None,
    session_output_root: Path | None = None,
) -> list[dict[str, object]]:
    """Create conductor launch scripts and return session metadata."""
    return _build_launch_sessions(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        codex_workers=codex_workers,
        claude_workers=claude_workers,
        dangerous=dangerous,
        rollover_threshold_pct=rollover_threshold_pct,
        await_ack_seconds=await_ack_seconds,
        default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
        retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        bridge_liveness=bridge_liveness,
        handoff_bundle=handoff_bundle,
        script_dir=script_dir,
        session_output_root=session_output_root,
        resolve_cli_path_fn=resolve_cli_path,
    )


def resolve_cli_path(provider: str) -> str:
    """Resolve the requested provider CLI from PATH."""
    return _resolve_cli_path(provider)


def launch_terminal_sessions(
    sessions: list[dict[str, object]],
    *,
    terminal_profile: str | None,
) -> None:
    """Open one Terminal.app window per session script."""
    _launch_terminal_sessions(
        sessions,
        terminal_profile=terminal_profile,
        default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
        auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
    )
