"""Validate the temporary markdown review-channel bridge contract."""

from __future__ import annotations

import importlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS_DIR = Path(__file__).resolve().parent.parent
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_review_channel_handoff = importlib.import_module("dev.scripts.devctl.review_channel.handoff")
_bridge_validation = importlib.import_module("dev.scripts.devctl.review_channel.bridge_validation")
_bridge_projection = importlib.import_module("dev.scripts.devctl.review_channel.bridge_projection")
_bridge_heading_aliases = importlib.import_module(
    "dev.scripts.devctl.review_channel.bridge_heading_aliases"
)
_typed_bridge_state = importlib.import_module(
    "dev.scripts.checks.review_channel_bridge.typed_state"
)

DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS = _review_channel_handoff.DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS
extract_bridge_snapshot = _review_channel_handoff.extract_bridge_snapshot
validate_live_bridge_contract = _bridge_validation.validate_live_bridge_contract
bridge_hygiene_errors = _bridge_projection.bridge_hygiene_errors
canonical_bridge_heading = _bridge_heading_aliases.canonical_bridge_heading

BRIDGE_PATH = REPO_ROOT / "bridge.md"
REVIEW_CHANNEL_PATH = REPO_ROOT / "dev/active/review_channel.md"
DEPRECATED_BRIDGE_STUB_MARKER = "bridge.md - Deprecated Projection Stub"

REQUIRED_BRIDGE_H2 = [
    "Start-Of-Conversation Rules",
    "Protocol",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Implementer Status",
    "Implementer Questions",
    "Implementer Ack",
    "Current Instruction For Implementer",
    "Last Reviewed Scope",
]

REQUIRED_BRIDGE_MARKERS = [
    # Codex finding rev_pkt_1785: drop the `python3` prefix so the marker
    # matches the interpreter actually rendered into bridge.md (which now
    # comes from `os.path.basename(sys.executable)` and may be `python3.11`
    # or any future interpreter), not just the literal `python3` shim.
    "dev/scripts/devctl.py startup-context --role reviewer --format summary`",
    "dev/scripts/devctl.py startup-context --role implementer --format summary`",
    "dev/scripts/devctl.py session-resume --role reviewer --format bootstrap`",
    "dev/scripts/devctl.py session-resume --role implementer --format bootstrap`",
    "dev/scripts/devctl.py context-graph --mode bootstrap --format md`",
    "`AGENTS.md`",
    "`dev/active/INDEX.md`",
    "`dev/active/MASTER_PLAN.md`",
    "`dev/active/review_channel.md`",
    "operator-visible chat update",
    "When `Reviewer mode` is `active_dual_agent`, this file is the live",
    "When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or",
    "If `Current Instruction For Implementer` or `Poll Status` says `hold steady`,",
    "status/ack updates must be substantive",
    "Do not use raw shell sleep loops such as `sleep 60`",
    "Specialist workers should wake on owned-path changes",
    "- Last Codex poll:",
    "- Last Codex poll (Local",
    "- Reviewer mode:",
    "- Last non-audit worktree hash:",
]

REQUIRED_REVIEW_CHANNEL_MARKERS = [
    "## Transitional Markdown Bridge (Current Operating Mode)",
    "`bridge.md`",
    "each meaningful Codex reviewer write to\n   `bridge.md` must also emit a concise operator-visible chat update",
    "`MASTER_PLAN.md` remains the canonical tracker and\n   `INDEX.md` remains the router",
    "`last_poll_local`",
    "`check_review_channel_bridge.py`",
    "`devctl swarm_run --continuous`",
    "only one Codex conductor updates the Codex-owned bridge",
    "Bridge behavior is mode-aware.",
    "Claude must stay in polling mode",
    "heartbeat every five minutes even when the blocker set is unchanged",
    "Default multi-agent wakeups should be change-routed instead of brute-force",
    "Completion stall",
]

ROLE_ASSIGNMENT_PATTERN = re.compile(
    r"(?m)^(?:\d+\.\s+)?(?P<reviewer>[A-Za-z0-9_-]+) is the reviewer\. "
    r"(?P<implementer>[A-Za-z0-9_-]+) is the coder\.$"
)


def _extract_h2(text: str) -> list[str]:
    return [
        canonical_bridge_heading(match.group(1).strip())
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE)
    ]


def _normalize_marker_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _missing_markers(text: str, required_markers: list[str]) -> list[str]:
    normalized_text = _normalize_marker_text(text)
    return [
        marker
        for marker in required_markers
        if not any(
            _normalize_marker_text(variant) in normalized_text
            for variant in _marker_variants(marker)
        )
    ]


