"""Hint builders for the compatibility-shim review probe."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

if __package__:
    from .bootstrap import import_attr
    from .probe_compatibility_rules import ShimFamilyRule, ShimFinding, ShimRootRule
    from .probe_compatibility_usage import ShimLifecycle
else:  # pragma: no cover - standalone script fallback
    from bootstrap import import_attr
    from probe_compatibility_rules import ShimFamilyRule, ShimFinding, ShimRootRule
    from probe_compatibility_usage import ShimLifecycle

RiskHint = import_attr("probe_bootstrap", "RiskHint")

REVIEW_LENS = "architecture"

AI_INSTRUCTIONS = {
    "missing_metadata": (
        "Compatibility shims should stay auditable. Add the canonical shim "
        "metadata fields (`shim-owner`, `shim-reason`, `shim-expiry`, "
        "`shim-target`) so maintainers can see who owns the seam, why it "
        "still exists, when it should expire, and where the real "
        "implementation lives."
    ),
    "invalid_expiry": (
        "Use an ISO `YYYY-MM-DD` expiry for compatibility shims. Keep the "
        "date realistic and close enough to force a revisit instead of "
        "turning the wrapper into invisible permanent debt."
    ),
    "expired_shim": (
        "This compatibility shim is past its recorded expiry. Either remove "
        "the wrapper because downstream callers have migrated, or extend the "
        "expiry with an updated reason and owner if the seam is still needed."
    ),
    "unresolved_target": (
        "The shim target should point at the live implementation path. Update "
        "`shim-target` to a real repo-relative module/file path so migration "
        "progress can be audited mechanically."
    ),
    "shim_heavy_root": (
        "This root is accumulating too many approved compatibility shims. "
        "Finish the namespace move or split the remaining legacy callers so "
        "the root stops acting like a long-lived wrapper drawer."
    ),
    "shim_heavy_family": (
        "This flat family still carries too many approved compatibility "
        "wrappers. Continue the namespace migration until the family no "
        "longer depends on a large wrapper budget."
    ),
    "temporary_repo_callers": (
        "This shim is still temporary, not a declared long-lived public "
        "contract, and repo-visible callers still depend on it. Migrate those "
        "callers to the canonical target module or explicitly allowlist the "
        "shim in repo policy if it is a deliberate public surface."
    ),
    "temporary_unused": (
        "This shim is not allowlisted as a long-lived public contract and the "
        "repo no longer references it. Remove the wrapper now, or add it to "
        "the explicit public-shim allowlist if external consumers still depend "
        "on it."
    ),
}


def sample_paths(findings: list[ShimFinding]) -> str:
    """Render a short sample-path summary for one hint."""
    samples = [finding.relative_path.as_posix() for finding in findings[:3]]
    more = len(findings) - len(samples)
    sample_text = ", ".join(samples)
    if more > 0:
        return f"{sample_text} (+{more} more)"
    return sample_text


def build_missing_metadata_hint(
    *,
    root: Path,
    findings: list[ShimFinding],
) -> RiskHint:
    """Build the root-level missing-metadata hint."""
    missing_counter = Counter(
        field
        for finding in findings
        for field in finding.missing_metadata_fields
    )
    field_summary = ", ".join(
        f"{field} x{missing_counter[field]}" for field in sorted(missing_counter)
    )
    return RiskHint(
        file=root.as_posix(),
        symbol="(root)",
        risk_type="compatibility_shim",
        severity="medium",
        signals=[
            (
                f"{len(findings)} shim files under `{root.as_posix()}` are missing "
                f"canonical metadata ({field_summary}); examples: {sample_paths(findings)}"
            )
        ],
        ai_instruction=AI_INSTRUCTIONS["missing_metadata"],
        review_lens=REVIEW_LENS,
    )


def build_heavy_root_hint(
    *,
    rule: ShimRootRule,
    valid_findings: list[ShimFinding],
    public_shim_count: int = 0,
) -> RiskHint:
    """Build the root-level shim-budget hint."""
    excluded_text = (
        f"; {public_shim_count} allowlisted public shim(s) excluded from the count"
        if public_shim_count
        else ""
    )
    return RiskHint(
        file=rule.root.as_posix(),
        symbol="(root)",
        risk_type="compatibility_shim",
        severity="medium",
        signals=[
            (
                f"{len(valid_findings)} temporary compatibility shims under "
                f"`{rule.root.as_posix()}` exceed the budget of {rule.max_shims}"
                f"{excluded_text}; examples: {sample_paths(valid_findings)}"
            )
        ],
        ai_instruction=AI_INSTRUCTIONS["shim_heavy_root"],
        review_lens=REVIEW_LENS,
    )


def build_heavy_family_hint(
    *,
    rule: ShimFamilyRule,
    valid_findings: list[ShimFinding],
    public_shim_count: int = 0,
) -> RiskHint:
    """Build the family-level shim-budget hint."""
    excluded_text = (
        f"; {public_shim_count} allowlisted public shim(s) excluded from the count"
        if public_shim_count
        else ""
    )
    return RiskHint(
        file=rule.root.as_posix(),
        symbol=rule.flat_prefix,
        risk_type="compatibility_shim",
        severity="medium",
        signals=[
            (
                f"{len(valid_findings)} temporary `{rule.flat_prefix}*` shims under "
                f"`{rule.root.as_posix()}` exceed the family budget of {rule.max_shims}"
                f"{excluded_text}; examples: {sample_paths(valid_findings)}"
            )
        ],
        ai_instruction=AI_INSTRUCTIONS["shim_heavy_family"],
        review_lens=REVIEW_LENS,
    )


def _sample_lifecycle_references(lifecycles: list[ShimLifecycle]) -> str:
    samples: list[str] = []
    for lifecycle in lifecycles[:3]:
        ref_paths = [ref.source_path.as_posix() for ref in lifecycle.references[:2]]
        more = len(lifecycle.references) - len(ref_paths)
        refs = ", ".join(ref_paths)
        if more > 0:
            refs = f"{refs} (+{more} more refs)"
        samples.append(f"{lifecycle.finding.relative_path.as_posix()} <- {refs}")
    return "; ".join(samples)


def build_temporary_repo_callers_hint(
    *,
    root: Path,
    lifecycles: list[ShimLifecycle],
) -> RiskHint:
    """Build the aggregated temporary-shim migration hint."""
    total_references = sum(len(lifecycle.references) for lifecycle in lifecycles)
    return RiskHint(
        file=root.as_posix(),
        symbol="(root)",
        risk_type="compatibility_shim_migration",
        severity="medium",
        signals=[
            (
                f"{len(lifecycles)} temporary compatibility shims under "
                f"`{root.as_posix()}` still have {total_references} repo-visible "
                f"caller/reference(s); examples: {_sample_lifecycle_references(lifecycles)}"
            )
        ],
        ai_instruction=AI_INSTRUCTIONS["temporary_repo_callers"],
        review_lens=REVIEW_LENS,
    )


def build_temporary_unused_hint(
    *,
    root: Path,
    lifecycles: list[ShimLifecycle],
) -> RiskHint:
    """Build the aggregated removable-shim hint."""
    return RiskHint(
        file=root.as_posix(),
        symbol="(root)",
        risk_type="compatibility_shim_unused",
        severity="high",
        signals=[
            (
                f"{len(lifecycles)} temporary compatibility shims under "
                f"`{root.as_posix()}` have no repo-visible callers and are not "
                f"allowlisted public contracts; examples: "
                f"{sample_paths([lifecycle.finding for lifecycle in lifecycles])}"
            )
        ],
        ai_instruction=AI_INSTRUCTIONS["temporary_unused"],
        review_lens=REVIEW_LENS,
    )


def _target_path(repo_root: Path, target: str) -> Path | None:
    target_text = target.strip()
    if not target_text:
        return None
    target_path = repo_root / Path(target_text)
    if target_path.exists():
        return target_path
    if "/" in target_text or "\\" in target_text or target_text.endswith(".py"):
        return None
    dotted = Path(*target_text.split("."))
    module_path = repo_root / dotted.with_suffix(".py")
    package_init = repo_root / dotted / "__init__.py"
    if module_path.exists():
        return module_path
    if package_init.exists():
        return package_init
    return None


def _expiry_status(value: str) -> tuple[date | None, str | None]:
    try:
        return date.fromisoformat(value.strip()), None
    except ValueError:
        return None, "invalid"


def build_file_level_hints(repo_root: Path, finding: ShimFinding) -> list[RiskHint]:
    """Build expiry/target hints for one valid shim."""
    hints: list[RiskHint] = []
    expiry = str(finding.metadata.get("expiry") or "").strip()
    if expiry:
        expiry_date, error = _expiry_status(expiry)
        if error == "invalid":
            hints.append(
                RiskHint(
                    file=finding.relative_path.as_posix(),
                    symbol="(shim)",
                    risk_type="compatibility_shim",
                    severity="medium",
                    signals=[f"`shim-expiry` must use `YYYY-MM-DD`; found `{expiry}`"],
                    ai_instruction=AI_INSTRUCTIONS["invalid_expiry"],
                    review_lens=REVIEW_LENS,
                )
            )
        elif expiry_date is not None and expiry_date < date.today():
            hints.append(
                RiskHint(
                    file=finding.relative_path.as_posix(),
                    symbol="(shim)",
                    risk_type="compatibility_shim",
                    severity="high",
                    signals=[f"shim expiry `{expiry}` is already in the past"],
                    ai_instruction=AI_INSTRUCTIONS["expired_shim"],
                    review_lens=REVIEW_LENS,
                )
            )
    target = str(finding.metadata.get("target") or "").strip()
    if target and _target_path(repo_root, target) is None:
        hints.append(
            RiskHint(
                file=finding.relative_path.as_posix(),
                symbol="(shim)",
                risk_type="compatibility_shim",
                severity="medium",
                signals=[f"`shim-target` does not resolve to a live repo path: `{target}`"],
                ai_instruction=AI_INSTRUCTIONS["unresolved_target"],
                review_lens=REVIEW_LENS,
            )
        )
    return hints


__all__ = [
    "AI_INSTRUCTIONS",
    "REVIEW_LENS",
    "build_file_level_hints",
    "build_heavy_family_hint",
    "build_heavy_root_hint",
    "build_missing_metadata_hint",
    "build_temporary_repo_callers_hint",
    "build_temporary_unused_hint",
]
