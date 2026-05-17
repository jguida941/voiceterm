"""Regression tests for ``derive_operator_interaction_mode`` (rev_pkt_0463).

Covers the canonical precedence shared by startup-context, control-plane
read model, launcher discipline, ensure-follow, and reviewer-supervisor
autostart. Asserts the iterate-all-candidates behavior rather than the
earlier short-circuit-on-governance shape so the rev_pkt_0463 repro
(governance=``local_terminal`` + collaboration=``remote_control`` + active
attachment -> expect ``remote_control``) is pinned.

Per rev_pkt_3000 + rev_pkt_3003 #1 the remote-control axis fails CLOSED:
a typed source declaring ``remote_control`` only wins when the
reviewer-runtime carries a live identity-bearing attachment with a fresh
heartbeat. Each positive test below provides such an attachment; each
attached-without-heartbeat sibling proves the negative path stays
``local_terminal`` so a future regression cannot quietly re-open the
fail-open route.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from dev.scripts.devctl.runtime.operator_context import (
    derive_operator_interaction_mode,
)


def _gov(mode: str) -> SimpleNamespace:
    return SimpleNamespace(bridge_config=SimpleNamespace(operator_interaction_mode=mode))


def _live_attachment(now_utc: str) -> dict[str, object]:
    """Identity-bearing attachment with a fresh heartbeat.

    Per rev_pkt_3000 + rev_pkt_3003 #1 only ``status='attached'`` plus a
    parseable ``last_seen_utc`` (or ``attached_at_utc``) within
    ``heartbeat_ttl_seconds`` proves live remote-control presence. Identity
    fields (``remote_session_id``/``session_url``) are required for the
    deserializer to return a state at all.
    """
    return {
        "provider": "claude",
        "session_name": "remote-control-test",
        "remote_session_id": "session_test_remote_control",
        "session_url": "https://claude.ai/code/session_test_remote_control",
        "status": "attached",
        "attached_at_utc": now_utc,
        "last_seen_utc": now_utc,
    }


class DeriveOperatorInteractionModeTests(unittest.TestCase):
    def test_rev_pkt_0463_repro_collaboration_overrides_local_terminal(self) -> None:
        """Governance=local_terminal + collaboration=remote_control + live attachment -> remote_control.

        Positive-active path: collaboration declares ``remote_control`` AND
        a live identity-bearing attachment is present, so the reducer must
        promote past the governance ``local_terminal`` floor.
        """
        live_now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "collaboration": {"operator_interaction_mode": "remote_control"},
                "reviewer_runtime": {
                    "remote_control_attachment": _live_attachment(live_now_utc),
                },
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_collaboration_remote_control_without_attachment_falls_closed(self) -> None:
        """Collaboration remote_control without a live attachment must fail closed.

        Per rev_pkt_3000 + rev_pkt_3003 #1 a typed source claiming
        ``remote_control`` is not enough on its own — the reviewer-runtime
        must also carry a live attachment with a fresh heartbeat. Without
        one, the reducer falls back to the governance ``local_terminal``.
        """
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "collaboration": {"operator_interaction_mode": "remote_control"},
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "local_terminal")

    def test_reviewer_runtime_mode_overrides_local_terminal(self) -> None:
        """reviewer_runtime mode=remote_control + live attachment -> remote_control."""
        live_now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {
                    "operator_interaction_mode": "remote_control",
                    "remote_control_attachment": _live_attachment(live_now_utc),
                },
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_reviewer_runtime_remote_control_without_attachment_falls_closed(self) -> None:
        """reviewer_runtime remote_control without a live attachment falls closed.

        Complementary negative for rev_pkt_3000 + rev_pkt_3003 #1: even when
        ``reviewer_runtime.operator_interaction_mode='remote_control'`` is
        declared, the absence of a live attachment must keep the reducer at
        ``local_terminal``.
        """
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {"operator_interaction_mode": "remote_control"},
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "local_terminal")

    def test_receipt_mode_overrides_local_terminal(self) -> None:
        """receipt mode=remote_control + live attachment -> remote_control."""
        live_now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {
                    "remote_control_attachment": _live_attachment(live_now_utc),
                },
            },
            receipt={"operator_interaction_mode": "remote_control"},
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_receipt_remote_control_without_attachment_falls_closed(self) -> None:
        """Receipt-only remote_control without a live attachment falls closed.

        Complementary negative for rev_pkt_3000 + rev_pkt_3003 #1: receipt
        mode is a typed claim, not proof of remote presence, so it must not
        promote past ``local_terminal`` on its own.
        """
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload=None,
            receipt={"operator_interaction_mode": "remote_control"},
            reviewer_mode="",
        )
        self.assertEqual(mode, "local_terminal")

    def test_attachment_override_when_no_non_local_terminal_mode(self) -> None:
        """Live identity-bearing attachment alone promotes to remote_control.

        Positive-active path per rev_pkt_3000 + rev_pkt_3003 #1: when no
        typed source declares ``remote_control`` but the reviewer-runtime
        carries a live identity-bearing attachment with a fresh heartbeat,
        the attachment override must promote past the governance
        ``local_terminal`` floor.
        """
        live_now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {
                    "remote_control_attachment": _live_attachment(live_now_utc),
                },
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "remote_control")

    def test_attachment_without_heartbeat_falls_closed_to_local_terminal(self) -> None:
        """attached-without-fresh-heartbeat must NOT promote to remote_control.

        Complementary negative for rev_pkt_3000 + rev_pkt_3003 #1: an
        attachment with ``status='attached'`` but no
        ``last_seen_utc``/``attached_at_utc`` (no proof of life) is
        classified inactive by ``remote_attachment_active``, so the
        attachment override must NOT fire and the reducer must keep the
        governance ``local_terminal``. This pins the fail-closed semantics
        so the old fail-open path (UI says Remote Control, typed surface
        says local_terminal) cannot regress.
        """
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={
                "reviewer_runtime": {
                    "remote_control_attachment": {
                        "provider": "claude",
                        "session_name": "remote-control-test",
                        "remote_session_id": "session_test_no_heartbeat",
                        "session_url": "https://claude.ai/code/session_test_no_heartbeat",
                        "status": "attached",
                    },
                },
            },
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "local_terminal")

    def test_local_terminal_preserved_without_typed_overrides(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=_gov("local_terminal"),
            review_state_payload={},
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "local_terminal")

    def test_single_agent_reviewer_mode_fallback(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=None,
            review_state_payload=None,
            receipt=None,
            reviewer_mode="single_agent",
        )
        self.assertEqual(mode, "single_agent")

    def test_dual_agent_reviewer_mode_fallback(self) -> None:
        mode = derive_operator_interaction_mode(
            governance=None,
            review_state_payload=None,
            receipt=None,
            reviewer_mode="active_dual_agent",
        )
        self.assertEqual(mode, "dual_agent")

    def test_reviewer_mode_fallback_for_empty_signal(self) -> None:
        """Empty reviewer_mode + no typed signals -> ``unresolved`` (fail closed).

        Per rev_pkt_3000 + rev_pkt_3003 #1 the reducer fails closed when
        every typed source is empty. ``normalize_reviewer_mode('')`` resolves
        to the ``tools_only`` default, which is neither ``active_dual_agent``
        nor ``single_agent``, so ``derive_operator_interaction_mode`` returns
        ``unresolved`` rather than silently promoting to ``dual_agent``. Pin
        this fail-closed shape so a future change cannot quietly re-introduce
        the dual-agent default.
        """
        mode = derive_operator_interaction_mode(
            governance=None,
            review_state_payload=None,
            receipt=None,
            reviewer_mode="",
        )
        self.assertEqual(mode, "unresolved")


if __name__ == "__main__":
    unittest.main()
