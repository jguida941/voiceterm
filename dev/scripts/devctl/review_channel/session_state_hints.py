"""Session-log hints used by review-channel remediation/status surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from .bridge_text_cleanup import strip_terminal_bytes
from .session_probe import _load_session_metadata, _log_age_seconds, _session_metadata_text

_SESSION_PROVIDERS = ("codex", "claude", "cursor")
_SESSION_LOG_TAIL_BYTES = 16_384
_MAX_SESSION_HINT_LOG_AGE_SECONDS = 900
_INTERRUPT_PROMPT_PATTERNS = (
    re.compile(
        r"conversation interrupted\b.*tell the model what to do differently",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"interrupted\s*[·-]\s*what should .* do instead",
        re.IGNORECASE | re.DOTALL,
    ),
)
_WAITING_FOR_INPUT_PATTERNS = (
    re.compile(r"(?m)^[❯›>]\s*$"),
    re.compile(r"(?m)^[❯›>]\s+"),
)


@dataclass(frozen=True)
class SessionStateHint:
    """One bounded session-state hint derived from a conductor log tail."""

    provider: str
    state: str
    summary: str
    log_path: str
    age_seconds: int | None = None


def detect_session_state_hints(
    *,
    session_output_root: Path,
    max_log_age_seconds: int = _MAX_SESSION_HINT_LOG_AGE_SECONDS,
) -> tuple[SessionStateHint, ...]:
    """Return bounded session-state hints from recent conductor log tails."""
    session_dir = session_output_root / "sessions"
    if not session_dir.exists():
        return ()

    hints: list[SessionStateHint] = []
    for provider in _SESSION_PROVIDERS:
        metadata_path = session_dir / f"{provider}-conductor.json"
        if not metadata_path.exists():
            continue
        metadata = _load_session_metadata(metadata_path)
        if metadata is None:
            continue
        log_path_text = _session_metadata_text(metadata, "log_path")
        if not log_path_text:
            continue
        age_seconds = _log_age_seconds(log_path_text)
        if age_seconds is None or age_seconds > max_log_age_seconds:
            continue
        log_path = Path(log_path_text)
        if not log_path.exists():
            continue
        cleaned_tail = _clean_log_tail(log_path)
        hint = _classify_session_state_hint(
            provider=provider,
            cleaned_tail=cleaned_tail,
            log_path=log_path_text,
            age_seconds=age_seconds,
        )
        if hint is not None:
            hints.append(hint)
    return tuple(hints)


def session_state_hints_to_dict(
    hints: tuple[SessionStateHint, ...],
) -> dict[str, dict[str, object]]:
    """Convert session-state hints into JSON-friendly provider mappings."""
    return {hint.provider: asdict(hint) for hint in hints}


def provider_session_state_hint(
    bridge_liveness: dict[str, object],
    *,
    provider: str,
) -> dict[str, object]:
    """Return one provider hint from bridge-liveness state when present."""
    raw_hints = bridge_liveness.get("session_state_hints")
    if not isinstance(raw_hints, dict):
        return {}
    hint = raw_hints.get(provider)
    return hint if isinstance(hint, dict) else {}


def _clean_log_tail(log_path: Path) -> str:
    try:
        raw_tail = log_path.read_bytes()[-_SESSION_LOG_TAIL_BYTES:]
    except OSError:
        return ""
    decoded = raw_tail.decode("utf-8", errors="ignore")
    return strip_terminal_bytes(decoded)


def _classify_session_state_hint(
    *,
    provider: str,
    cleaned_tail: str,
    log_path: str,
    age_seconds: int | None,
) -> SessionStateHint | None:
    normalized = cleaned_tail.strip()
    if not normalized:
        return None
    if any(pattern.search(normalized) for pattern in _INTERRUPT_PROMPT_PATTERNS):
        return SessionStateHint(
            provider=provider,
            state="interrupt_prompt",
            summary=(
                f"{provider.title()} conductor log shows an interrupt/retry prompt "
                "instead of active loop progress."
            ),
            log_path=log_path,
            age_seconds=age_seconds,
        )
    if any(pattern.search(normalized) for pattern in _WAITING_FOR_INPUT_PATTERNS):
        return SessionStateHint(
            provider=provider,
            state="waiting_for_user_input",
            summary=(
                f"{provider.title()} conductor log appears to be waiting for manual "
                "input instead of progressing the repo-owned loop."
            ),
            log_path=log_path,
            age_seconds=age_seconds,
        )
    return None
