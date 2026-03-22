"""Git change-context helpers for probe topology."""

from __future__ import annotations

from ..collect import collect_git_status


def collect_changed_paths(
    since_ref: str | None,
    head_ref: str,
) -> tuple[set[str], list[str]]:
    status = collect_git_status(since_ref=since_ref, head_ref=head_ref)
    if "error" in status:
        return set(), [f"git change context unavailable: {status['error']}"]
    changes = status.get("changes", [])
    if not isinstance(changes, list):
        return set(), ["git change context unavailable: unexpected changes payload"]
    return {
        str(change.get("path") or "").strip()
        for change in changes
        if isinstance(change, dict) and str(change.get("path") or "").strip()
    }, []
