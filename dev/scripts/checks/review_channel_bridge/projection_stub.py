"""Deprecated bridge projection-stub recognition."""

from __future__ import annotations


DEPRECATED_BRIDGE_STUB_MARKER = "bridge.md - Deprecated Projection Stub"


def is_deprecated_bridge_stub(text: str) -> bool:
    return (
        DEPRECATED_BRIDGE_STUB_MARKER in text
        and "This file is not authority." in text
        and "projection_stale" in text
    )


def deprecated_bridge_stub_report(*, relative_path: str, untracked: bool) -> dict:
    report = {
        "path": relative_path,
        "ok": not untracked,
        "active": True,
        "deprecated_projection_stub": True,
        "projection_stale": True,
        "missing_h2": [],
        "missing_markers": [],
    }
    if untracked:
        report.update(
            {
                "untracked": True,
                "error": f"Bridge-active file is untracked by git: {relative_path}",
            }
        )
    return report
