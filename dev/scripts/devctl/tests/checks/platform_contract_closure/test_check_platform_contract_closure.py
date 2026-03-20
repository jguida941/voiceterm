"""Tests for the platform contract-closure guard."""

from __future__ import annotations

from unittest.mock import patch

from dev.scripts.checks.platform_contract_closure.report import build_report, render_md
from dev.scripts.checks.platform_contract_closure.emitter_parity import (
    check_review_state_emitter_parity as _check_review_state_emitter_parity,
)
from dev.scripts.checks.platform_contract_closure.support import (
    evaluate_platform_contract_closure,
)
from dev.scripts.devctl.governance.surfaces import (
    RepoPackMetadata,
    SurfacePolicy,
    SurfaceSpec,
)
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint
from dev.scripts.devctl.tests.checks.platform_contract_test_support import (
    drop_contract_field,
    rewrite_artifact_schema,
)


def _surface_policy_with_tokens(*tokens: str) -> SurfacePolicy:
    joined = "\n".join(tokens)
    return SurfacePolicy(
        policy_path="dev/config/devctl_repo_policy.json",
        warnings=(),
        metadata=RepoPackMetadata(
            pack_id="voiceterm",
            pack_version="0.1.0-dev",
            product_name="VoiceTerm",
            repo_name="codex-voice",
        ),
        context={"key_commands_block": joined},
        surfaces=(
            SurfaceSpec(
                surface_id="claude_instructions",
                surface_type="local_instructions",
                renderer="template_file",
                output_path="CLAUDE.md",
                template_path="dev/config/templates/claude_instructions.template.md",
                tracked=False,
                local_only=True,
                description="Local instructions",
                required_contains=tokens,
            ),
        ),
    )

def test_platform_contract_closure_passes_on_current_blueprint() -> None:
    report = build_report()
    assert report["ok"] is True
    assert report["violations"] == []


def test_platform_contract_closure_flags_runtime_field_drift() -> None:
    blueprint = drop_contract_field("DecisionPacket", "validation_plan")
    coverage, violations = evaluate_platform_contract_closure(
        blueprint,
        _surface_policy_with_tokens(
            "platform-contracts",
            "render-surfaces",
            "check_platform_contract_closure.py",
        ),
    )
    assert len(coverage) >= 1
    drift_violations = [v for v in violations if v.get("rule") == "runtime-field-drift"]
    assert len(drift_violations) == 1
    assert drift_violations[0]["contract_id"] == "DecisionPacket"
    assert drift_violations[0]["extra_fields"] == ("validation_plan",)


def test_platform_contract_closure_flags_artifact_schema_drift() -> None:
    blueprint = rewrite_artifact_schema("ProbeReport", schema_version=9)
    _coverage, violations = evaluate_platform_contract_closure(
        blueprint,
        _surface_policy_with_tokens(
            "platform-contracts",
            "render-surfaces",
            "check_platform_contract_closure.py",
        ),
    )
    schema_violations = [v for v in violations if v.get("rule") == "artifact-schema-drift"]
    assert len(schema_violations) == 1
    assert schema_violations[0]["contract_id"] == "ProbeReport"


def test_platform_contract_closure_flags_missing_startup_surface_token() -> None:
    blueprint = build_platform_blueprint()
    _coverage, violations = evaluate_platform_contract_closure(
        blueprint,
        _surface_policy_with_tokens("platform-contracts"),
    )
    surface_violations = [v for v in violations if v.get("rule") == "missing-startup-surface-token"]
    assert len(surface_violations) == 1
    assert "check_platform_contract_closure.py" in surface_violations[0]["missing_tokens"]


def test_emitter_parity_catches_missing_bridge_state_key() -> None:
    """Guard must fail if event-backed bridge_state drops a ReviewBridgeState field."""
    from dev.scripts.devctl.review_channel import event_projection

    original = event_projection._build_event_bridge_state

    def _drop_ack_current(*, review_state: dict[str, object], bridge_liveness: dict[str, object]) -> dict[str, object]:
        bridge_state = dict(
            original(review_state=review_state, bridge_liveness=bridge_liveness)
        )
        del bridge_state["claude_ack_current"]
        return bridge_state

    with patch.object(event_projection, "_build_event_bridge_state", _drop_ack_current):
        results = _check_review_state_emitter_parity()

    violation = next(
        violation
        for coverage, violation in results
        if coverage["check"] == "bridge_state_keys"
    )
    assert violation is not None
    assert violation["rule"] == "emitter-field-gap"
    assert "claude_ack_current" in violation["detail"]


