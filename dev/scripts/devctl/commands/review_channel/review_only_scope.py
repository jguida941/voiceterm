"""Reviewer-only launch scope helper (rev_pkt_2892 Finding 2 fix).

Extracted from `bridge_action_support` to keep that module under the Python
shape soft limit. Pairs with `runtime/startup_gate._is_review_only_reviewer_launch`
so the startup-gate short-circuit and the launch-roster restriction agree on
the scope: both must require the same explicit flag pair, and both must
apply at the same time, so a launch cannot skip startup authority while
still spawning implementer-capable sessions.
"""

from __future__ import annotations


def is_reviewer_only_launch_scope(args) -> bool:
    """Return True iff the launch was declared as a non-mutating reviewer.

    Requires explicit `--policy-hint review_only` plus `--remote-role reviewer`.
    Both flags must be set; the policy_hint flag alone is not sufficient
    because it may be a default value, and the remote_role flag alone does
    not signal reviewer-only intent.
    """
    policy_hint = str(getattr(args, "policy_hint", "") or "").strip().lower()
    remote_role = str(getattr(args, "remote_role", "") or "").strip().lower()
    return policy_hint == "review_only" and remote_role == "reviewer"
