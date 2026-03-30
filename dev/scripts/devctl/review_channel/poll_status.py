"""Poll-status rewrite helpers shared by bridge heartbeat writers."""

from __future__ import annotations

import re

AUTO_REFRESH_PREFIX = "- Auto-refreshed reviewer heartbeat:"
POLL_STATUS_SECTION_RE = re.compile(
    r"(^## Poll Status[ \t]*$\n)(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
_REVIEWER_CHECKPOINT_POLL_STATUS_PREFIX = "- Reviewer checkpoint "
_AUTOMATION_POLL_STATUS_PREFIXES = (
    AUTO_REFRESH_PREFIX,
    "- Reviewer heartbeat refreshed through repo-owned tooling",
)


def rewrite_poll_status(text: str, *, note: str) -> str:
    """Rewrite the live Poll Status section, preserving real checkpoints."""
    def replace_section(match: re.Match[str]) -> str:
        body = _effective_poll_status_body(
            existing_body=match.group(2),
            replacement_note=note,
        )
        return f"{match.group(1)}\n{body}\n\n"

    rewritten, count = POLL_STATUS_SECTION_RE.subn(replace_section, text, count=1)
    if count != 1:
        raise ValueError("Unable to locate the `Poll Status` section in the bridge.")
    return rewritten


def _effective_poll_status_body(
    *,
    existing_body: str,
    replacement_note: str,
) -> str:
    existing = existing_body.strip()
    replacement = replacement_note.strip()
    if not existing:
        return replacement
    if _should_preserve_reviewer_checkpoint(
        existing_body=existing,
        replacement_note=replacement,
    ):
        return existing
    return replacement


def _should_preserve_reviewer_checkpoint(
    *,
    existing_body: str,
    replacement_note: str,
) -> bool:
    first_existing = next(
        (line.strip() for line in existing_body.splitlines() if line.strip()),
        "",
    )
    first_replacement = next(
        (line.strip() for line in replacement_note.splitlines() if line.strip()),
        "",
    )
    return first_existing.startswith(
        _REVIEWER_CHECKPOINT_POLL_STATUS_PREFIX
    ) and first_replacement.startswith(_AUTOMATION_POLL_STATUS_PREFIXES)
