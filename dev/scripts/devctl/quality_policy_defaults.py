"""Built-in quality-step capability registry used by repo policies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QualityStepSpec:
    """One built-in quality step plus its repo-policy metadata."""

    step_name: str
    script_id: str
    extra_args: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    supports_commit_range: bool = True


DEFAULT_AI_GUARD_SPECS = (
    QualityStepSpec("code-shape-guard", "code_shape", languages=("python", "rust")),
    QualityStepSpec("package-layout-guard", "package_layout"),
    QualityStepSpec(
        "python-broad-except-guard",
        "python_broad_except",
        languages=("python",),
    ),
    QualityStepSpec(
        "python-subprocess-policy-guard",
        "python_subprocess_policy",
        languages=("python",),
    ),
    QualityStepSpec(
        "command-source-validation-guard",
        "command_source_validation",
        languages=("python",),
    ),
    QualityStepSpec("duplicate-types-guard", "duplicate_types", languages=("rust",)),
    QualityStepSpec(
        "structural-complexity-guard",
        "structural_complexity",
        languages=("rust",),
    ),
    QualityStepSpec("rust-test-shape-guard", "rust_test_shape", languages=("rust",)),
    QualityStepSpec(
        "ide-provider-isolation-guard",
        "ide_provider_isolation",
        extra_args=("--fail-on-violations",),
        supports_commit_range=False,
    ),
    QualityStepSpec(
        "compat-matrix-guard",
        "compat_matrix",
        supports_commit_range=False,
    ),
    QualityStepSpec(
        "compat-matrix-smoke-guard",
        "compat_matrix_smoke",
        supports_commit_range=False,
    ),
    QualityStepSpec(
        "naming-consistency-guard",
        "naming_consistency",
        supports_commit_range=False,
    ),
    QualityStepSpec(
        "rust-lint-debt-guard",
        "rust_lint_debt",
        extra_args=("--report-dead-code", "--dead-code-report-limit", "120"),
        languages=("rust",),
    ),
    QualityStepSpec(
        "rust-best-practices-guard",
        "rust_best_practices",
        languages=("rust",),
    ),
    QualityStepSpec(
        "serde-compatibility-guard",
        "serde_compatibility",
        languages=("rust",),
    ),
    QualityStepSpec(
        "rust-runtime-panic-policy-guard",
        "rust_runtime_panic_policy",
        languages=("rust",),
    ),
    QualityStepSpec(
        "rust-audit-patterns-guard",
        "rust_audit_patterns",
        languages=("rust",),
    ),
    QualityStepSpec(
        "rust-security-footguns-guard",
        "rust_security_footguns",
        languages=("rust",),
    ),
    QualityStepSpec(
        "function-duplication-guard",
        "function_duplication",
        languages=("python", "rust"),
    ),
    QualityStepSpec("god-class-guard", "god_class", languages=("python", "rust")),
    QualityStepSpec(
        "nesting-depth-guard",
        "nesting_depth",
        languages=("python", "rust"),
    ),
    QualityStepSpec(
        "parameter-count-guard",
        "parameter_count",
        languages=("python", "rust"),
    ),
    QualityStepSpec(
        "python-dict-schema-guard",
        "python_dict_schema",
        languages=("python",),
    ),
    QualityStepSpec(
        "python-global-mutable-guard",
        "python_global_mutable",
        languages=("python",),
    ),
    QualityStepSpec(
        "python-design-complexity-guard",
        "python_design_complexity",
        languages=("python",),
    ),
    QualityStepSpec(
        "python-cyclic-imports-guard",
        "python_cyclic_imports",
        languages=("python",),
    ),
    QualityStepSpec(
        "python-suppression-debt-guard",
        "python_suppression_debt",
        languages=("python",),
    ),
    QualityStepSpec(
        "structural-similarity-guard",
        "structural_similarity",
        languages=("python", "rust"),
    ),
    QualityStepSpec(
        "facade-wrappers-guard",
        "facade_wrappers",
        languages=("python",),
    ),
)

DEFAULT_REVIEW_PROBE_SPECS = (
    QualityStepSpec("probe-concurrency", "probe_concurrency", languages=("rust",)),
    QualityStepSpec(
        "probe-design-smells",
        "probe_design_smells",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-boolean-params",
        "probe_boolean_params",
        languages=("python", "rust"),
    ),
    QualityStepSpec(
        "probe-stringly-typed",
        "probe_stringly_typed",
        languages=("python", "rust"),
    ),
    QualityStepSpec(
        "probe-unwrap-chains",
        "probe_unwrap_chains",
        languages=("rust",),
    ),
    QualityStepSpec(
        "probe-clone-density",
        "probe_clone_density",
        languages=("rust",),
    ),
    QualityStepSpec(
        "probe-type-conversions",
        "probe_type_conversions",
        languages=("rust",),
    ),
    QualityStepSpec(
        "probe-magic-numbers",
        "probe_magic_numbers",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-dict-as-struct",
        "probe_dict_as_struct",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-unnecessary-intermediates",
        "probe_unnecessary_intermediates",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-vague-errors",
        "probe_vague_errors",
        languages=("rust",),
    ),
    QualityStepSpec(
        "probe-defensive-overchecking",
        "probe_defensive_overchecking",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-single-use-helpers",
        "probe_single_use_helpers",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-exception-quality",
        "probe_exception_quality",
        languages=("python",),
    ),
    QualityStepSpec(
        "probe-compatibility-shims",
        "probe_compatibility_shims",
        languages=("python",),
    ),
)

AI_GUARD_REGISTRY = {spec.script_id: spec for spec in DEFAULT_AI_GUARD_SPECS}
REVIEW_PROBE_REGISTRY = {spec.script_id: spec for spec in DEFAULT_REVIEW_PROBE_SPECS}
VOICETERM_ONLY_AI_GUARD_IDS = (
    "ide_provider_isolation",
    "compat_matrix",
    "compat_matrix_smoke",
    "naming_consistency",
)


def _build_default_checks(
    enabled_ids: tuple[str, ...],
    registry: dict[str, QualityStepSpec],
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    return tuple(
        (
            registry[script_id].step_name,
            script_id,
            registry[script_id].extra_args,
        )
        for script_id in enabled_ids
        if script_id in registry
    )


# The engine-level fallback must stay portable. VoiceTerm-only matrix/isolation
# guards are enabled through repo presets instead of leaking into every repo that
# adopts the quality-policy resolver.
DEFAULT_ENABLED_AI_GUARD_IDS = tuple(
    spec.script_id for spec in DEFAULT_AI_GUARD_SPECS if spec.script_id not in VOICETERM_ONLY_AI_GUARD_IDS
)
DEFAULT_ENABLED_REVIEW_PROBE_IDS = tuple(spec.script_id for spec in DEFAULT_REVIEW_PROBE_SPECS)
DEFAULT_AI_GUARD_CHECKS = _build_default_checks(
    DEFAULT_ENABLED_AI_GUARD_IDS,
    AI_GUARD_REGISTRY,
)
DEFAULT_REVIEW_PROBE_CHECKS = _build_default_checks(
    DEFAULT_ENABLED_REVIEW_PROBE_IDS,
    REVIEW_PROBE_REGISTRY,
)
