"""Tests for shared runtime ControlState contracts."""

from __future__ import annotations

import unittest

from dev.scripts.devctl.runtime import (
    ControlStateContext,
    OperatorContext,
    OperatorInteractionMode,
    build_control_state,
    control_state_from_payload,
    operator_context_from_mapping,
)


class ControlStateTests(unittest.TestCase):
    def test_build_control_state_normalizes_mobile_review_payloads(self) -> None:
        state = build_control_state(
            controller_payload={
                "phase": "blocked",
                "reason": "review_follow_up_required",
                "controller": {
                    "plan_id": "MP-340",
                    "controller_run_id": "run-1",
                    "mode_effective": "report-only",
                    "latest_working_branch": "feature/mobile",
                },
                "loop": {
                    "unresolved_count": 2,
                    "risk": "high",
                    "next_actions": ["refresh-status"],
                },
                "source_run": {"run_url": "https://example.invalid/run/1"},
            },
            review_payload={
                "bridge_liveness": {
                    "overall_state": "stale",
                    "codex_poll_state": "stale",
                },
                "review_state": {
                    "agents": [
                        {"agent_id": "codex", "status": "stale", "role": "reviewer"},
                        {"agent_id": "claude", "status": "active", "role": "implementer"},
                    ],
                    "queue": {"pending_total": 1},
                    "bridge": {
                        "last_codex_poll_utc": "2026-03-12T00:00:00Z",
                        "last_worktree_hash": "abc123",
                        "current_instruction": "refresh the bundle",
                        "open_findings": "bridge drift",
                        "claude_status": "implementing",
                        "claude_ack": "acknowledged",
                    },
                },
            },
            context=ControlStateContext(
                approval_policy={"mode": "balanced", "summary": "Ask before write"},
                sources={"phone_input_path": "/tmp/phone.json"},
                timestamp="2026-03-12T00:00:00Z",
                warnings=("phone missing",),
            ),
        )

        self.assertEqual(state.contract_id, "ControlState")
        self.assertEqual(state.primary_run().plan_id, "MP-340")
        self.assertEqual(state.primary_run().review_bridge_state, "stale")
        self.assertEqual(state.review_bridge.last_worktree_hash, "abc123")
        self.assertEqual(state.approvals.mode, "balanced")
        self.assertEqual(state.agent_status("codex"), "stale")
        self.assertEqual(state.sources.phone_input_path, "/tmp/phone.json")

    def test_control_state_from_payload_reads_explicit_contract(self) -> None:
        state = control_state_from_payload(
            {
                "control_state": {
                    "schema_version": 1,
                    "contract_id": "ControlState",
                    "command": "mobile-status",
                    "timestamp": "2026-03-12T00:00:00Z",
                    "approvals": {"mode": "balanced", "summary": "Ask"},
                    "active_runs": [
                        {
                            "plan_id": "MP-377",
                            "controller_run_id": "run-7",
                            "phase": "running",
                            "reason": "slice_active",
                            "risk": "medium",
                            "unresolved_count": 1,
                            "pending_total": 0,
                            "mode_effective": "report-only",
                            "review_bridge_state": "fresh",
                            "codex_poll_state": "fresh",
                            "current_instruction": "continue",
                            "open_findings": "none",
                            "next_actions": ["keep going"],
                            "latest_working_branch": "feature/runtime",
                            "source_run_url": "https://example.invalid/run/7",
                        }
                    ],
                    "review_bridge": {
                        "overall_state": "fresh",
                        "codex_poll_state": "fresh",
                        "last_codex_poll_utc": "2026-03-12T00:00:00Z",
                        "last_worktree_hash": "hash-7",
                        "pending_total": 0,
                        "current_instruction": "continue",
                        "open_findings": "none",
                        "claude_status": "active",
                        "claude_ack": "acknowledged",
                    },
                    "agents": [
                        {"agent_id": "codex", "status": "active", "role": "reviewer"}
                    ],
                    "sources": {"review_channel_path": "dev/active/review_channel.md"},
                }
            }
        )

        self.assertIsNotNone(state)
        self.assertEqual(state.primary_run().controller_run_id, "run-7")
        self.assertEqual(state.review_bridge.overall_state, "fresh")
        self.assertEqual(state.agent_status("codex"), "active")

    def test_build_control_state_accepts_standalone_review_state_json(self) -> None:
        """Standalone review_state.json has top-level queue/bridge/agents keys."""
        state = build_control_state(
            controller_payload={
                "phase": "running",
                "reason": "slice_active",
                "controller": {
                    "plan_id": "MP-377",
                    "controller_run_id": "run-5",
                    "mode_effective": "autonomy",
                    "latest_working_branch": "feature/governance",
                },
                "loop": {"unresolved_count": 0, "risk": "low"},
                "source_run": {"run_url": "https://example.invalid/run/5"},
            },
            review_payload={
                "review": {
                    "plan_id": "MP-377",
                    "session_id": "session-abc",
                },
                "queue": {"pending_total": 3},
                "bridge": {
                    "last_codex_poll_utc": "2026-03-13T21:00:00Z",
                    "last_worktree_hash": "standalone-hash",
                    "current_instruction": "fix runtime boundary",
                    "open_findings": "one medium finding",
                    "claude_status": "coding",
                    "claude_ack": "ack-standalone",
                },
                "bridge_liveness": {
                    "overall_state": "fresh",
                    "codex_poll_state": "active",
                },
                "agents": [
                    {"agent_id": "codex-1", "status": "active", "role": "reviewer"},
                    {"agent_id": "claude-9", "status": "coding", "role": "implementer"},
                ],
            },
        )

        self.assertEqual(state.review_bridge.overall_state, "fresh")
        self.assertEqual(state.review_bridge.codex_poll_state, "active")
        self.assertEqual(state.review_bridge.last_worktree_hash, "standalone-hash")
        self.assertEqual(
            state.review_bridge.current_instruction, "fix runtime boundary"
        )
        self.assertEqual(state.review_bridge.open_findings, "one medium finding")
        self.assertEqual(state.review_bridge.claude_status, "coding")
        self.assertEqual(state.review_bridge.claude_ack, "ack-standalone")
        self.assertEqual(state.review_bridge.pending_total, 3)
        self.assertEqual(state.primary_run().plan_id, "MP-377")
        self.assertEqual(state.agent_status("codex-1"), "active")
        self.assertEqual(state.agent_status("claude-9"), "coding")
        self.assertEqual(len(state.agents), 2)