def test_emitter_parity_catches_type_drift() -> None:
    """Guard must fail if a bridge_state field has the wrong type."""
    from dev.scripts.devctl.review_channel import event_projection

    original = event_projection._build_event_bridge_state

    def _type_drift(*, review_state: dict[str, object], bridge_liveness: dict[str, object]) -> dict[str, object]:
        bridge_state = dict(
            original(review_state=review_state, bridge_liveness=bridge_liveness)
        )
        bridge_state["last_codex_poll_age_seconds"] = 0.5
        return bridge_state

    with patch.object(event_projection, "_build_event_bridge_state", _type_drift):
        results = _check_review_state_emitter_parity()

    violation = next(
        violation
        for coverage, violation in results
        if coverage["check"] == "bridge_state_types"
    )
    assert violation is not None
    assert violation["rule"] == "emitter-type-drift"
    assert "last_codex_poll_age_seconds" in violation["detail"]


def test_emitter_parity_catches_compat_gap() -> None:
    """Guard must fail if _compat is missing a transitional key."""
    from dev.scripts.devctl.review_channel import event_projection

    original = event_projection.enrich_event_review_state

    def _compat_gap(**kwargs: object) -> tuple[dict[str, object], dict[str, object]]:
        enriched, extras = original(**kwargs)
        broken = dict(enriched)
        compat = dict(broken["_compat"])
        compat.pop("service_identity")
        broken["_compat"] = compat
        return broken, extras

    with patch.object(event_projection, "enrich_event_review_state", _compat_gap):
        results = _check_review_state_emitter_parity()

    violation = next(
        violation
        for coverage, violation in results
        if coverage["check"] == "compat_field_coverage"
    )
    assert violation is not None
    assert violation["rule"] == "compat-field-gap"
    assert "service_identity" in violation["detail"]


def test_emitted_artifact_review_state_matches_contract() -> None:
    """End-to-end: write projection bundle, read back, validate contract fields."""
    import json
    import tempfile
    from dataclasses import fields as dc_fields
    from pathlib import Path

    from dev.scripts.checks.platform_contract_closure.emitter_parity import (
        _build_synthetic_review_state,
        _BRIDGE_STATE_EXPECTED_TYPES,
    )
    from dev.scripts.devctl.review_channel.event_projection import (
        _build_event_bridge_liveness,
        _build_event_bridge_state,
    )
    from dev.scripts.devctl.review_channel.projection_bundle import (
        write_projection_bundle,
    )
    from dev.scripts.devctl.runtime.review_state_models import ReviewBridgeState

    synthetic = _build_synthetic_review_state()
    liveness = _build_event_bridge_liveness(synthetic)
    bridge_state = _build_event_bridge_state(
        review_state=synthetic, bridge_liveness=liveness,
    )
    synthetic["bridge"] = bridge_state

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_root = Path(tmp_dir) / "projections"
        output_root.mkdir()
        write_projection_bundle(
            output_root=output_root,
            review_state=synthetic,
            agent_registry={"timestamp": "", "agents": []},
            action="status",
        )

        # Read back the artifact
        on_disk = json.loads(
            (output_root / "review_state.json").read_text(encoding="utf-8")
        )

    # Validate bridge contract fields on the artifact
    contract_fields = {f.name for f in dc_fields(ReviewBridgeState)}
    artifact_bridge = on_disk.get("bridge", {})
    assert isinstance(artifact_bridge, dict), "bridge must be a dict on disk"
    missing = sorted(contract_fields - set(artifact_bridge.keys()))
    extra = sorted(set(artifact_bridge.keys()) - contract_fields)
    assert not missing, f"Artifact review_state.json bridge missing: {missing}"
    assert not extra, f"Artifact review_state.json bridge has extra: {extra}"

    # Validate types survived serialization round-trip
    for field_name, expected_type in _BRIDGE_STATE_EXPECTED_TYPES.items():
        value = artifact_bridge.get(field_name)
        if value is not None and not isinstance(value, expected_type):
            raise AssertionError(
                f"Artifact bridge.{field_name}: expected {expected_type}, "
                f"got {type(value).__name__} ({value!r})"
            )


def test_platform_contract_closure_markdown_lists_violations() -> None:
    blueprint = drop_contract_field("TypedAction", "dry_run")
    coverage, violations = evaluate_platform_contract_closure(
        blueprint,
        _surface_policy_with_tokens(
            "platform-contracts",
            "render-surfaces",
            "check_platform_contract_closure.py",
        ),
    )
    report = {
        "command": "check_platform_contract_closure",
        "ok": False,
        "checked_runtime_contracts": len(
            [row for row in coverage if row.get("kind") == "runtime_contract"]
        ),
        "checked_artifact_schemas": len(
            [row for row in coverage if row.get("kind") == "artifact_schema"]
        ),
        "violations": list(violations),
        "coverage": list(coverage),
    }
    output = render_md(report)
    assert "# check_platform_contract_closure" in output
    assert "runtime-field-drift" in output
    assert "dry_run" in output
