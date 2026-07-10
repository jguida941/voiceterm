"""Focused tests for scope-path claim extraction from freeform text."""

from __future__ import annotations

from dev.scripts.devctl.runtime.scope_path_claims import (
    extract_scope_paths,
    normalize_scope_path,
    path_matches_scope_claim,
)


def test_extract_scope_paths_recognizes_jsonl_extension() -> None:
    text = "Scope: dev/state/plan_index.jsonl plus dev/active/MASTER_PLAN.md"
    paths = extract_scope_paths(text)
    assert "dev/state/plan_index.jsonl" in paths
    assert "dev/active/MASTER_PLAN.md" in paths


def test_extract_scope_paths_recognizes_json_extension() -> None:
    text = "Generated artifact dev/reports/governance/plan_registry.json refresh."
    paths = extract_scope_paths(text)
    assert "dev/reports/governance/plan_registry.json" in paths


def test_extract_scope_paths_handles_mixed_jsonl_and_json() -> None:
    text = (
        "Touched dev/state/plan_index.jsonl, dev/reports/governance/plan_registry.json, "
        "and dev/guides/SYSTEM_MAP.md."
    )
    paths = extract_scope_paths(text)
    assert "dev/state/plan_index.jsonl" in paths
    assert "dev/reports/governance/plan_registry.json" in paths
    assert "dev/guides/SYSTEM_MAP.md" in paths


def test_extract_scope_paths_dedupes_repeated_paths() -> None:
    text = (
        "First mention dev/state/plan_index.jsonl. "
        "Second mention dev/state/plan_index.jsonl in same body."
    )
    paths = extract_scope_paths(text)
    assert paths.count("dev/state/plan_index.jsonl") == 1


def test_path_matches_scope_claim_accepts_jsonl_via_extracted_scope() -> None:
    instruction = "Update dev/state/plan_index.jsonl as part of typed plan refresh."
    scope = extract_scope_paths(instruction)
    assert path_matches_scope_claim("dev/state/plan_index.jsonl", scope)


def test_normalize_scope_path_strips_dot_slash_prefix_for_jsonl() -> None:
    assert normalize_scope_path("./dev/state/plan_index.jsonl") == "dev/state/plan_index.jsonl"
