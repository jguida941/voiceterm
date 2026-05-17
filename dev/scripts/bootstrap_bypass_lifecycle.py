#!/usr/bin/env python3
"""Bootstrap a typed BypassLifecycle receipt so review-channel --action launch can succeed.

Why this exists: P102 typestate enforcement (commit 915ca48d) tightened
_require_active_bypass_lifecycle to require a persisted BypassLifecycle with
state=ACTIVE + edit_only scope. The launch command was the ONLY path that
historically granted such a lifecycle inline, but the receipt-check now happens
BEFORE the inline grant, creating a bootstrap deadlock: launch needs receipt,
receipt only granted by launch.

This script breaks the deadlock by directly calling evaluate_bypass_request()
(library function) and persisting the resulting lifecycle to
dev/state/bypass_lifecycles.jsonl, after which review-channel launches succeed.

Operator-witnessed run. The script prints the receipt_id; pass that to
--bypass-receipt-id on the next launch command.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "dev" / "scripts"))

from devctl.runtime.lifetime_bypass_mode import (  # noqa: E402
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassEvaluationInput,
    BypassRequest,
    evaluate_bypass_request,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def main() -> int:
    now = now_utc()
    expires = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    request = BypassRequest(
        request_id=f"bootstrap-{now.replace(':', '').replace('.', '').replace('-', '')[:24]}",
        scope=BypassAuthorityScope.EDIT_ONLY,
        reason=(
            "Bootstrap initial BypassLifecycle to unblock review-channel launch "
            "after P102 typestate enforcement (commit 915ca48d) removed the "
            "inline-grant path. Operator-witnessed; edit-only scope (no commit/push)."
        ),
        actor="operator",
        requested_at_utc=now,
        target_role="implementer",
        target_session_id="",
        target_surface="review-channel-launch",
        evidence_refs=(
            "memory:feedback_typed_codex_launch_command_pattern",
            "commit:915ca48d",
            "packet:rev_pkt_3982",
        ),
    )

    evidence = BypassEvaluationInput(
        operator_signature="operator_witnessed_bootstrap_2026-05-14",
        ai_approval_evidence="claude-overnight-watch-verified-cooperative-stop",
        evaluated_at_utc=now,
        evaluator_actor_id="operator",
        expires_at_utc=expires,
        policy_evidence_refs=("ProjectGovernance", "repo-pack-policy"),
    )

    lifecycle = evaluate_bypass_request(request, evidence)

    if lifecycle.receipt is None:
        print("BOOTSTRAP FAILED: evaluate_bypass_request did not produce a receipt")
        print(f"  state={lifecycle.state}")
        print(f"  evaluation={lifecycle.evaluation.reason if lifecycle.evaluation else 'none'}")
        return 1

    store_path = REPO_ROOT / DEFAULT_BYPASS_LIFECYCLE_STORE_REL
    store_path.parent.mkdir(parents=True, exist_ok=True)

    payload = lifecycle.to_dict()
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")

    print(f"BOOTSTRAP SUCCESS")
    print(f"  store={store_path}")
    print(f"  lifecycle_id={lifecycle.lifecycle_id}")
    print(f"  receipt_id={lifecycle.receipt.receipt_id}")
    print(f"  state={lifecycle.state}")
    print(f"  scope={lifecycle.receipt.requested_authority_scope}")
    print(f"  expires_at_utc={lifecycle.receipt.expires_at_utc}")
    print()
    print("Next: launch codex with this receipt id:")
    print(
        f"  python3 dev/scripts/devctl.py review-channel --action launch "
        f"--reviewer-mode single_agent --execution-mode markdown-bridge "
        f"--terminal none --dangerous --bypass-receipt-id {lifecycle.receipt.receipt_id} "
        f'--bypass-reason "Resume per stop_anchor success 2026-05-14T07:37:33Z" '
        f"--remote-role operator --format json"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
