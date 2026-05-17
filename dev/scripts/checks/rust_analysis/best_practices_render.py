"""Rendering helpers for the Rust best-practices guard."""

from __future__ import annotations

METRIC_KEYS = (
    "allow_without_reason",
    "undocumented_unsafe_blocks",
    "pub_unsafe_fn_missing_safety_docs",
    "unsafe_impl_missing_safety_comment",
    "mem_forget_calls",
    "result_string_types",
    "expect_on_join_recv",
    "unwrap_on_join_recv",
    "dropped_send_results",
    "dropped_emit_results",
    "detached_thread_spawns",
    "env_mutation_calls",
    "suspicious_open_options",
    "float_literal_comparisons",
    "nonatomic_persistent_toml_writes",
    "custom_persistent_toml_parsers",
)


def format_aggregate_growth(totals: dict[str, int]) -> str:
    return ", ".join(
        f"{metric} {totals[f'{metric}_growth']:+d}"
        for metric in METRIC_KEYS
    )


def format_violation_growth(item: dict) -> str:
    parts: list[str] = []
    for metric in METRIC_KEYS:
        growth = item["growth"][metric]
        base = item["base"][metric]
        current = item["current"][metric]
        parts.append(f"{metric} {base} -> {current} ({growth:+d})")
    return ", ".join(parts)
