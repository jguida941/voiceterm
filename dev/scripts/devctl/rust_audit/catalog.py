"""Static category and guard metadata for Rust audit reporting."""

from __future__ import annotations

from typing import Any


RUST_AUDIT_CATEGORY_INFO: dict[str, dict[str, str | int]] = {
    "allow_without_reason": {
        "guard": "best_practices",
        "label": "allow attrs without reason",
        "severity": "medium",
        "weight": 2,
        "why": "Suppressions without rationale hide debt, ownership, and exit criteria.",
        "fix": "Add `reason=` metadata or remove the suppression.",
    },
    "undocumented_unsafe_blocks": {
        "guard": "best_practices",
        "label": "undocumented unsafe blocks",
        "severity": "high",
        "weight": 3,
        "why": "Unsafe code without nearby safety notes makes invariants hard to review and easy to break.",
        "fix": "Add a nearby `SAFETY:` comment describing the required invariants.",
    },
    "pub_unsafe_fn_missing_safety_docs": {
        "guard": "best_practices",
        "label": "unsafe fns missing safety docs",
        "severity": "high",
        "weight": 3,
        "why": "Callers need an explicit `# Safety` contract to use public unsafe APIs correctly.",
        "fix": "Document caller obligations with a `# Safety` section.",
    },
    "unsafe_impl_missing_safety_comment": {
        "guard": "best_practices",
        "label": "unsafe impls missing safety rationale",
        "severity": "high",
        "weight": 3,
        "why": "Unsafe trait impls encode invariants that are otherwise invisible during review.",
        "fix": "Add a nearby safety comment explaining why the impl is sound.",
    },
    "mem_forget_calls": {
        "guard": "best_practices",
        "label": "mem::forget calls",
        "severity": "high",
        "weight": 3,
        "why": "Forgetting values skips `Drop`, which can leak resources or bypass cleanup invariants.",
        "fix": "Prefer explicit ownership transfer or `ManuallyDrop` with documented constraints.",
    },
    "result_string_types": {
        "guard": "best_practices",
        "label": "Result<_, String> surfaces",
        "severity": "medium",
        "weight": 2,
        "why": "Stringly typed errors lose structure, make matching brittle, and weaken API contracts.",
        "fix": "Use a typed error enum or a structured error type.",
    },
    "expect_on_join_recv": {
        "guard": "best_practices",
        "label": "expect on join/recv",
        "severity": "high",
        "weight": 3,
        "why": "Coordination failures should surface as typed shutdown/error paths, not surprise panics.",
        "fix": "Handle the error explicitly and propagate or log the failure.",
    },
    "unwrap_on_join_recv": {
        "guard": "best_practices",
        "label": "unwrap on join/recv",
        "severity": "high",
        "weight": 3,
        "why": "Unchecked synchronization failures turn routine edge cases into runtime crashes.",
        "fix": "Match on the result and preserve shutdown/error intent.",
    },
    "dropped_send_results": {
        "guard": "best_practices",
        "label": "dropped send results",
        "severity": "high",
        "weight": 3,
        "why": "Ignoring channel-send results can silently lose cancellation, shutdown, or state-update signals.",
        "fix": "Handle `send` failure explicitly and decide whether it is expected or a bug.",
    },
    "env_mutation_calls": {
        "guard": "best_practices",
        "label": "env mutation calls",
        "severity": "medium",
        "weight": 2,
        "why": "Global environment mutation creates hidden coupling across runtime code and tests.",
        "fix": "Isolate the change behind a guarded helper or move it to startup/test scaffolding.",
    },
    "allow_attrs": {
        "guard": "lint_debt",
        "label": "allow attrs",
        "severity": "medium",
        "weight": 2,
        "why": "Broad lint suppression reduces compiler signal and lets debt accumulate quietly.",
        "fix": "Remove the suppression or narrow it to the exact temporary exception.",
    },
    "dead_code_allow_attrs": {
        "guard": "lint_debt",
        "label": "dead_code allows",
        "severity": "medium",
        "weight": 2,
        "why": "Dead-code suppressions often hide stale APIs, test scaffolding drift, or ownership confusion.",
        "fix": "Delete unused code or document why the preserved surface is intentional.",
    },
    "unwrap_expect_calls": {
        "guard": "lint_debt",
        "label": "unwrap/expect calls",
        "severity": "high",
        "weight": 3,
        "why": "Unchecked failure paths turn recoverable errors into runtime aborts.",
        "fix": "Replace with typed error handling or explicit invariants with rationale.",
    },
    "unchecked_unwrap_expect_calls": {
        "guard": "lint_debt",
        "label": "unchecked unwrap/expect",
        "severity": "high",
        "weight": 3,
        "why": "Unchecked unwrap variants bypass safety checks and can create undefined behavior.",
        "fix": "Use checked handling or prove and document the invariant locally.",
    },
    "panic_macro_calls": {
        "guard": "lint_debt",
        "label": "panic! calls",
        "severity": "high",
        "weight": 3,
        "why": "Runtime panics abort control flow abruptly and complicate recovery and operator diagnosis.",
        "fix": "Prefer typed errors or explicitly allowlist the panic with rationale if truly required.",
    },
    "unallowlisted_panic_calls": {
        "guard": "runtime_panic_policy",
        "label": "unallowlisted runtime panic! calls",
        "severity": "high",
        "weight": 3,
        "why": "New runtime panic paths should be intentional and documented because they are user-visible crash behavior.",
        "fix": "Add typed recovery or a nearby `panic-policy: allow reason=...` comment.",
    },
}

RUST_AUDIT_GUARDS: dict[str, dict[str, Any]] = {
    "best_practices": {
        "script": "dev/scripts/checks/check_rust_best_practices.py",
        "categories": (
            "allow_without_reason",
            "undocumented_unsafe_blocks",
            "pub_unsafe_fn_missing_safety_docs",
            "unsafe_impl_missing_safety_comment",
            "mem_forget_calls",
            "result_string_types",
            "expect_on_join_recv",
            "unwrap_on_join_recv",
            "dropped_send_results",
            "env_mutation_calls",
        ),
    },
    "lint_debt": {
        "script": "dev/scripts/checks/check_rust_lint_debt.py",
        "categories": (
            "allow_attrs",
            "dead_code_allow_attrs",
            "unwrap_expect_calls",
            "unchecked_unwrap_expect_calls",
            "panic_macro_calls",
        ),
    },
    "runtime_panic_policy": {
        "script": "dev/scripts/checks/check_rust_runtime_panic_policy.py",
        "categories": ("unallowlisted_panic_calls",),
    },
}
