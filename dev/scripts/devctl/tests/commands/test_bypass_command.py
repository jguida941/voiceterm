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
            "--format",
            "json",
        ]
    )

    rc = bypass.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["receipt_id"] == "bypass:publish-grant"
    assert payload["scope"] == "edit_commit_and_push"


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