def _marker_variants(marker: str) -> tuple[str, ...]:
    """Return accepted marker text variants during bridge role-label migration."""
    variants = {str(marker)}
    for canonical, alias in (
        ("Current Instruction For Implementer", "Current Instruction For Claude"),
        ("Implementer Status", "Claude Status"),
        ("Implementer Questions", "Claude Questions"),
        ("Implementer Ack", "Claude Ack"),
        (
            "the implementer ACK section (`Claude Ack`)",
            "the implementer ACK section (`Claude Ack` compatibility heading)",
        ),
    ):
        for value in tuple(variants):
            if canonical in value:
                variants.add(value.replace(canonical, alias))
    return tuple(variants)


def _is_deprecated_bridge_stub(text: str) -> bool:
    return (
        DEPRECATED_BRIDGE_STUB_MARKER in text
        and "This file is not authority." in text
        and "projection_stale" in text
    )


def _bridge_role_names(text: str) -> tuple[str, str]:
    match = ROLE_ASSIGNMENT_PATTERN.search(text)
    if match is None:
        return ("Codex", "Claude")
    return (
        str(match.group("reviewer")).strip() or "Codex",
        str(match.group("implementer")).strip() or "Claude",
    )


def _reviewer_owned_sections_marker(reviewer_name: str) -> str:
    if reviewer_name == "Codex":
        return "Only the Codex conductor may update the Codex-owned sections"
    return (
        f"Only the {reviewer_name} conductor may update the reviewer-owned "
        "sections, including the `Last Codex poll` compatibility heartbeat"
    )


def _implementer_owned_sections_marker(implementer_name: str) -> str:
    return (
        f"Only the {implementer_name} conductor may update the implementer-owned "
        "compatibility sections (`Implementer Status`, `Implementer Questions`, `Implementer Ack`)"
    )


def _required_bridge_markers(text: str) -> list[str]:
    reviewer_name, implementer_name = _bridge_role_names(text)
    return list(
        dict.fromkeys(
            [
                *REQUIRED_BRIDGE_MARKERS,
                f"{reviewer_name} is the reviewer. {implementer_name} is the coder.",
                (
                    f"{reviewer_name} should start from `Poll Status`, `Current "
                    "Verdict`, `Open Findings`, `Current Instruction For Implementer`, "
                    "and `Last Reviewed Scope`."
                ),
                (
                    f"{implementer_name} should start from `Poll Status`, "
                    "`Current Verdict`, `Open Findings`, `Current Instruction For "
                    "Implementer`, and `Last Reviewed Scope`"
                ),
                (
                    f"{implementer_name} must read `Last Codex poll` / "
                    "`Poll Status` first on each repoll."
                ),
                (
                    f"{reviewer_name} must poll non-`bridge.md` worktree changes "
                    "every 2-3 minutes"
                ),
                (
                    f"{reviewer_name} must exclude `bridge.md` itself when "
                    "computing the reviewed"
                ),
                f"{reviewer_name} stays reviewer-only by default",
                (
                    "When the current slice is accepted and scoped plan work "
                    f"remains, {reviewer_name} must"
                ),
                (
                    f"{reviewer_name} must emit an operator-visible heartbeat "
                    "every 5 minutes"
                ),
                _reviewer_owned_sections_marker(reviewer_name),
                _implementer_owned_sections_marker(implementer_name),
            ]
        )
    )


def _enforce_live_poll_freshness() -> bool:
    """GitHub-hosted CI cannot act as the live Codex reviewer heartbeat owner."""
    return os.getenv("GITHUB_ACTIONS", "").strip().lower() != "true"


def _current_utc() -> datetime:
    """Compatibility clock hook retained for older unit tests."""
    return datetime.now(timezone.utc)


