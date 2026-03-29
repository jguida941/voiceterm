"""Override-cap support helpers for check_code_shape."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

OVERRIDE_CAP_RATIO_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class DocsContext:
    """Grouped best-practice docs and audit guidance for override-cap rendering."""

    best_practice_docs: dict[str, tuple[str, ...]]
    shape_audit_guidance: str


def guidance_with_docs(
    *,
    path: Path,
    guidance: str,
    docs: DocsContext,
) -> tuple[str, list[str]]:
    docs_refs = list(docs.best_practice_docs.get(path.suffix, ()))
    guidance_parts = [guidance, docs.shape_audit_guidance]
    if docs_refs:
        guidance_parts.append("Best-practice refs: " + ", ".join(docs_refs))
    return " ".join(guidance_parts), docs_refs


def override_cap_violation(
    *,
    path: Path,
    reason: str,
    guidance: str,
    current_record: dict[str, object],
    baseline_record: dict[str, object] | None,
    docs: DocsContext,
) -> dict[str, object]:
    full_guidance, docs_refs = guidance_with_docs(
        path=path,
        guidance=guidance,
        docs=docs,
    )
    return {
        "path": path.as_posix(),
        "violation_family": "override_cap",
        "reason": reason,
        "guidance": full_guidance,
        "best_practice_refs": docs_refs,
        "policy_source": f"path_override:{path.as_posix()}",
        "current_override_soft": current_record["override_soft"],
        "current_override_hard": current_record["override_hard"],
        "current_language_soft": current_record["language_soft"],
        "current_language_hard": current_record["language_hard"],
        "current_soft_ratio": current_record["soft_ratio"],
        "current_hard_ratio": current_record["hard_ratio"],
        "current_triggered_caps": list(current_record.get("triggered_caps", [])),
        "baseline_override_soft": None
        if baseline_record is None
        else baseline_record["override_soft"],
        "baseline_override_hard": None
        if baseline_record is None
        else baseline_record["override_hard"],
        "baseline_soft_ratio": None
        if baseline_record is None
        else baseline_record["soft_ratio"],
        "baseline_hard_ratio": None
        if baseline_record is None
        else baseline_record["hard_ratio"],
        "baseline_triggered_caps": []
        if baseline_record is None
        else list(baseline_record.get("triggered_caps", [])),
    }


def load_override_cap_baseline_records(
    *,
    ref: str | None,
    repo_root: Path,
    policy_path: Path,
    read_text_from_ref,
    collect_override_cap_records,
) -> list[dict[str, object]]:
    """Load override-cap records from the policy file at one git ref."""
    if not ref:
        return []
    source = read_text_from_ref(policy_path, ref)
    if source is None:
        return []

    namespace: dict[str, object] = {
        "__file__": str(repo_root / policy_path),
        "__name__": f"_code_shape_policy_snapshot_{ref.replace('/', '_')}",
    }
    exec(compile(source, str(policy_path), "exec"), namespace)
    overrides = namespace.get("PATH_POLICY_OVERRIDES")
    language_policies = namespace.get("LANGUAGE_POLICIES")
    if not isinstance(overrides, dict) or not isinstance(language_policies, dict):
        return []
    return collect_override_cap_records(
        overrides=overrides,
        language_policies=language_policies,
    )


def evaluate_override_cap_violations(
    *,
    mode: str,
    changed_paths: list[Path],
    current_records: list[dict[str, object]],
    baseline_records: list[dict[str, object]],
    docs: DocsContext,
) -> list[dict[str, object]]:
    """Fail on touched, new, or worsened over-cap overrides."""
    if mode == "absolute":
        return []

    changed_path_strs = {path.as_posix() for path in changed_paths}
    baseline_by_path = {
        str(record["path"]): record for record in baseline_records
    }
    violations: list[dict[str, object]] = []
    seen_paths: set[str] = set()

    for record in current_records:
        path_str = str(record["path"])
        if path_str in seen_paths:
            continue
        path = Path(path_str)
        baseline_record = baseline_by_path.get(path_str)

        if path_str in changed_path_strs:
            violations.append(
                override_cap_violation(
                    path=path,
                    reason="override_cap_exceeded_on_touched_file",
                    guidance=(
                        "Touched file still depends on a path override that exceeds the "
                        "operator cap. Split the file or lower the override before merge."
                    ),
                    current_record=record,
                    baseline_record=baseline_record,
                    docs=docs,
                )
            )
            seen_paths.add(path_str)
            continue

        if baseline_record is None:
            violations.append(
                override_cap_violation(
                    path=path,
                    reason="override_cap_new_above_threshold",
                    guidance=(
                        "New PATH_POLICY_OVERRIDES entry exceeds the operator cap. "
                        "Lower the override or modularize the target file before merge."
                    ),
                    current_record=record,
                    baseline_record=None,
                    docs=docs,
                )
            )
            seen_paths.add(path_str)
            continue

        current_caps = set(record.get("triggered_caps", []))
        baseline_caps = set(baseline_record.get("triggered_caps", []))
        if current_caps - baseline_caps:
            violations.append(
                override_cap_violation(
                    path=path,
                    reason="override_cap_crossed_threshold",
                    guidance=(
                        "Override now crosses an operator cap that the baseline policy "
                        "did not cross. Revert the expansion or modularize first."
                    ),
                    current_record=record,
                    baseline_record=baseline_record,
                    docs=docs,
                )
            )
            seen_paths.add(path_str)
            continue

        soft_worsened = (
            float(record["soft_ratio"])
            > float(baseline_record["soft_ratio"]) + OVERRIDE_CAP_RATIO_EPSILON
        )
        hard_worsened = (
            float(record["hard_ratio"])
            > float(baseline_record["hard_ratio"]) + OVERRIDE_CAP_RATIO_EPSILON
        )
        if soft_worsened or hard_worsened:
            violations.append(
                override_cap_violation(
                    path=path,
                    reason="override_cap_ratio_worsened",
                    guidance=(
                        "Override cap debt got worse relative to the baseline policy. "
                        "Do not widen over-cap budgets; reduce them or modularize first."
                    ),
                    current_record=record,
                    baseline_record=baseline_record,
                    docs=docs,
                )
            )
            seen_paths.add(path_str)

    return violations
