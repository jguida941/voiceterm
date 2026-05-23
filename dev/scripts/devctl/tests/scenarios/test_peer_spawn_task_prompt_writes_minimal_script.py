"""Scenario: ``peer-spawn --task-prompt`` must take a minimal one-shot
launch path that invokes ``codex exec --sandbox workspace-write`` with
the operator-provided bounded prompt verbatim, and must NOT route through
the multi-agent review-channel supervised wrapper.

The review-channel launch wrapper is built for collaborative live
sessions: it carries a supervisor loop, an inactivity watchdog, a
task-complete handoff guard, and — crucially — a preflight authority
check that requires ``review_state_path`` to exist. A bounded one-shot
mutation has no ``review_state``; under the supervised wrapper the
preflight rejects with exit 82 BEFORE codex is invoked. That is the
exact failure mode observed in live dogfood with the marker
``PEERSPAWN-REAL-20260523T142707Z``: stderr ``"launch authority stale:
review_state_path missing"`` followed by ``"conductor exited with
non-restartable status 82"``.

Invariants asserted by this scenario:

1. The launch script written by ``peer-spawn --task-prompt`` invokes
   ``codex exec --sandbox workspace-write`` against the repo root.
2. The operator-supplied bounded prompt is embedded verbatim in the
   script (no multi-turn conductor prompt substitution).
3. The script does NOT carry the supervised review-channel wrapper
   markers (``review_channel_launch_authority_check``,
   ``run_review_channel_once``, ``review_channel_inactivity_watchdog``,
   ``review_channel_task_complete_handoff_guard``,
   ``REVIEW_CHANNEL_HEADLESS_MODE``). Their presence would mean the
   wrapper's exit-82 trap is back in the launch path.

The test is hermetic via two existing test-mode env vars:

- ``DEVCTL_BYPASS_LIFECYCLE_STORE_PATH`` points the spawn authority
  resolver at a synthetic single-row bypass store in ``tmp_path``.
- ``DEVCTL_PEER_SPAWN_TASK_PROMPT_DRY_LAUNCH=1`` makes the bounded-task
  launch path write the script and return without invoking
  ``subprocess.Popen``, so the test can read the script shape without
  spawning a real codex process or burning provider credits.
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


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _utc_future_iso(*, hours: int = 1) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def _write_synthetic_active_bypass_store(
    store_path: Path, *, receipt_id: str
) -> None:
    now = _utc_now_iso()
    expires = _utc_future_iso(hours=1)
    request_id = f"req-{receipt_id}"
    record = {
        "contract_id": "BypassLifecycle",
        "schema_version": 1,
        "lifecycle_id": f"gel:bypass:{receipt_id}",
        "state": "bypass_active",
        "request": {
            "contract_id": "BypassRequest",
            "schema_version": 1,
            "request_id": request_id,
            "scope": "edit_only",
            "reason": "task-prompt script-shape scenario fixture",
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
            "evaluation_id": f"eval-{receipt_id}",
            "request_id": request_id,
            "decision": "approved",
            "evaluated_at_utc": now,
            "evaluator_actor_id": "operator",
            "reason": "operator_approved_bypass_request",
            "approved_scope": "edit_only",
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
            "requested_authority_scope": "edit_only",
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
    store_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


def _invoke_peer_spawn(
    *,
    bypass_receipt_id: str,
    bypass_store_path: Path,
    task_prompt_file: Path,
) -> dict:
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    env["DEVCTL_BYPASS_LIFECYCLE_STORE_PATH"] = str(bypass_store_path)
    env["DEVCTL_PEER_SPAWN_TASK_PROMPT_DRY_LAUNCH"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "peer-spawn",
            "--provider", "codex",
            "--role", "implementer",
            "--bypass-receipt-id", bypass_receipt_id,
            "--row-id", "MP-TASK-PROMPT-SCENARIO",
            "--actor", "claude",
            "--reason", "scenario: task-prompt minimal launch path",
            "--interaction-mode", "remote_control",
            "--task-prompt-file", str(task_prompt_file),
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    if result.returncode not in (0,):
        raise AssertionError(
            "peer-spawn returned non-zero exit on the bounded-task path "
            f"({result.returncode}); stdout head:\n{result.stdout[:1500]}\n"
            f"stderr head:\n{result.stderr[:1500]}"
        )
    return json.loads(result.stdout)


def test_peer_spawn_task_prompt_emits_codex_exec_invocation_with_prompt_verbatim(
    tmp_path: Path,
) -> None:
    receipt_id = "bypass:grant-task-prompt-scenario"
    store_path = tmp_path / "bypass_lifecycles.jsonl"
    _write_synthetic_active_bypass_store(store_path, receipt_id=receipt_id)

    unique_marker = "TASK-PROMPT-SHAPE-MARKER-77f3a4c8e1d2"
    prompt_path = tmp_path / "bounded_task_prompt.txt"
    prompt_path.write_text(
        f"Write a new file at exactly:\n\n  dev/reports/dogfood/task_shape_probe.md\n\n"
        f"The file must contain ONLY this single line:\n\n  {unique_marker}\n\n"
        "Do not edit any other file. Once the file exists, stop.\n",
        encoding="utf-8",
    )

    payload = _invoke_peer_spawn(
        bypass_receipt_id=receipt_id,
        bypass_store_path=store_path,
        task_prompt_file=prompt_path,
    )

    receipt = payload.get("receipt") or {}
    script_path_str = str(receipt.get("script_path") or "")
    assert script_path_str, (
        "peer-spawn returned no script_path in the AgentSpawnReceipt; "
        "bounded-task launch path did not write a script. "
        f"receipt payload: {receipt!r}"
    )
    script_path = Path(script_path_str)
    assert script_path.is_file(), (
        f"AgentSpawnReceipt.script_path points at a non-existent file: "
        f"{script_path}; the bounded-task launch path is supposed to "
        "write the script before returning."
    )
    content = script_path.read_text(encoding="utf-8")

    assert "codex exec" in content, (
        "Bounded-task launch script does not invoke `codex exec`. "
        "Without that, the launched zsh wrapper has nothing to run that "
        "would perform the operator's task. Script content:\n"
        f"{content[:2000]}"
    )
    assert "--sandbox workspace-write" in content, (
        "Bounded-task launch script does not pass `--sandbox "
        "workspace-write`, which is what authorizes codex to mutate the "
        "workspace. Without it, even if codex runs, it cannot write "
        "files. Script content:\n"
        f"{content[:2000]}"
    )
    assert unique_marker in content, (
        f"Bounded-task launch script does not contain the operator's "
        f"prompt verbatim. The marker {unique_marker!r} is missing — "
        "either the prompt builder injection point was bypassed, or the "
        "multi-turn conductor prompt is still in play. Script content "
        f"(head):\n{content[:2000]}"
    )


def test_peer_spawn_task_prompt_script_omits_review_channel_supervised_wrapper(
    tmp_path: Path,
) -> None:
    """The bounded-task launch script must NOT carry the supervised
    review-channel wrapper artifacts. Their presence in the script means
    the spawn would route through the wrapper's preflight authority
    check, which fails with exit 82 when ``review_state_path`` is missing
    (the exact failure mode observed under marker
    ``PEERSPAWN-REAL-20260523T142707Z``).
    """
    receipt_id = "bypass:grant-task-prompt-no-wrapper"
    store_path = tmp_path / "bypass_lifecycles.jsonl"
    _write_synthetic_active_bypass_store(store_path, receipt_id=receipt_id)

    prompt_path = tmp_path / "bounded_task_prompt_no_wrapper.txt"
    prompt_path.write_text("noop bounded task body for wrapper-absence assertion\n", encoding="utf-8")

    payload = _invoke_peer_spawn(
        bypass_receipt_id=receipt_id,
        bypass_store_path=store_path,
        task_prompt_file=prompt_path,
    )

    script_path = Path((payload.get("receipt") or {}).get("script_path") or "")
    assert script_path.is_file(), (
        f"script_path not on disk: {script_path}"
    )
    content = script_path.read_text(encoding="utf-8")

    forbidden_markers = (
        "review_channel_launch_authority_check",
        "run_review_channel_once",
        "review_channel_inactivity_watchdog",
        "review_channel_task_complete_handoff_guard",
        "REVIEW_CHANNEL_HEADLESS_MODE",
    )
    present_markers = [m for m in forbidden_markers if m in content]
    assert not present_markers, (
        "Bounded-task launch script still carries supervised "
        "review-channel wrapper markers. These markers gate codex behind "
        "preflight authority checks that fail with exit 82 when no "
        "review_state exists, so this script would not deliver any "
        "bounded mutation:\n"
        f"  forbidden markers present: {present_markers}\n"
        f"  script_path: {script_path}\n"
        f"  script head:\n{content[:2000]}"
    )