def _is_tracked_by_git(path: Path) -> bool:
    """Return True if the file is tracked by git (committed or staged)."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # If git is unavailable or times out, skip the tracking check
        return True


def _build_path_report(
    *,
    path: Path,
    required_h2: list[str] | None = None,
    required_markers: list[str],
    optional: bool = False,
    require_tracked: bool = False,
) -> dict:
    relative_path = str(path.relative_to(REPO_ROOT))
    if not path.exists():
        if optional:
            return {
                "path": relative_path,
                "ok": True,
                "active": False,
                "missing_h2": [],
                "missing_markers": [],
            }
        return {
            "path": relative_path,
            "ok": False,
            "active": False,
            "error": f"Missing file: {relative_path}",
            "missing_h2": required_h2 or [],
            "missing_markers": required_markers,
        }

    untracked = require_tracked and not _is_tracked_by_git(path)

    text = path.read_text(encoding="utf-8")
    if path == BRIDGE_PATH and _is_deprecated_bridge_stub(text):
        return {
            "path": relative_path,
            "ok": not untracked,
            "active": True,
            "deprecated_projection_stub": True,
            "projection_stale": True,
            "missing_h2": [],
            "missing_markers": [],
            **(
                {
                    "untracked": True,
                    "error": f"Bridge-active file is untracked by git: {relative_path}",
                }
                if untracked
                else {}
            ),
        }
    headings = _extract_h2(text)
    missing_h2 = [heading for heading in required_h2 if heading not in headings] if required_h2 is not None else []
    if path == BRIDGE_PATH:
        required_markers = _required_bridge_markers(text)
    missing_markers = _missing_markers(text, required_markers)
    report: dict = {
        "path": relative_path,
        "ok": not (missing_h2 or missing_markers or untracked),
        "active": True,
        "missing_h2": missing_h2,
        "missing_markers": missing_markers,
    }
    if path == BRIDGE_PATH:
        hygiene_errors = bridge_hygiene_errors(text)
        report["hygiene_errors"] = hygiene_errors
        report["ok"] = report["ok"] and not hygiene_errors
    if untracked:
        report["untracked"] = True
        report["error"] = f"Bridge-active file is untracked by git: {relative_path}"
    return report


def build_report() -> dict:
    review_channel_text = (
        REVIEW_CHANNEL_PATH.read_text(encoding="utf-8")
        if REVIEW_CHANNEL_PATH.exists()
        else ""
    )
    review_bridge_active = (
        "## Transitional Markdown Bridge (Current Operating Mode)"
        in review_channel_text
    )
    typed_review_state = (
        _typed_bridge_state.load_typed_review_state(REPO_ROOT)
        if review_bridge_active
        else None
    )
    bridge = _build_path_report(
        path=BRIDGE_PATH,
        required_h2=REQUIRED_BRIDGE_H2,
        required_markers=REQUIRED_BRIDGE_MARKERS,
        optional=not review_bridge_active,
        require_tracked=review_bridge_active,
    )
    if (
        review_bridge_active
        and bridge.get("ok", False)
        and not bridge.get("deprecated_projection_stub")
    ):
        bridge_text = BRIDGE_PATH.read_text(encoding="utf-8")
        role_packet_progress_current = (
            _typed_bridge_state.role_neutral_packet_progress_current(
                typed_review_state,
                target_roles=("implementer", "coder"),
            )
        )
        bridge["role_packet_progress_current"] = role_packet_progress_current
        metadata_errors = _typed_bridge_state.validate_bridge_metadata(
            bridge_text,
            typed_review_state,
            enforce_live_poll_freshness=_enforce_live_poll_freshness(),
        )
        if metadata_errors:
            bridge["ok"] = False
            bridge["metadata_errors"] = metadata_errors
        state_errors = validate_live_bridge_contract(
            extract_bridge_snapshot(bridge_text),
            typed_current_session=(
                getattr(typed_review_state, "current_session", None)
                if typed_review_state is not None
                else None
            ),
            role_packet_progress_current=role_packet_progress_current,
        )
        if state_errors:
            bridge["ok"] = False
            bridge["state_errors"] = state_errors
    review_channel = _build_path_report(
        path=REVIEW_CHANNEL_PATH,
        required_markers=(
            REQUIRED_REVIEW_CHANNEL_MARKERS if review_bridge_active else []
        ),
        require_tracked=review_bridge_active,
    )
    return {
        "command": "check_review_channel_bridge",
        "review_bridge_active": review_bridge_active,
        "ok": bridge["ok"] and review_channel["ok"],
        "bridge": bridge,
        "review_channel": review_channel,
    }


def render_md(report: dict) -> str:
    lines = ["# check_review_channel_bridge", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- review_bridge_active: {report.get('review_bridge_active', False)}")
    for key in ("bridge", "review_channel"):
        section = report[key]
        lines.append(f"- {key}_path: {section['path']}")
        lines.append(f"- {key}_ok: {section.get('ok', False)}")
        if key == "bridge":
            lines.append(f"- {key}_active: {section.get('active', False)}")
            if section.get("deprecated_projection_stub"):
                lines.append(f"- {key}_deprecated_projection_stub: True")
            if section.get("projection_stale"):
                lines.append(f"- {key}_projection_stale: True")
        if section.get("untracked"):
            lines.append(f"- {key}_untracked: True")
        error = section.get("error")
        if error:
            lines.append(f"- {key}_error: {error}")
            if section.get("untracked"):
                continue
        missing_h2 = section.get("missing_h2", [])
        lines.append(
            f"- {key}_missing_h2: {', '.join(missing_h2) if missing_h2 else 'none'}"
        )
        missing_markers = section.get("missing_markers", [])
        lines.append(
            "- "
            f"{key}_missing_markers: "
            f"{', '.join(missing_markers) if missing_markers else 'none'}"
        )
        hygiene_errors = section.get("hygiene_errors", [])
        if hygiene_errors:
            lines.append("- " f"{key}_hygiene_errors: " f"{', '.join(hygiene_errors)}")
        metadata_errors = section.get("metadata_errors", [])
        if metadata_errors:
            lines.append(
                "- "
                f"{key}_metadata_errors: "
                f"{', '.join(metadata_errors) if metadata_errors else 'none'}"
            )
        state_errors = section.get("state_errors", [])
        if state_errors:
            lines.append(
                "- "
                f"{key}_state_errors: "
                f"{', '.join(state_errors) if state_errors else 'none'}"
            )
    return "\n".join(lines)
