"""Shape evaluation helpers for check_code_shape."""

from __future__ import annotations

from pathlib import Path

try:
    from check_bootstrap import import_attr
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import import_attr

BEST_PRACTICE_DOCS = import_attr("code_shape_policy", "BEST_PRACTICE_DOCS")
SHAPE_AUDIT_GUIDANCE = import_attr("code_shape_policy", "SHAPE_AUDIT_GUIDANCE")


def violation(
    *,
    path: Path,
    reason: str,
    guidance: str,
    policy,
    policy_source: str,
    lines: tuple[int | None, int],
) -> dict:
    base_lines, current_lines = lines
    growth = None if base_lines is None else current_lines - base_lines
    docs_refs = BEST_PRACTICE_DOCS.get(path.suffix, ())
    guidance_parts = [guidance]
    if reason != "current_file_missing":
        guidance_parts.append(SHAPE_AUDIT_GUIDANCE)
    if docs_refs:
        guidance_parts.append("Best-practice refs: " + ", ".join(docs_refs))
    return {
        "path": path.as_posix(),
        "violation_family": "shape",
        "reason": reason,
        "guidance": " ".join(guidance_parts),
        "best_practice_refs": list(docs_refs),
        "base_lines": base_lines,
        "current_lines": current_lines,
        "growth": growth,
        "policy": {
            "soft_limit": policy.soft_limit,
            "hard_limit": policy.hard_limit,
            "oversize_growth_limit": policy.oversize_growth_limit,
            "hard_lock_growth_limit": policy.hard_lock_growth_limit,
        },
        "policy_source": policy_source,
    }


def evaluate_shape(
    *,
    path: Path,
    policy,
    policy_source: str,
    base_lines: int | None,
    current_lines: int | None,
) -> dict | None:
    if current_lines is None:
        return violation(
            path=path, reason="current_file_missing",
            guidance="File is missing in current tree; rerun after resolving rename/delete state.",
            policy=policy, policy_source=policy_source,
            lines=(base_lines, 0),
        )

    if base_lines is None:
        if current_lines > policy.soft_limit:
            return violation(
                path=path, reason="new_file_exceeds_soft_limit",
                guidance="Split the new file before merge or keep it under the soft limit.",
                policy=policy, policy_source=policy_source,
                lines=(base_lines, current_lines),
            )
        return None

    growth = current_lines - base_lines
    if base_lines <= policy.soft_limit and current_lines > policy.soft_limit:
        return violation(
            path=path, reason="crossed_soft_limit",
            guidance="Refactor into smaller modules before crossing the soft limit.",
            policy=policy, policy_source=policy_source,
            lines=(base_lines, current_lines),
        )

    if (
        base_lines <= policy.hard_limit
        and current_lines > policy.hard_limit
        and growth > 0
    ):
        return violation(
            path=path, reason="crossed_hard_limit",
            guidance="Hard limit exceeded; split and reduce file size before merge.",
            policy=policy, policy_source=policy_source,
            lines=(base_lines, current_lines),
        )

    if base_lines > policy.hard_limit and growth > policy.hard_lock_growth_limit:
        return violation(
            path=path, reason="hard_locked_file_grew",
            guidance="File is already above hard limit; do not grow it further.",
            policy=policy, policy_source=policy_source,
            lines=(base_lines, current_lines),
        )

    if base_lines > policy.soft_limit and growth > policy.oversize_growth_limit:
        return violation(
            path=path, reason="oversize_file_growth_exceeded_budget",
            guidance="File is already above soft limit; keep growth within budget or decompose first.",
            policy=policy, policy_source=policy_source,
            lines=(base_lines, current_lines),
        )

    return None


def evaluate_absolute_shape(
    *,
    path: Path,
    policy,
    policy_source: str,
    current_lines: int | None,
) -> dict | None:
    if current_lines is None:
        return violation(
            path=path, reason="current_file_missing",
            guidance="File is missing in current tree; rerun after resolving rename/delete state.",
            policy=policy, policy_source=policy_source,
            lines=(None, 0),
        )

    if current_lines > policy.hard_limit:
        return violation(
            path=path, reason="absolute_hard_limit_exceeded",
            guidance="File exceeds absolute hard limit; split modules or lower file size before merge.",
            policy=policy, policy_source=policy_source,
            lines=(None, current_lines),
        )

    return None


def recent_history_line_counts(
    path: Path,
    review_window_days: int,
    guard,
    count_lines_fn,
) -> list[int]:
    """Return historical line counts for *path* over the review window.

    The *guard* (GuardContext) is passed explicitly to avoid depending on
    a module-level global.
    """
    if review_window_days <= 0:
        return []
    since_value = f"{review_window_days}.days"
    commits = guard.run_git(
        ["git", "log", "--since", since_value, "--format=%H", "--", path.as_posix()]
    ).stdout.splitlines()
    line_counts: list[int] = []
    seen: set[str] = set()
    for commit in commits:
        ref = commit.strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        lines = count_lines_fn(guard.read_text_from_ref(path, ref))
        if lines is not None:
            line_counts.append(lines)
    return line_counts


def evaluate_stale_path_override(
    *,
    path: Path,
    override_policy,
    language_default_policy,
    policy_source: str,
    current_lines: int | None,
    review_window: tuple[int, list[int]],
) -> dict | None:
    review_window_days, review_window_line_counts = review_window
    if current_lines is None:
        return None
    if override_policy.soft_limit <= language_default_policy.soft_limit:
        return None

    max_recent_lines = max(
        [current_lines, *review_window_line_counts], default=current_lines
    )
    if max_recent_lines > language_default_policy.soft_limit:
        return None

    return violation(
        path=path,
        reason="stale_path_override_below_default_soft_limit",
        guidance=(
            "PATH_POLICY_OVERRIDES entry is looser than the language default and the file stayed "
            f"at or below the language soft limit for {review_window_days} days. "
            "Remove the override or tighten it to a stricter-than-default budget."
        ),
        policy=override_policy, policy_source=policy_source,
        lines=(max_recent_lines, current_lines),
    )
