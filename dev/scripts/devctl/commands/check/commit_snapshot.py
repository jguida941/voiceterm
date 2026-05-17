"""Commit-snapshot mode helpers for `devctl check`."""

from __future__ import annotations

from dataclasses import replace


def apply_commit_snapshot_mode(args) -> str | None:
    """Constrain `check` to guards that can inspect a staged commit tree."""
    if not getattr(args, "commit_snapshot", False):
        return None
    if not getattr(args, "since_ref", None):
        return "--commit-snapshot requires --since-ref"
    args.skip_fmt = True
    args.skip_clippy = True
    args.skip_tests = True
    args.skip_build = True
    args.no_host_process_cleanup = True
    args.no_process_sweep_cleanup = True
    return None


def policy_for_commit_snapshot(quality_policy):
    """Return only range-capable checks for staged-tree validation."""
    return replace(
        quality_policy,
        ai_guard_checks=tuple(
            spec for spec in quality_policy.ai_guard_checks if spec.supports_commit_range
        ),
        review_probe_checks=tuple(
            spec
            for spec in quality_policy.review_probe_checks
            if spec.supports_commit_range
        ),
    )
