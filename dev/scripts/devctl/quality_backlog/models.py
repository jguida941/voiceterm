"""Typed row models and scoring tables for quality-backlog reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AbsoluteCheck:
    key: str
    script: str


@dataclass(slots=True)
class InventoryRow:
    path: str
    language: str
    line_count: int
    soft_limit: int
    hard_limit: int
    pressure_pct: float
    status: str
    score: int
    policy_source: str | None

    def to_dict(self) -> dict[str, Any]:
        return dict(
            path=self.path,
            language=self.language,
            line_count=self.line_count,
            soft_limit=self.soft_limit,
            hard_limit=self.hard_limit,
            pressure_pct=self.pressure_pct,
            status=self.status,
            score=self.score,
            policy_source=self.policy_source,
        )


@dataclass(slots=True)
class CheckExecution:
    key: str
    command: str
    exit_code: int
    ok: bool
    stderr: str
    parse_error: str
    report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(
            command=self.command,
            exit_code=self.exit_code,
            ok=self.ok,
            stderr=self.stderr,
            parse_error=self.parse_error,
            report=self.report,
        )


@dataclass(slots=True)
class PriorityRow:
    path: str
    language: str
    score: int = 0
    signals: set[str] = field(default_factory=set)
    suggested_fixes: set[str] = field(default_factory=set)
    severity: str = "low"

    def add_signal(
        self,
        *,
        signal: str,
        score: int,
        suggestions: tuple[tuple[str, str], ...],
    ) -> None:
        self.score += score
        self.signals.add(signal)
        for prefix, suggestion in suggestions:
            if signal.startswith(prefix):
                self.suggested_fixes.add(suggestion)

    def finalize(self) -> None:
        self.severity = severity_from_score(self.score)

    def to_dict(self) -> dict[str, Any]:
        return dict(
            path=self.path,
            language=self.language,
            score=self.score,
            severity=self.severity,
            signals=sorted(self.signals),
            suggested_fixes=sorted(self.suggested_fixes),
        )


ABSOLUTE_CHECKS: tuple[AbsoluteCheck, ...] = (
    AbsoluteCheck("code_shape", "dev/scripts/checks/check_code_shape.py"),
    AbsoluteCheck("rust_lint_debt", "dev/scripts/checks/check_rust_lint_debt.py"),
    AbsoluteCheck("rust_best_practices", "dev/scripts/checks/check_rust_best_practices.py"),
    AbsoluteCheck(
        "rust_runtime_panic_policy",
        "dev/scripts/checks/check_rust_runtime_panic_policy.py",
    ),
    AbsoluteCheck(
        "rust_compiler_warnings",
        "dev/scripts/checks/check_rust_compiler_warnings.py",
    ),
    AbsoluteCheck(
        "structural_similarity",
        "dev/scripts/checks/check_structural_similarity.py",
    ),
    AbsoluteCheck(
        "facade_wrappers",
        "dev/scripts/checks/check_facade_wrappers.py",
    ),
    AbsoluteCheck(
        "serde_compatibility",
        "dev/scripts/checks/check_serde_compatibility.py",
    ),
    AbsoluteCheck(
        "function_duplication",
        "dev/scripts/checks/check_function_duplication.py",
    ),
    AbsoluteCheck(
        "rust_security_footguns",
        "dev/scripts/checks/check_rust_security_footguns.py",
    ),
)

CODE_SHAPE_REASON_WEIGHTS: dict[str, int] = dict(
    absolute_hard_limit_exceeded=520,
    crossed_hard_limit=460,
    hard_locked_file_grew=420,
    new_file_exceeds_soft_limit=320,
    crossed_soft_limit=280,
    oversize_file_growth_exceeded_budget=240,
    function_exceeds_max_lines=240,
    stale_path_override_below_default_soft_limit=180,
)

RUST_BEST_PRACTICE_WEIGHTS: dict[str, int] = dict(
    allow_without_reason=180,
    undocumented_unsafe_blocks=320,
    pub_unsafe_fn_missing_safety_docs=300,
    unsafe_impl_missing_safety_comment=240,
    mem_forget_calls=260,
    result_string_types=160,
    expect_on_join_recv=190,
    unwrap_on_join_recv=190,
    dropped_send_results=230,
    dropped_emit_results=230,
    detached_thread_spawns=170,
    env_mutation_calls=180,
    suspicious_open_options=180,
    float_literal_comparisons=120,
    nonatomic_persistent_toml_writes=200,
    custom_persistent_toml_parsers=180,
)

LINT_DEBT_WEIGHTS: dict[str, int] = dict(
    allow_attrs_growth=140,
    dead_code_allow_attrs_growth=100,
    unwrap_expect_calls_growth=180,
    unchecked_unwrap_expect_calls_growth=200,
    panic_macro_calls_growth=220,
)

COMPILER_WARNING_WEIGHTS: dict[str, int] = dict(
    unused_imports=40,
    deprecated=70,
)

STRUCTURAL_SIMILARITY_WEIGHTS: dict[str, int] = dict(
    cross_file_similar_pairs_growth=280,
)

FACADE_WRAPPER_WEIGHTS: dict[str, int] = dict(
    facade_heavy_module_growth=220,
    facade_wrapper_growth=160,
)

SERDE_COMPATIBILITY_WEIGHTS: dict[str, int] = dict(
    serde_deserialize_enum_missing_allow_growth=340,
)

FUNCTION_DUPLICATION_WEIGHTS: dict[str, int] = dict(
    duplicate_function_body_growth=300,
)

SECURITY_FOOTGUN_WEIGHTS: dict[str, int] = dict(
    footgun_growth=360,
)

SUGGESTIONS_BY_SIGNAL_PREFIX: tuple[tuple[str, str], ...] = (
    (
        "shape:hard",
        "Split oversized file into focused modules and move unrelated responsibilities out.",
    ),
    (
        "shape:soft",
        "Decompose module before more feature work; keep one responsibility per file.",
    ),
    (
        "code_shape:function_exceeds_max_lines",
        "Split long functions into named helper functions with explicit intent.",
    ),
    (
        "rust_best:result_string_types",
        "Replace `Result<_, String>` with typed errors and structured context.",
    ),
    (
        "rust_panic:unallowlisted_panic_calls",
        "Replace runtime `panic!` paths with typed error handling or explicit allow rationale.",
    ),
    (
        "rust_warning:unused_imports",
        "Remove unused imports and dead re-exports to keep modules easy to review.",
    ),
    (
        "rust_warning:deprecated",
        "Migrate deprecated APIs to supported equivalents before they spread.",
    ),
    (
        "structural_similarity",
        "Extract shared logic into a common helper to eliminate control-flow duplication.",
    ),
    (
        "facade_wrappers",
        "Collapse pass-through wrapper chains; callers should use the real module directly.",
    ),
    (
        "serde_compat",
        "Add #[serde(deny_unknown_fields)] or allow policy to protect deserialization stability.",
    ),
    (
        "function_dup",
        "Extract identical function bodies into a shared module to avoid maintenance drift.",
    ),
    (
        "security_footgun",
        "Replace dangerous patterns with safe alternatives documented in AGENTS.md.",
    ),
)


def severity_from_score(score: int) -> str:
    if score >= 700:
        return "critical"
    if score >= 350:
        return "high"
    if score >= 140:
        return "medium"
    return "low"
