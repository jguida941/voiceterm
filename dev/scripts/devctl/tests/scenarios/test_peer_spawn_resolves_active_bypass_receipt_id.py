"""Scenario: ``peer-spawn --bypass-receipt-id <id>`` must resolve the id
against the typed BypassLifecycle store and pass the resulting receipt
into the spawn driver. Today the CLI handler returns ``None`` for any
id-only path, so the driver always denies with ``bypass_receipt_missing``
even when an active receipt exists in the store. That breaks the only
operator-facing flag the ``peer-spawn --help`` text advertises as
canonical.

The invariant this test locks in: given an active edit_only
BypassLifecycle whose receipt_id is passed via ``--bypass-receipt-id``,
the spawn output must NOT carry ``denied_bypass_missing`` /
``bypass_receipt_missing``. A dry-run against a resolved receipt resolves
to ``status="dry_run_no_launch_callable"`` (ok=True), because the launch
adapter is intentionally skipped.

The fixture is hermetic: the test builds a one-row lifecycle store under
``tmp_path`` and points ``DEVCTL_BYPASS_LIFECYCLE_STORE_PATH`` at it, so
the live ``dev/state/bypass_lifecycles.jsonl`` is not touched.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]


def _future_utc(*, hours: int = 1) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _build_synthetic_active_lifecycle_row(
    *,
    receipt_id: str,
    scope: str = "edit_only",
) -> dict[str, object]:
    """Construct one BypassLifecycle JSON record shaped exactly like the
    typed `from_mapping` chain expects.

    The receipt's `expires_at_utc` is one hour in the future and its
    `requested_authority_scope` is `edit_only`, which transitively grants
    `agent_spawn_only` via `_GRANTED_SCOPES`. Lifecycle `state` is
    `bypass_active`, which is the gating value `bypass_lifecycle_active`
    checks against.
    """
    now = _now_utc()
    expires = _future_utc(hours=1)
    request_id = f"req-{receipt_id}"
    evaluation_id = f"eval-{receipt_id}"
    return {
        "contract_id": "BypassLifecycle",
        "schema_version": 1,
        "lifecycle_id": f"gel:bypass:{receipt_id}",
        "state": "bypass_active",
        "request": {
            "contract_id": "BypassRequest",
            "schema_version": 1,
            "request_id": request_id,
            "scope": scope,
            "reason": "peer-spawn id-resolution scenario fixture",
            "actor": "operator",
            "requested_at_utc": now,
            "state": "bypass_requested",
            "target_role": "",
            "target_session_id": "",
            "target_surface": "",
            "evidence_refs": [],
        },
        "evaluation": {
            "contract_id": "BypassEvaluation",
            "schema_version": 1,
            "evaluation_id": evaluation_id,
            "request_id": request_id,
            "decision": "approved",
            "evaluated_at_utc": now,
            "evaluator_actor_id": "operator",
            "reason": "operator_approved_bypass_request",
            "approved_scope": scope,
            "governed_exception_lifecycle_id": "",
            "authority_evidence_refs": [],
            "policy_evidence_refs": [],
        },
        "receipt": {
            "contract_id": "BypassReceipt",
            "schema_version": 1,
            "receipt_id": receipt_id,
            "reason": "operator_approved_bypass_request",
            "operator_signature": "operator",
            "ai_approval_evidence": "test_fixture",
            "requested_authority_scope": scope,
            "granted_at_utc": now,
            "granted_by_operator_actor_id": "operator",
            "state": "bypass_active",
            "expires_at_utc": expires,
            "revoked_at_utc": "",
            "revoked_reason": "",
        },
        "expiry": None,
        "governed_exception": None,
        "activation_evidence_refs": [],
    }


def _write_synthetic_store(path: Path, *, receipt_id: str) -> None:
    row = _build_synthetic_active_lifecycle_row(receipt_id=receipt_id)
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")


def _run_peer_spawn(
    *,
    receipt_id: str,
    store_path: Path,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    env["DEVCTL_BYPASS_LIFECYCLE_STORE_PATH"] = str(store_path)
    cmd = [
        sys.executable,
        "dev/scripts/devctl.py",
        "peer-spawn",
        "--provider", "codex",
        "--role", "reviewer",
        "--bypass-receipt-id", receipt_id,
        "--row-id", "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        "--actor", "claude",
        "--reason", "scenario: id-resolution against active receipt",
        "--interaction-mode", "remote_control",
        "--dry-run",
        "--format", "json",
    ]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def test_peer_spawn_resolves_active_bypass_receipt_id_into_typed_receipt(
    tmp_path: Path,
) -> None:
    receipt_id = "bypass:grant-scenario-active-edit-only"
    store_path = tmp_path / "bypass_lifecycles.jsonl"
    _write_synthetic_store(store_path, receipt_id=receipt_id)

    result = _run_peer_spawn(receipt_id=receipt_id, store_path=store_path)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"peer-spawn --format json did not emit valid JSON: {exc!r}\n"
            f"stdout head:\n{result.stdout[:2000]}\n"
            f"stderr head:\n{result.stderr[:2000]}"
        )

    receipt = payload.get("receipt") or {}
    status = str(receipt.get("status") or "")
    errors = list(payload.get("errors") or [])

    assert status != "denied_bypass_missing", (
        "peer-spawn returned denied_bypass_missing even though "
        f"--bypass-receipt-id={receipt_id} matches an ACTIVE edit_only "
        "BypassLifecycle in the test store. The CLI handler is not "
        "resolving the receipt id against the lifecycle store; today it "
        "drops to `return None` on the id-only path, which forces every "
        "operator-facing peer-spawn call to be denied. This is the exact "
        "failure mode behind the 'launching codex doesn't work' report.\n"
        f"  store_path: {result.returncode and 'subprocess exit ' + str(result.returncode)}\n"
        f"  receipt.status: {status!r}\n"
        f"  errors: {errors!r}\n"
        f"  stdout head: {result.stdout[:1500]}"
    )
    assert "bypass_receipt_missing" not in errors, (
        "peer-spawn errors[] still contains 'bypass_receipt_missing' even "
        "after the id was resolved. The lookup adapter is partially wired "
        "but the deny path is still firing — likely scope mismatch or "
        "expired-receipt drift, not the id-lookup gap.\n"
        f"  errors: {errors!r}"
    )

    bypass_receipt_id_echoed = str(receipt.get("bypass_receipt_id") or "")
    assert bypass_receipt_id_echoed == receipt_id, (
        "AgentSpawnReceipt.bypass_receipt_id must echo the resolved "
        "receipt id so downstream callers can audit which receipt "
        "authorized the spawn.\n"
        f"  got: {bypass_receipt_id_echoed!r}\n"
        f"  want: {receipt_id!r}"
    )


def test_peer_spawn_returns_typed_denial_when_receipt_id_not_in_store(
    tmp_path: Path,
) -> None:
    """The resolution path must still emit a typed denial when the id is
    unknown to the store. We seed a store with one record whose id is
    deliberately different from the one we look up, then assert the typed
    denial surface is intact (no traceback, recognized error vocab).
    """
    store_path = tmp_path / "bypass_lifecycles.jsonl"
    _write_synthetic_store(store_path, receipt_id="bypass:grant-other-id")

    result = _run_peer_spawn(
        receipt_id="bypass:grant-missing-from-store",
        store_path=store_path,
    )

    payload = json.loads(result.stdout)
    assert payload.get("ok") is False
    errors = list(payload.get("errors") or [])
    assert errors, "errors[] is empty on an unresolved id"
    # The denial vocabulary may be either bypass_receipt_missing (the
    # current overall denial code) or a more specific receipt-not-found
    # variant once the resolver is in place. Both are acceptable as long
    # as the typed vocab is preserved.
    recognized = (
        "bypass_receipt_missing",
        "bypass_receipt_not_active",
        "bypass_receipt_scope_insufficient",
    )
    assert any(
        str(e).startswith(p) for e in errors for p in recognized
    ), f"errors {errors!r} do not match the recognized typed denial vocab"
    assert "Traceback" not in result.stdout, (
        "unresolved id path surfaced a raw traceback instead of typed denial"
    )
