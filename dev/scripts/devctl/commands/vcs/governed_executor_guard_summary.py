"""Guard-result summaries for governed VCS packets."""

from __future__ import annotations

import json

from ...runtime import ActionResult


def guard_results_summary(result: ActionResult | None) -> str:
    """Return one compact JSON guard summary for approval packets."""
    if result is None:
        return json.dumps(
            {
                "action_id": "quality.guard_bundle",
                "status": "not_recorded",
                "reason": "guard_result_missing",
            },
            sort_keys=True,
        )
    payload = {
        "action_id": result.action_id,
        "status": result.status,
        "reason": result.reason,
    }
    return json.dumps(payload, sort_keys=True)