class OperatorInteractionModeTests(unittest.TestCase):
    """Tests for OperatorInteractionMode enum values."""

    def test_enum_values_are_string_comparable(self) -> None:
        self.assertEqual(OperatorInteractionMode.LOCAL_TERMINAL, "local_terminal")
        self.assertEqual(OperatorInteractionMode.REMOTE_CONTROL, "remote_control")
        self.assertEqual(OperatorInteractionMode.DUAL_AGENT, "dual_agent")
        self.assertEqual(OperatorInteractionMode.SINGLE_AGENT, "single_agent")

    def test_enum_from_string(self) -> None:
        mode = OperatorInteractionMode("remote_control")
        self.assertEqual(mode, OperatorInteractionMode.REMOTE_CONTROL)

    def test_enum_invalid_value_raises(self) -> None:
        with self.assertRaises(ValueError):
            OperatorInteractionMode("invalid_mode")


class OperatorContextTests(unittest.TestCase):
    """Tests for OperatorContext dataclass defaults and serialization."""

    def test_default_values(self) -> None:
        ctx = OperatorContext()
        self.assertEqual(ctx.interaction_mode, "unresolved")
        self.assertEqual(ctx.device, "desktop")
        self.assertTrue(ctx.operator_available)
        self.assertEqual(ctx.notification_channel, "terminal")

    def test_custom_values(self) -> None:
        ctx = OperatorContext(
            interaction_mode="remote_control",
            device="phone",
            operator_available=False,
            notification_channel="dashboard",
        )
        self.assertEqual(ctx.interaction_mode, "remote_control")
        self.assertEqual(ctx.device, "phone")
        self.assertFalse(ctx.operator_available)
        self.assertEqual(ctx.notification_channel, "dashboard")

    def test_frozen_immutability(self) -> None:
        ctx = OperatorContext()
        with self.assertRaises(AttributeError):
            ctx.interaction_mode = "remote_control"  # type: ignore[misc]


class OperatorContextFromMappingTests(unittest.TestCase):
    """Tests for operator_context_from_mapping deserialization."""

    def test_full_mapping(self) -> None:
        ctx = operator_context_from_mapping({
            "interaction_mode": "remote_control",
            "device": "phone",
            "operator_available": False,
            "notification_channel": "bridge",
        })
        self.assertEqual(ctx.interaction_mode, "remote_control")
        self.assertEqual(ctx.device, "phone")
        self.assertFalse(ctx.operator_available)
        self.assertEqual(ctx.notification_channel, "bridge")

    def test_empty_mapping_yields_defaults(self) -> None:
        ctx = operator_context_from_mapping({})
        self.assertEqual(ctx.interaction_mode, "unresolved")
        self.assertEqual(ctx.device, "desktop")
        self.assertTrue(ctx.operator_available)
        self.assertEqual(ctx.notification_channel, "terminal")

    def test_none_value_yields_defaults(self) -> None:
        ctx = operator_context_from_mapping(None)
        self.assertEqual(ctx.interaction_mode, "unresolved")


class ControlStateOperatorContextTests(unittest.TestCase):
    """Tests for OperatorContext threading through ControlState construction."""

    def test_build_control_state_default_operator_context(self) -> None:
        state = build_control_state(
            controller_payload={"phase": "running", "reason": "ok"},
            review_payload={},
        )
        self.assertEqual(
            state.operator_context.interaction_mode, "unresolved"
        )

    def test_build_control_state_with_explicit_operator_context(self) -> None:
        state = build_control_state(
            controller_payload={"phase": "running", "reason": "ok"},
            review_payload={},
            context=ControlStateContext(
                operator_context=OperatorContext(
                    interaction_mode="remote_control",
                    device="phone",
                ),
            ),
        )
        self.assertEqual(
            state.operator_context.interaction_mode, "remote_control"
        )
        self.assertEqual(state.operator_context.device, "phone")

    def test_control_state_from_payload_with_operator_context(self) -> None:
        state = control_state_from_payload({
            "control_state": {
                "schema_version": 1,
                "contract_id": "ControlState",
                "command": "mobile-status",
                "timestamp": "",
                "approvals": {"mode": "unknown"},
                "active_runs": [],
                "review_bridge": {},
                "agents": [],
                "sources": {},
                "operator_context": {
                    "interaction_mode": "dual_agent",
                    "device": "desktop",
                },
            },
        })
        self.assertIsNotNone(state)
        self.assertEqual(
            state.operator_context.interaction_mode, "dual_agent"
        )

    def test_to_dict_includes_operator_context(self) -> None:
        state = build_control_state(
            controller_payload={"phase": "running", "reason": "ok"},
            review_payload={},
            context=ControlStateContext(
                operator_context=OperatorContext(
                    interaction_mode="single_agent",
                ),
            ),
        )
        d = state.to_dict()
        self.assertIn("operator_context", d)
        self.assertEqual(d["operator_context"]["interaction_mode"], "single_agent")
