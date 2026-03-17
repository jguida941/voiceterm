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

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..config import REPO_ROOT
from ..repo_packs import active_path_config
from .launch import (
    list_terminal_profiles,
    resolve_terminal_profile_name,
)

# Backward-compat aliases sourced from the frozen path config
DEFAULT_BRIDGE_REL = active_path_config().bridge_rel
DEFAULT_REVIEW_CHANNEL_REL = active_path_config().review_channel_rel

DEFAULT_TERMINAL_PROFILE = "auto-dark"
DEFAULT_ROLLOVER_DIR_REL = active_path_config().rollover_root_rel
DEFAULT_ROLLOVER_THRESHOLD_PCT = 50
DEFAULT_ROLLOVER_ACK_WAIT_SECONDS = 180
BRIDGE_GUARD_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "checks/check_review_channel_bridge.py"
)
TRANSITIONAL_BRIDGE_HEADING = "## Transitional Markdown Bridge (Current Operating Mode)"
REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE = (
    "Transitional launcher: keep this path bridge-gated and retire or migrate it "
    "once the markdown bridge is inactive or the overlay-native review-channel "
    "launcher becomes canonical."
)
AUTO_DARK_TERMINAL_PROFILES = ("Pro", "Homebrew", "Clear Dark")
ACTIVE_SESSION_FRESHNESS_SECONDS = 120

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


@dataclass(frozen=True)
class ActiveSessionConflict:
    """One repo-visible session artifact that still looks live."""

    provider: str
    session_name: str
    metadata_path: str
    log_path: str | None
    age_seconds: int | None
    reason: str


def project_id_for_repo(repo_root: Path) -> str:
    """Build the stable repo/worktree identity used across review-channel artifacts."""
    digest = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def load_text(path: Path) -> str:
    """Read UTF-8 text from disk."""
    return path.read_text(encoding="utf-8")


def detect_active_session_conflicts(
    *,
    session_output_root: Path,
    freshness_seconds: int = ACTIVE_SESSION_FRESHNESS_SECONDS,
) -> tuple[ActiveSessionConflict, ...]:
    """Return live-looking session artifacts that should block a second launch."""
    session_dir = session_output_root / "sessions"
    if not session_dir.exists():
        return ()

    conflicts: list[ActiveSessionConflict] = []
    for provider in ("codex", "claude", "cursor"):
        metadata_path = session_dir / f"{provider}-conductor.json"
        if not metadata_path.exists():
            continue
        metadata = _load_session_metadata(metadata_path)
        if metadata is None:
            continue
        session_name = _session_metadata_text(metadata, "session_name") or f"{provider}-conductor"
        log_path_text = _session_metadata_text(metadata, "log_path")
        script_path_text = _session_metadata_text(metadata, "script_path")
        process_running = _probe_script_running(script_path_text)
        if process_running is True:
            conflicts.append(
                ActiveSessionConflict(
                    provider=provider,
                    session_name=session_name,
                    metadata_path=str(metadata_path),
                    log_path=log_path_text,
                    age_seconds=_log_age_seconds(log_path_text),
                    reason="existing conductor script process is still running",
                )
            )
            continue
        if process_running is False:
            continue
        age_seconds = _log_age_seconds(log_path_text)
        if age_seconds is None or age_seconds > freshness_seconds:
            continue
        conflicts.append(
            ActiveSessionConflict(
                provider=provider,
                session_name=session_name,
                metadata_path=str(metadata_path),
                log_path=log_path_text,
                age_seconds=age_seconds,
                reason=(
                    "session trace was updated "
                    f"{age_seconds}s ago and the script process could not be probed"
                ),
            )
        )
    return tuple(conflicts)


def summarize_active_session_conflicts(
    conflicts: tuple[ActiveSessionConflict, ...],
) -> str:
    """Render one concise duplicate-launch blocker message."""
    if not conflicts:
        return "none"
    parts: list[str] = []
    for conflict in conflicts:
        detail = f"{conflict.provider}: {conflict.reason}"
        if conflict.log_path:
            detail += f" (log: {conflict.log_path})"
        parts.append(detail)
    return "; ".join(parts)


def bridge_is_active(review_channel_text: str) -> bool:
    """Return True when the transitional markdown bridge remains active."""
    return TRANSITIONAL_BRIDGE_HEADING in review_channel_text


def _load_session_metadata(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _session_metadata_text(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _probe_script_running(script_path_text: str | None) -> bool | None:
    if not script_path_text or shutil.which("pgrep") is None:
        return None
    try:
        result = subprocess.run(
            ["pgrep", "-f", script_path_text],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 0 and result.stdout.strip():
        return True
    if result.returncode == 1:
        return False
    return None


def _log_age_seconds(log_path_text: str | None) -> int | None:
    if not log_path_text:
        return None
    log_path = Path(log_path_text)
    if not log_path.exists():
        return None
    modified = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(tz=timezone.utc) - modified
    return max(0, int(age.total_seconds()))


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
    """Infer the provider name from a lane assignment's lane title prefix."""
    lowered = lane.lower()
    if lowered.startswith("codex "):
        return "codex"
    if lowered.startswith("claude "):
        return "claude"
    if lowered.startswith("cursor "):
        return "cursor"
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
    """Validate transitional-launch prerequisites and return parsed state.

    When ``execution_mode`` is ``"auto"`` and the markdown bridge is inactive
    or missing, the function still succeeds if ``review_channel.md`` exists
    and contains lane assignments. This allows the launcher to operate from
    event-backed state without a live ``code_audit.md`` bridge.
    """
    if execution_mode == "overlay":
        raise ValueError(
            "Overlay-native launch is not implemented yet. This launcher is "
            "bridge-gated for the current markdown-bridge cycle only."
        )
    if not review_channel_path.exists():
        raise ValueError(f"Missing review-channel plan: {review_channel_path}")
    review_channel_text = load_text(review_channel_path)
    bridge_active = bridge_is_active(review_channel_text) and bridge_path.exists()
    if not bridge_active and execution_mode == "markdown-bridge":
        if not bridge_is_active(review_channel_text):
            raise ValueError(
                "The transitional markdown bridge is inactive in review_channel.md. "
                "Retire or migrate this launcher instead of using it against a "
                "structured/overlay-native checkout."
            )
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
