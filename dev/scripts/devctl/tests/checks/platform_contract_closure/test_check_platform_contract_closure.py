"""Tests for the platform contract-closure guard."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

from dev.scripts.checks.platform_contract_closure import (
    field_routes,
    field_routes_planning,
)
from dev.scripts.checks.platform_contract_closure.connectivity_registry_closure import (
    check_connectivity_registry_closure,
)
from dev.scripts.checks.platform_contract_closure.contract_registry_closure import (
    check_contract_registry_closure,
)
from dev.scripts.checks.platform_contract_closure.emitter_parity import (
    check_review_state_emitter_parity as _check_review_state_emitter_parity,
)
from dev.scripts.checks.platform_contract_closure.report import build_report, render_md
from dev.scripts.checks.platform_contract_closure.support import (
    evaluate_platform_contract_closure,
)
from dev.scripts.checks.platform_contract_closure.typed_state_writer_authority import (
    check_typed_state_writer_authority,
)
from dev.scripts.devctl.governance.surfaces import (
    RepoPackMetadata,
    SurfacePolicy,
    SurfaceSpec,
)
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint
from dev.scripts.devctl.platform.contract_registry import build_contract_registry_rows
from dev.scripts.devctl.platform.connectivity_registry_models import (
    ConnectivityContractRow,
    ConnectivityFieldRow,
    ConnectivityRegistrySnapshot,
    ConnectivityWriterRow,
)
from dev.scripts.devctl.platform.connectivity_reader_verification import (
    find_missing_connection_findings,
)
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


def _synthetic_source(tmp_path: Path, rel_path: str, source: str) -> Path:
    path = tmp_path / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).strip() + "\n", encoding="utf-8")
    return path


def test_platform_contract_closure_passes_on_current_blueprint() -> None:
    report = build_report()
    assert report["ok"] is True
    assert report["checked_field_routes"] == 18
    assert report["checked_field_route_families"] == 11
    assert report["violations"] == []


def test_typed_state_writer_authority_passes_current_repo() -> None:
    coverage, violations = check_typed_state_writer_authority()
    assert coverage["ok"] is True
    assert violations == ()


def test_platform_contract_closure_checks_connectivity_registry_consumers() -> None:
    report = build_report()
    rows = [
        row
        for row in report["coverage"]
        if row.get("kind") == "connectivity_registry_closure"
    ]

    assert len(rows) == 1
    row = rows[0]
    assert row["ok"] is True
    assert row["zero_reader_field_count"] == 0
    assert row["aspirational_gap_count"] == 0
    for reader_id in (
        "context_graph",
        "startup_context",
        "session_resume",
        "render_surfaces",
        "system_map_index",
    ):
        assert reader_id in row["observed_reader_ids"]
        assert reader_id in row["row_reader_ids"]
    assert row["reader_verification_violation_count"] == 0


def test_contract_registry_closure_flags_missing_registry_row() -> None:
    blueprint = build_platform_blueprint()
    rows = build_contract_registry_rows(blueprint)[1:]

    coverage, violations = check_contract_registry_closure(
        blueprint=blueprint,
        rows=rows,
    )

    assert coverage["ok"] is False
    assert any(
        violation["rule"] == "missing-registry-row" for violation in violations
    )


def test_contract_registry_closure_flags_stale_registry_row() -> None:
    blueprint = build_platform_blueprint()
    rows = list(build_contract_registry_rows(blueprint))
    rows[0] = replace(rows[0], ownership_mode="shared")

    coverage, violations = check_contract_registry_closure(
        blueprint=blueprint,
        rows=tuple(rows),
    )

    assert coverage["ok"] is False
    stale = next(
        violation for violation in violations if violation["rule"] == "stale-registry-row"
    )
    assert "ownership_mode" in stale["stale_fields"]


def test_connectivity_registry_closure_flags_sampled_aspirational_gaps() -> None:
    contracts = (
        ("TypedAction", "dev.scripts.devctl.runtime.action_contracts:TypedAction"),
        ("ArtifactStore", "dev.scripts.devctl.runtime.action_contracts:ArtifactStore"),
        ("RunRecord", "dev.scripts.devctl.runtime.action_contracts:RunRecord"),
        (
            "DecisionPacket",
            "dev.scripts.devctl.runtime.finding_contracts:DecisionPacketRecord",
        ),
        ("ReviewState", "dev.scripts.devctl.runtime.review_state_models:ReviewState"),
    )
    registry = ConnectivityRegistrySnapshot(
        schema_version=1,
        contract_id="ConnectivityRegistrySnapshot",
        source_contract_count=len(contracts),
        governed_surface_ids=(),
        connected_contracts=tuple(
            ConnectivityContractRow(
                contract_id=contract_id,
                owner_layer="governance_runtime",
                runtime_model=runtime_model,
                writer=ConnectivityWriterRow(
                    writer_id=f"writer:{contract_id}",
                    path="dev/scripts/devctl/runtime/example.py",
                    authority_kind="runtime_model",
                ),
                fields=(
                    ConnectivityFieldRow(
                        field_name="contract_id",
                        type_hint="str",
                        field_kind="source",
                        writer_ids=(f"writer:{contract_id}",),
                        reader_ids=("pyqt6_operator_console",),
                    ),
                ),
                reader_ids=("pyqt6_operator_console",),
                projection_ids=("pyqt6_operator_console",),
            )
            for contract_id, runtime_model in contracts
        ),
    )

    with patch(
        "dev.scripts.checks.platform_contract_closure.connectivity_registry_closure.build_connectivity_registry_snapshot",
        return_value=registry,
    ):
        coverage, violations = check_connectivity_registry_closure(
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            )
        )

    assert coverage["ok"] is False
    gap_violations = [
        violation
        for violation in violations
        if violation.get("rule") == "aspirational-connectivity-gap"
    ]
    assert coverage["aspirational_gap_count"] == 5
    assert {v["contract_id"] for v in gap_violations} == {
        "TypedAction",
        "ArtifactStore",
        "RunRecord",
        "DecisionPacket",
        "ReviewState",
    }
    assert all(
        violation["reader_id"] == "pyqt6_operator_console"
        for violation in gap_violations
    )
    assert all(
        violation["classification"] == "aspirational_gap"
        for violation in gap_violations
    )


def test_missing_connection_override_classifies_mistaken_declaration(
    tmp_path: Path,
) -> None:
    override_path = tmp_path / "registry_reader_overrides.json"
    override_path.write_text(
        dedent(
            """
            {
              "overrides": [
                {
                  "contract_id": "TypedAction",
                  "reader_id": "pyqt6_operator_console",
                  "classification": "mistakenly_declared",
                  "justification": "Synthetic test surface is not a TypedAction consumer."
                }
              ]
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    registry = ConnectivityRegistrySnapshot(
        schema_version=1,
        contract_id="ConnectivityRegistrySnapshot",
        source_contract_count=1,
        governed_surface_ids=(),
        connected_contracts=(
            ConnectivityContractRow(
                contract_id="TypedAction",
                owner_layer="governance_runtime",
                runtime_model="dev.scripts.devctl.runtime.action_contracts:TypedAction",
                writer=ConnectivityWriterRow(
                    writer_id="writer:TypedAction",
                    path="dev/scripts/devctl/runtime/example.py",
                    authority_kind="runtime_model",
                ),
                fields=(
                    ConnectivityFieldRow(
                        field_name="contract_id",
                        type_hint="str",
                        field_kind="source",
                        writer_ids=("writer:TypedAction",),
                        reader_ids=("pyqt6_operator_console",),
                    ),
                ),
                reader_ids=("pyqt6_operator_console",),
                projection_ids=("pyqt6_operator_console",),
            ),
        ),
    )

    findings = find_missing_connection_findings(
        registry=registry,
        required_reader_ids=(),
        row_reader_ids=(),
        repo_root=Path.cwd(),
        override_path=override_path,
    )

    assert len(findings) == 1
    assert findings[0].classification == "mistakenly_declared"
    assert findings[0].justification


def test_typed_state_writer_authority_flags_current_session_constructor(
    tmp_path: Path,
) -> None:
    source = _synthetic_source(
        tmp_path,
        "dev/scripts/devctl/review_channel/bad_current_session.py",
        """
        def bad():
            return ReviewCurrentSessionState(current_instruction="x")
        """,
    )
    coverage, violations = check_typed_state_writer_authority(python_files=(source,))
    assert coverage["ok"] is False
    assert len(violations) == 1
    assert violations[0]["rule"] == "typed-state-writer-bypass"
    assert violations[0]["field"] == "ReviewCurrentSessionState"


def test_typed_state_writer_authority_flags_current_session_review_state_write(
    tmp_path: Path,
) -> None:
    source = _synthetic_source(
        tmp_path,
        "dev/scripts/devctl/review_channel/bad_current_session_write.py",
        """
        def bad(review_state):
            review_state["current_session"] = {"current_instruction": "x"}
        """,
    )
    _coverage, violations = check_typed_state_writer_authority(python_files=(source,))
    assert len(violations) == 1
    assert violations[0]["field"] == "current_session"


def test_typed_state_writer_authority_flags_reviewer_mode_projection_write(
    tmp_path: Path,
) -> None:
    source = _synthetic_source(
        tmp_path,
        "dev/scripts/devctl/review_channel/bad_reviewer_mode.py",
        """
        def bad(payload):
            payload["reviewer_mode"] = "active_dual_agent"
        """,
    )
    _coverage, violations = check_typed_state_writer_authority(python_files=(source,))
    assert len(violations) == 1
    assert violations[0]["field"] == "reviewer_mode"


def test_typed_state_writer_authority_flags_reviewer_mode_attribute_write(
    tmp_path: Path,
) -> None:
    source = _synthetic_source(
        tmp_path,
        "dev/scripts/devctl/review_channel/bad_reviewer_mode_attr.py",
        """
        def bad(bridge_state):
            bridge_state.reviewer_mode = "active_dual_agent"
        """,
    )
    _coverage, violations = check_typed_state_writer_authority(python_files=(source,))
    assert len(violations) == 1
    assert violations[0]["field"] == "reviewer_mode"


def test_typed_state_writer_authority_ignores_test_fixtures(tmp_path: Path) -> None:
    source = _synthetic_source(
        tmp_path,
        "dev/scripts/devctl/tests/bad_fixture.py",
        """
        def fixture(payload):
            payload["reviewer_mode"] = "active_dual_agent"
            return ReviewCurrentSessionState(current_instruction="x")
        """,
    )
    coverage, violations = check_typed_state_writer_authority(python_files=(source,))
    assert coverage["ok"] is True
    assert violations == ()


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
    schema_violations = [
        v for v in violations if v.get("rule") == "artifact-schema-drift"
    ]
    assert len(schema_violations) == 1
    assert schema_violations[0]["contract_id"] == "ProbeReport"


def test_platform_contract_closure_flags_missing_startup_surface_token() -> None:
    blueprint = build_platform_blueprint()
    _coverage, violations = evaluate_platform_contract_closure(
        blueprint,
        _surface_policy_with_tokens("platform-contracts"),
    )
    surface_violations = [
        v for v in violations if v.get("rule") == "missing-startup-surface-token"
    ]
    assert len(surface_violations) == 1
    assert (
        "check_platform_contract_closure.py" in surface_violations[0]["missing_tokens"]
    )


def test_platform_contract_closure_flags_missing_ai_instruction_prompt_route() -> None:
    blueprint = build_platform_blueprint()
    with patch(
        "dev.scripts.coderabbit.ralph_ai_fix.build_prompt",
        return_value="Prompt without routed probe guidance.",
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    route_violations = [
        v for v in violations if v.get("rule") == "unconsumed-field-route"
    ]
    route_violations = [
        v
        for v in route_violations
        if v.get("contract_id") == "Finding" and v.get("field_name") == "ai_instruction"
    ]
    assert len(route_violations) == 1
    assert route_violations[0]["route_id"] == "ralph_prompt"


def test_platform_contract_closure_flags_missing_ai_instruction_autonomy_route() -> (
    None
):
    blueprint = build_platform_blueprint()
    with patch(
        "dev.scripts.devctl.commands.loop_packet_helpers.load_loop_packet_probe_guidance",
        return_value=[],
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    route_violations = [
        v
        for v in violations
        if v.get("rule") == "unconsumed-field-route"
        and v.get("route_id") == "autonomy_loop_packet"
        and v.get("contract_id") == "Finding"
    ]
    assert len(route_violations) == 1
    assert route_violations[0]["field_name"] == "ai_instruction"


def test_platform_contract_closure_flags_missing_ai_instruction_guard_run_route() -> (
    None
):
    blueprint = build_platform_blueprint()
    with patch(
        "dev.scripts.devctl.commands.guard_run.load_probe_guidance",
        return_value=[],
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    route_violations = [
        v
        for v in violations
        if v.get("rule") == "unconsumed-field-route"
        and v.get("route_id") == "guard_run_report"
        and v.get("contract_id") == "Finding"
    ]
    assert len(route_violations) == 1
    assert route_violations[0]["field_name"] == "ai_instruction"


def test_platform_contract_closure_flags_incomplete_ai_instruction_route_family() -> (
    None
):
    blueprint = build_platform_blueprint()
    reduced_checks = tuple(
        check
        for check in field_routes.FIELD_ROUTE_CHECKS
        if getattr(check, "__name__", "")
        != "check_finding_ai_instruction_guard_run_route"
    )
    with patch(
        "dev.scripts.checks.platform_contract_closure.support.field_routes.FIELD_ROUTE_CHECKS",
        new=reduced_checks,
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    family_violations = [
        v
        for v in violations
        if v.get("rule") == "field-route-family-incomplete"
        and v.get("contract_id") == "Finding"
    ]
    assert len(family_violations) == 1
    assert family_violations[0]["field_name"] == "ai_instruction"
    assert family_violations[0]["missing_route_ids"] == ("guard_run_report",)


def test_platform_contract_closure_flags_missing_decision_mode_ralph_route() -> None:
    blueprint = build_platform_blueprint()
    with patch(
        "dev.scripts.coderabbit.ralph_ai_fix.build_prompt",
        return_value="Prompt without decision-mode routing.",
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    route_violations = [
        v
        for v in violations
        if v.get("rule") == "unconsumed-field-route"
        and v.get("contract_id") == "DecisionPacket"
        and v.get("route_id") == "ralph_prompt"
    ]
    assert len(route_violations) == 1
    assert route_violations[0]["field_name"] == "decision_mode"


def test_platform_contract_closure_flags_incomplete_decision_mode_route_family() -> (
    None
):
    blueprint = build_platform_blueprint()
    reduced_checks = tuple(
        check
        for check in field_routes.FIELD_ROUTE_CHECKS
        if getattr(check, "__name__", "")
        != "check_decision_packet_mode_guard_run_route"
    )
    with patch(
        "dev.scripts.checks.platform_contract_closure.support.field_routes.FIELD_ROUTE_CHECKS",
        new=reduced_checks,
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    family_violations = [
        v
        for v in violations
        if v.get("rule") == "field-route-family-incomplete"
        and v.get("contract_id") == "DecisionPacket"
    ]
    assert len(family_violations) == 1
    assert family_violations[0]["field_name"] == "decision_mode"
    assert family_violations[0]["missing_route_ids"] == ("guard_run_report",)


def test_platform_contract_closure_flags_missing_finding_backlog_findings_priority_route() -> (
    None
):
    blueprint = build_platform_blueprint()
    original = field_routes_planning._source_contains_any

    def _missing_latest_rows(module_path: str, tokens: tuple[str, ...]) -> bool:
        if (
            module_path == "dev.scripts.devctl.commands.reporting.findings_priority"
            and any(token in {"backlog.latest_rows", "latest_rows"} for token in tokens)
        ):
            return False
        return original(module_path, tokens)

    with patch.object(
        field_routes_planning,
        "_source_contains_any",
        side_effect=_missing_latest_rows,
    ):
        _coverage, violations = evaluate_platform_contract_closure(
            blueprint,
            _surface_policy_with_tokens(
                "platform-contracts",
                "render-surfaces",
                "check_platform_contract_closure.py",
            ),
        )

    route_violations = [
        v
        for v in violations
        if v.get("rule") == "unconsumed-field-route"
        and v.get("contract_id") == "FindingBacklog"
        and v.get("field_name") == "latest_rows"
    ]
    assert len(route_violations) == 1
    assert route_violations[0]["route_id"] == "findings_priority"


def test_emitter_parity_catches_missing_bridge_state_key() -> None:
    """Guard must fail if event-backed bridge_state drops a ReviewBridgeState field."""
    from dev.scripts.devctl.review_channel import event_projection

    original = event_projection.build_event_bridge_state_projection

    def _drop_ack_current(
        *,
        review_state: dict[str, object],
        bridge_liveness: dict[str, object],
        reviewer_runtime=None,
    ) -> dict[str, object]:
        bridge_state = dict(
            original(
                review_state=review_state,
                bridge_liveness=bridge_liveness,
                reviewer_runtime=reviewer_runtime,
            )
        )
        del bridge_state["claude_ack_current"]
        return bridge_state

    with patch.object(
        event_projection,
        "build_event_bridge_state_projection",
        _drop_ack_current,
    ):
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

    original = event_projection.build_event_bridge_state_projection

    def _type_drift(
        *,
        review_state: dict[str, object],
        bridge_liveness: dict[str, object],
        reviewer_runtime=None,
    ) -> dict[str, object]:
        bridge_state = dict(
            original(
                review_state=review_state,
                bridge_liveness=bridge_liveness,
                reviewer_runtime=reviewer_runtime,
            )
        )
        bridge_state["last_codex_poll_age_seconds"] = 0.5
        return bridge_state

    with patch.object(
        event_projection,
        "build_event_bridge_state_projection",
        _type_drift,
    ):
        results = _check_review_state_emitter_parity()

    violation = next(
        violation
        for coverage, violation in results
        if coverage["check"] == "bridge_state_types"
    )
    assert violation is not None
    assert violation["rule"] == "emitter-type-drift"
    assert "last_codex_poll_age_seconds" in violation["detail"]


def test_emitter_parity_catches_parser_roundtrip_drift() -> None:
    """Guard must fail if emitted bridge fields drift from parser-owned truth."""
    from dev.scripts.devctl.review_channel import event_projection

    original = event_projection.build_event_bridge_state_projection

    def _roundtrip_drift(
        *,
        review_state: dict[str, object],
        bridge_liveness: dict[str, object],
        reviewer_runtime=None,
    ) -> dict[str, object]:
        bridge_state = dict(
            original(
                review_state=review_state,
                bridge_liveness=bridge_liveness,
                reviewer_runtime=reviewer_runtime,
            )
        )
        bridge_state["overall_state"] = "synthetic-drift"
        return bridge_state

    with patch.object(
        event_projection,
        "build_event_bridge_state_projection",
        _roundtrip_drift,
    ):
        results = _check_review_state_emitter_parity()

    violation = next(
        violation
        for coverage, violation in results
        if coverage["check"] == "bridge_state_parser_roundtrip"
    )
    assert violation is not None
    assert violation["rule"] == "bridge-parser-roundtrip-drift"
    assert "overall_state" in violation["detail"]


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
        _BRIDGE_STATE_EXPECTED_TYPES,
        _build_synthetic_review_state,
    )
    from dev.scripts.devctl.review_channel.event_projection import (
        build_event_bridge_liveness_projection,
        build_event_bridge_state_projection,
    )
    from dev.scripts.devctl.review_channel.projection_bundle import (
        write_projection_bundle,
    )
    from dev.scripts.devctl.runtime.review_state_models import (
        CollaborationSessionState,
        ReviewBridgeState,
        ReviewCurrentSessionState,
    )

    synthetic = _build_synthetic_review_state()
    liveness = build_event_bridge_liveness_projection(synthetic)
    bridge_state = build_event_bridge_state_projection(
        review_state=synthetic,
        bridge_liveness=liveness,
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

    # Validate typed current_session contract fields on the artifact
    current_session_fields = {f.name for f in dc_fields(ReviewCurrentSessionState)}
    artifact_current_session = on_disk.get("current_session", {})
    assert isinstance(
        artifact_current_session, dict
    ), "current_session must be a dict on disk"
    missing_current_session = sorted(
        current_session_fields - set(artifact_current_session.keys())
    )
    extra_current_session = sorted(
        set(artifact_current_session.keys()) - current_session_fields
    )
    assert not missing_current_session, (
        "Artifact review_state.json current_session missing: "
        f"{missing_current_session}"
    )
    assert not extra_current_session, (
        "Artifact review_state.json current_session has extra: "
        f"{extra_current_session}"
    )

    collaboration_fields = {f.name for f in dc_fields(CollaborationSessionState)}
    artifact_collaboration = on_disk.get("collaboration", {})
    assert isinstance(
        artifact_collaboration, dict
    ), "collaboration must be a dict on disk"
    missing_collaboration = sorted(
        collaboration_fields - set(artifact_collaboration.keys())
    )
    extra_collaboration = sorted(
        set(artifact_collaboration.keys()) - collaboration_fields
    )
    assert not missing_collaboration, (
        "Artifact review_state.json collaboration missing: " f"{missing_collaboration}"
    )
    assert not extra_collaboration, (
        "Artifact review_state.json collaboration has extra: " f"{extra_collaboration}"
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


def test_auto_mode_phase_route_passes_with_resolved_phase_wired() -> None:
    """The tightened route must pass when resolved_phase is in both the packet and renderer."""
    from dev.scripts.checks.platform_contract_closure.field_routes_surface_state import (
        check_auto_mode_phase_session_resume_route,
    )

    coverage, violation = check_auto_mode_phase_session_resume_route()
    assert coverage["ok"] is True
    assert violation is None
    assert "resolved_phase" in coverage["detail"]


def test_auto_mode_phase_route_fails_when_renderer_drops_resolved_phase() -> None:
    """The route must fail if the renderer stops referencing resolved_phase."""
    from dev.scripts.checks.platform_contract_closure.field_routes_surface_state import (
        _source_contains_any,
        check_auto_mode_phase_session_resume_route,
    )

    original = _source_contains_any

    def _fake_source_check(module_path: str, tokens: tuple[str, ...]) -> bool:
        if (
            module_path
            == "dev.scripts.devctl.commands.governance.session_resume_render"
        ):
            return False
        return original(module_path, tokens)

    with patch(
        "dev.scripts.checks.platform_contract_closure.field_routes_surface_state._source_contains_any",
        side_effect=_fake_source_check,
    ):
        coverage, violation = check_auto_mode_phase_session_resume_route()

    assert coverage["ok"] is False
    assert violation is not None
    assert violation["rule"] == "unconsumed-field-route"
    assert violation["contract_id"] == "AutoModeState"
    assert violation["field_name"] == "phase"


def test_top_blocker_dashboard_route_rejects_docstring_only_package_match(
    monkeypatch,
    tmp_path,
) -> None:
    """Regression for F1: a package ``__init__.py`` docstring that merely
    mentions ``top_blocker`` must not satisfy the dashboard field-route proof.

    Before the AST-backed helper landed, ``_source_contains_any`` scanned every
    ``*.py`` file in a package and short-circuited on the first raw-text hit.
    After the ``dashboard_render`` flat->package refactor, the new
    ``__init__.py`` docstring mentioned ``top_blocker`` and satisfied the
    check even when no submodule actually rendered the field. This test locks
    the fix: a synthetic dashboard_render package whose ``__init__.py`` only
    *documents* ``top_blocker`` and whose submodules never reference it must
    fail the route check with an ``unconsumed-field-route`` violation.
    """
    from dev.scripts.checks.platform_contract_closure import (
        field_routes_surface_state as mod,
    )

    fake_package = (
        tmp_path / "dev" / "scripts" / "devctl" / "commands" / "dashboard_render"
    )
    fake_package.mkdir(parents=True)
    (fake_package / "__init__.py").write_text(
        '"""Docstring that mentions top_blocker but performs no executable use."""\n',
        encoding="utf-8",
    )
    (fake_package / "markdown.py").write_text(
        "def render(snapshot):\n" "    return snapshot.get('other_field', '')\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "_REPO_ROOT", tmp_path)

    coverage, violation = mod.check_top_blocker_dashboard_route()
    assert coverage["ok"] is False
    assert violation is not None
    assert violation["rule"] == "unconsumed-field-route"
    assert violation["field_name"] == "top_blocker"


def test_platform_contract_closure_markdown_lists_field_route_count() -> None:
    report = build_report()
    output = render_md(report)
    assert "checked_field_routes: 18" in output
    assert "checked_field_route_families: 11" in output
