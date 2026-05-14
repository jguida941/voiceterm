"""Tests for the ``devctl bypass`` command surface."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands.bypass import command as bypass
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.runtime.classifier_safety_attestation import (
    classifier_permission_rules_for_receipt,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassLifecycle,
    load_bypass_lifecycles,
)


def test_bypass_parser_accepts_grant_scope_and_reason() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "bypass",
            "grant",
            "--scope",
            "edit-only",
            "--reason",
            "operator approved bootstrap",
            "--evaluator-actor-id",
            "operator",
            "--format",
            "json",
        ]
    )

    assert args.command == "bypass"
    assert args.bypass_action == "grant"
    assert args.scope == "edit-only"
    assert args.reason == "operator approved bootstrap"
    assert args.evaluator_actor_id == "operator"
    assert COMMAND_HANDLERS["bypass"] is bypass.run
    assert "bypass" in COMMANDS


def test_bypass_grant_persists_active_lifecycle(
    tmp_path: Path,
    capsys,
) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bypass.add_parser(sub)
    store = tmp_path / "bypass_lifecycles.jsonl"
    args = parser.parse_args(
        [
            "bypass",
            "grant",
            "--scope",
            "edit-and-commit",
            "--reason",
            "operator approved commit repair",
            "--evaluator-actor-id",
            "operator",
            "--request-id",
            "test-grant",
            "--store-path",
            str(store),
            "--classifier-settings-path",
            str(tmp_path / "settings.local.json"),
            "--evidence-ref",
            "packet:rev_pkt_test",
            "--format",
            "json",
        ]
    )

    rc = bypass.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["receipt_id"] == "bypass:test-grant"
    assert payload["scope"] == "edit_and_commit"
    classifier = payload["classifier_safety_attestation"]
    assert classifier["ok"] is True
    assert classifier["bypass_receipt_id"] == "bypass:test-grant"
    settings = json.loads((tmp_path / "settings.local.json").read_text())
    allow = settings["permissions"]["allow"]
    assert any("--bypass-receipt-id bypass:test-grant" in rule for rule in allow)
    assert all("bypass:test-grant" in rule for rule in allow)
    assert not any("bypass grant" in rule for rule in allow)
    assert not any("launch_codex_with_bootstrap_receipt" in rule for rule in allow)
    attestations = settings["codex_voice_classifier_safety"]["attestations"]
    assert attestations[-1]["contract_id"] == "ClassifierSafetyAttestation"
    assert attestations[-1]["bypass_receipt_id"] == "bypass:test-grant"
    lifecycles = load_bypass_lifecycles(store)
    assert len(lifecycles) == 1
    lifecycle = lifecycles[0]
    assert isinstance(lifecycle, BypassLifecycle)
    assert lifecycle.state.value == "bypass_active"
    assert lifecycle.receipt is not None
    assert lifecycle.receipt.receipt_id == "bypass:test-grant"
    assert lifecycle.request.evidence_refs == ("packet:rev_pkt_test",)


def test_bypass_grant_maps_publish_scope(
    tmp_path: Path,
    capsys,
) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bypass.add_parser(sub)
    store = tmp_path / "bypass_lifecycles.jsonl"
    args = parser.parse_args(
        [
            "bypass",
            "grant",
            "--scope",
            "edit-commit-and-publish",
            "--reason",
            "operator approved publication repair",
            "--request-id",
            "publish-grant",
            "--store-path",
            str(store),
            "--classifier-settings-path",
            str(tmp_path / "settings.local.json"),
            "--format",
            "json",
        ]
    )

    rc = bypass.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["receipt_id"] == "bypass:publish-grant"
    assert payload["scope"] == "edit_commit_and_push"
    assert payload["classifier_safety_attestation"]["ok"] is True


def test_bypass_attest_projects_existing_active_lifecycle(
    tmp_path: Path,
    capsys,
) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bypass.add_parser(sub)
    store = tmp_path / "bypass_lifecycles.jsonl"
    settings = tmp_path / "settings.local.json"
    grant_args = parser.parse_args(
        [
            "bypass",
            "grant",
            "--scope",
            "edit-only",
            "--reason",
            "operator approved classifier projection",
            "--request-id",
            "attest-grant",
            "--store-path",
            str(store),
            "--classifier-settings-path",
            str(settings),
            "--format",
            "json",
        ]
    )
    assert bypass.run(grant_args) == 0
    capsys.readouterr()
    attest_args = parser.parse_args(
        [
            "bypass",
            "attest",
            "--receipt-id",
            "bypass:attest-grant",
            "--store-path",
            str(store),
            "--classifier-settings-path",
            str(settings),
            "--format",
            "json",
        ]
    )

    rc = bypass.run(attest_args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    classifier = payload["classifier_safety_attestation"]
    assert classifier["attestation_id"] == "classifier-safety:bypass:attest-grant"
    settings_payload = json.loads(settings.read_text())
    attestations = settings_payload["codex_voice_classifier_safety"]["attestations"]
    assert len(
        [
            row
            for row in attestations
            if row["attestation_id"] == "classifier-safety:bypass:attest-grant"
        ]
    ) == 1
    allow = settings_payload["permissions"]["allow"]
    assert len(allow) == len(set(allow))


def test_bypass_attest_requires_active_receipt(tmp_path: Path, capsys) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bypass.add_parser(sub)
    args = parser.parse_args(
        [
            "bypass",
            "attest",
            "--receipt-id",
            "bypass:missing",
            "--store-path",
            str(tmp_path / "bypass_lifecycles.jsonl"),
            "--classifier-settings-path",
            str(tmp_path / "settings.local.json"),
            "--format",
            "json",
        ]
    )

    rc = bypass.run(args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error"] == "active_bypass_receipt_not_found"


def test_classifier_permission_rules_are_receipt_scoped() -> None:
    rules = classifier_permission_rules_for_receipt("bypass:receipt-1")

    assert rules
    assert all("bypass:receipt-1" in rule for rule in rules)
    assert not any("Bash(*)" in rule for rule in rules)
    assert not any("bypass grant" in rule for rule in rules)
    assert not any("startup-context" in rule for rule in rules)
    assert not any("launch_codex_with_bootstrap_receipt" in rule for rule in rules)
    assert any("review-channel --action launch" in rule for rule in rules)
    assert any("review-channel --action recover" in rule for rule in rules)


def test_classifier_projection_preserves_existing_settings(tmp_path: Path) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    bypass.add_parser(sub)
    store = tmp_path / "bypass_lifecycles.jsonl"
    settings = tmp_path / "settings.local.json"
    settings.write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": ["Read(*)"],
                    "deny": ["Bash(git push *)"],
                },
                "hooks": {"UserPromptSubmit": []},
                "outputStyle": "Explanatory",
            }
        )
    )
    args = parser.parse_args(
        [
            "bypass",
            "grant",
            "--scope",
            "edit-only",
            "--reason",
            "operator approved preserved settings projection",
            "--request-id",
            "preserve-settings",
            "--store-path",
            str(store),
            "--classifier-settings-path",
            str(settings),
            "--format",
            "json",
        ]
    )

    assert bypass.run(args) == 0

    payload = json.loads(settings.read_text())
    assert "Read(*)" in payload["permissions"]["allow"]
    assert payload["permissions"]["deny"] == ["Bash(git push *)"]
    assert payload["hooks"] == {"UserPromptSubmit": []}
    assert payload["outputStyle"] == "Explanatory"


def test_bypass_grant_requires_scope(tmp_path: Path) -> None:
    args = SimpleNamespace(
        scope="",
        reason="operator approved repair",
        evaluator_actor_id="operator",
        request_id="missing-scope",
        target_role="implementer",
        target_session_id="",
        target_surface="review-channel-launch",
        evidence_ref=(),
        operator_signature="",
        ai_approval_evidence="",
        expires_in_hours=24.0,
        store_path=str(tmp_path / "bypass_lifecycles.jsonl"),
    )

    with pytest.raises(ValueError, match="unknown_bypass_scope"):
        bypass.grant_action(args)


def test_bypass_grant_requires_reason(tmp_path: Path) -> None:
    args = SimpleNamespace(
        scope="edit-only",
        reason=" ",
        evaluator_actor_id="operator",
        request_id="missing-reason",
        target_role="implementer",
        target_session_id="",
        target_surface="review-channel-launch",
        evidence_ref=(),
        operator_signature="",
        ai_approval_evidence="",
        expires_in_hours=24.0,
        store_path=str(tmp_path / "bypass_lifecycles.jsonl"),
    )

    with pytest.raises(ValueError, match="reason_required"):
        bypass.grant_action(args)


def test_bypass_grant_appends_multiple_lifecycles(tmp_path: Path) -> None:
    store = tmp_path / "bypass_lifecycles.jsonl"

    for request_id in ("grant-one", "grant-two"):
        report, rc = bypass.grant_action(
            SimpleNamespace(
                scope="edit-only",
                reason=f"operator approved {request_id}",
                evaluator_actor_id="operator",
                request_id=request_id,
                target_role="implementer",
                target_session_id="",
                target_surface="review-channel-launch",
                evidence_ref=(),
                operator_signature="",
                ai_approval_evidence="",
                expires_in_hours=24.0,
                store_path=str(store),
            )
        )
        assert rc == 0
        assert report["receipt_id"] == f"bypass:{request_id}"

    assert len(store.read_text(encoding="utf-8").splitlines()) == 2
    assert [
        lifecycle.receipt.receipt_id
        for lifecycle in load_bypass_lifecycles(store)
        if lifecycle.receipt is not None
    ] == ["bypass:grant-one", "bypass:grant-two"]
