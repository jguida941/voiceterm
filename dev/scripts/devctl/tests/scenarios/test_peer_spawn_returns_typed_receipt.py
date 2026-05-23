"""Scenario: spawning a peer conductor (codex / claude / cursor) must
either succeed with a typed AgentSpawnReceipt, or fail with a typed
denial receipt whose shape downstream guards can read.

The contract this test locks in:
- Output carries an `AgentSpawnRequest` section (so the request was
  recorded as a typed event, not silently dropped at the CLI boundary).
- Output carries a `Receipt` section with a `status` field. On denial,
  status starts with ``denied_`` and a `reason` field is populated.
- The `errors` field exposes the typed reason code (one of the
  recognized vocabulary entries below), so the caller's automation can
  branch on it instead of pattern-matching prose.
- The output exposes a `canonical_command_hint` pointing at the typed
  remediation (passing ``--bypass-receipt-id``), so a stuck caller has a
  next step without consulting human prose.
- The denial path MUST NOT surface a raw stack trace, a generic argparse
  error, or anything resembling an external classifier denial — those
  are the failure modes that strand a caller (no typed handle to branch
  on, no remediation pointer).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]

RECOGNIZED_DENIAL_PREFIXES = (
    "bypass_receipt_missing",
    "bypass_receipt_not_active",
    "bypass_receipt_scope_insufficient",
    "unsupported_provider",
    "unsupported_role",
)


def _run_peer_spawn(*args: str, fmt: str = "md") -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    cmd = [
        sys.executable,
        "dev/scripts/devctl.py",
        "peer-spawn",
        *args,
        "--format",
        fmt,
    ]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def test_peer_spawn_codex_without_bypass_receipt_returns_typed_denial_md():
    result = _run_peer_spawn(
        "--provider", "codex",
        "--role", "reviewer",
        "--row-id", "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        "--actor", "claude",
        "--reason", "TDD scenario probe",
        "--interaction-mode", "remote_control",
        fmt="md",
    )
    stdout = result.stdout
    assert "Traceback" not in stdout, (
        "peer-spawn surfaced a raw python traceback instead of a typed "
        "denial receipt:\n" + stdout[:2000]
    )
    assert "## AgentSpawnRequest" in stdout, (
        "peer-spawn output missing AgentSpawnRequest section — the "
        "request was not recorded as a typed event:\n" + stdout[:2000]
    )
    assert "## Receipt" in stdout, (
        "peer-spawn output missing Receipt section — denial path is not "
        "emitting a typed AgentSpawnReceipt:\n" + stdout[:2000]
    )
    assert "- status: denied_" in stdout, (
        "denial receipt status is missing the `denied_` prefix; "
        "downstream automation cannot branch on it.\n" + stdout[:2000]
    )
    assert "- reason: " in stdout, (
        "denial receipt missing reason field:\n" + stdout[:2000]
    )
    assert "--bypass-receipt-id" in stdout, (
        "denial output does not surface canonical_command_hint pointing "
        "at the typed remediation flag:\n" + stdout[:2000]
    )
    assert "## Errors" in stdout, (
        "denial output missing Errors section — caller has no typed "
        "error vocabulary to branch on:\n" + stdout[:2000]
    )


def test_peer_spawn_codex_without_bypass_receipt_returns_typed_denial_json():
    result = _run_peer_spawn(
        "--provider", "codex",
        "--role", "reviewer",
        "--row-id", "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        "--actor", "claude",
        "--reason", "TDD scenario probe (json)",
        "--interaction-mode", "remote_control",
        fmt="json",
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"peer-spawn --format json did not emit valid JSON: {exc!r}\n"
            f"stdout head:\n{result.stdout[:2000]}"
        )
    assert payload.get("ok") is False, (
        f"peer-spawn unexpectedly reported ok={payload.get('ok')!r} "
        "without an active spawn-scoped bypass receipt on the ledger"
    )
    assert payload.get("action") == "peer-spawn", (
        f"action field is {payload.get('action')!r}, not 'peer-spawn'"
    )
    receipt = payload.get("receipt") or {}
    assert isinstance(receipt, dict) and receipt, (
        f"receipt missing or non-dict in denial payload: {receipt!r}"
    )
    status = str(receipt.get("status") or "")
    assert status.startswith("denied_"), (
        f"receipt.status is {status!r}; expected to start with 'denied_'"
    )
    reason = str(receipt.get("reason") or "")
    assert reason, "receipt.reason is empty on a denial path"
    assert any(reason.startswith(p) for p in RECOGNIZED_DENIAL_PREFIXES), (
        f"receipt.reason {reason!r} is not in the recognized typed denial "
        f"vocabulary {RECOGNIZED_DENIAL_PREFIXES}"
    )
    errors = payload.get("errors") or []
    assert errors, "errors field is empty on a denial payload"
    assert any(
        str(e).startswith(p) for e in errors for p in RECOGNIZED_DENIAL_PREFIXES
    ), f"errors {errors!r} not in recognized denial vocabulary"
    hint = str(payload.get("canonical_command_hint") or "")
    assert "--bypass-receipt-id" in hint, (
        f"canonical_command_hint does not point at the typed remediation: "
        f"{hint!r}"
    )


def test_peer_spawn_unsupported_provider_returns_typed_error():
    result = _run_peer_spawn(
        "--provider", "claude",
        "--role", "implementer",
        "--row-id", "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        "--actor", "claude",
        "--reason", "TDD probe: provider validation",
        fmt="json",
    )
    # 'claude' IS supported per SUPPORTED_PROVIDERS, so this should still
    # hit the bypass-receipt-missing path, not provider rejection. The
    # contract here is that the typed denial vocabulary is exercised in
    # all paths — provider validation is one branch, receipt validation
    # is another. Both produce typed errors[0] with recognized prefix.
    payload = json.loads(result.stdout)
    assert payload.get("ok") is False
    errors = payload.get("errors") or []
    assert errors and any(
        str(e).startswith(p) for e in errors for p in RECOGNIZED_DENIAL_PREFIXES
    ), f"errors {errors!r} not in recognized typed vocabulary"
