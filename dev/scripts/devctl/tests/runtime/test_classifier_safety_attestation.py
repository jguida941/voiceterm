"""Tests for ClassifierSafetyAttestation projection behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dev.scripts.devctl.runtime.classifier_safety_attestation import (
    CLASSIFIER_SAFETY_SETTINGS_KEY,
    build_classifier_safety_attestation,
    classifier_permission_rules_for_receipt,
    project_classifier_safety_attestation,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassEvaluationInput,
    BypassRequest,
    evaluate_bypass_request,
)


def _active_lifecycle(*, expires_at_utc: str = "2030-05-14T00:00:00Z"):
    return evaluate_bypass_request(
        BypassRequest(
            request_id="classifier-safety-test",
            scope=BypassAuthorityScope.EDIT_ONLY,
            reason="Operator approved classifier projection test.",
            actor="operator",
            requested_at_utc="2026-05-14T13:00:00Z",
            target_role="implementer",
            target_session_id="session-test",
            target_surface="review-channel-launch",
            evidence_refs=("packet:rev_pkt_test",),
        ),
        BypassEvaluationInput(
            operator_signature="operator",
            ai_approval_evidence="packet:rev_pkt_test",
            evaluated_at_utc="2026-05-14T13:00:30Z",
            evaluator_actor_id="operator",
            expires_at_utc=expires_at_utc,
        ),
    )


def test_build_attestation_requires_active_bypass_lifecycle(tmp_path: Path) -> None:
    lifecycle = _active_lifecycle(expires_at_utc="2020-01-01T00:00:00Z")

    attestation = build_classifier_safety_attestation(
        lifecycle,
        settings_path=tmp_path / "settings.local.json",
    )

    assert attestation is None


def test_projection_emits_wildcard_dominance_warning(tmp_path: Path) -> None:
    settings = tmp_path / "settings.local.json"
    settings.write_text(
        json.dumps({"permissions": {"allow": ["Bash(*)"]}}),
        encoding="utf-8",
    )
    attestation = build_classifier_safety_attestation(
        _active_lifecycle(),
        settings_path=settings,
    )
    assert attestation is not None

    result = project_classifier_safety_attestation(settings, attestation)

    assert result["classifier_dominated_by_wildcard"] is True
    assert result["warnings"] == ("classifier_dominated_by_bash_wildcard",)
    payload = json.loads(settings.read_text(encoding="utf-8"))
    bridge = payload[CLASSIFIER_SAFETY_SETTINGS_KEY]
    assert bridge["classifier_dominated_by_wildcard"] is True
    assert bridge["latest_warning"] == "classifier_dominated_by_bash_wildcard"
    assert "Bash(*)" in payload["permissions"]["allow"]
    assert all(
        rule in payload["permissions"]["allow"]
        for rule in classifier_permission_rules_for_receipt(
            "bypass:classifier-safety-test"
        )
    )


def test_projection_rejects_invalid_settings_payloads(tmp_path: Path) -> None:
    settings = tmp_path / "settings.local.json"
    attestation = build_classifier_safety_attestation(
        _active_lifecycle(),
        settings_path=settings,
    )
    assert attestation is not None

    settings.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="expected Claude settings JSON object"):
        project_classifier_safety_attestation(settings, attestation)

    settings.write_text(
        json.dumps({"permissions": {"allow": [1]}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="allow_must_be_string_list"):
        project_classifier_safety_attestation(settings, attestation)

    settings.write_text(
        json.dumps({CLASSIFIER_SAFETY_SETTINGS_KEY: {"attestations": ["bad"]}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="attestations_must_be_object_list"):
        project_classifier_safety_attestation(settings, attestation)
