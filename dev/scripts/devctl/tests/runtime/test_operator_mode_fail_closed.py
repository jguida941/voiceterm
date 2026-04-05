"""Focused tests proving operator interaction mode fails closed through the typed chain.

MP-380: remote-control mode must not silently degrade to local_terminal.
MP-382: terminal-none launch must surface missing proof-of-life as typed truth.

These tests verify the full parse -> startup-context -> control-plane read model
-> session-resume chain preserves remote_control mode and rejects
unresolved/invalid modes instead of defaulting to local_terminal.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from dev.scripts.devctl.runtime.operator_context import (
    OperatorInteractionMode,
    is_remote_mode,
    is_resolved,
    resolve_operator_interaction_mode,
)
from dev.scripts.devctl.runtime.project_governance_parse import (
    bridge_config_from_mapping,
)
from dev.scripts.devctl.runtime.startup_context import (
    ReviewerGateState,
    _interaction_mode_from_reviewer_mode,
)
from dev.scripts.devctl.runtime.control_plane_read_model import (
    _default_read_model,
    control_plane_read_model_from_mapping,
)
from dev.scripts.devctl.commands.governance.session_resume_support import (
    SessionCachePacket,
    derive_interaction_mode,
    packet_from_mapping,
)
from dev.scripts.devctl.commands.review_channel.bridge_launch_headless import (
    HeadlessLaunchResult,
    HeadlessLaunchStatus,
    spawn_one_headless_session as _spawn_one_headless_session,
)


# -------------------------------------------------------
# MP-380: OperatorInteractionMode enum and helpers
# -------------------------------------------------------

class TestOperatorInteractionModeEnum(unittest.TestCase):
    """Verify the typed enum covers all expected modes."""

    def test_all_modes_present(self) -> None:
        values = {m.value for m in OperatorInteractionMode}
        self.assertIn("local_terminal", values)
        self.assertIn("remote_control", values)
        self.assertIn("dual_agent", values)
        self.assertIn("single_agent", values)
        self.assertIn("unresolved", values)

    def test_resolve_known_modes(self) -> None:
        for mode in ("local_terminal", "remote_control", "dual_agent", "single_agent"):
            result = resolve_operator_interaction_mode(mode)
            self.assertEqual(result.value, mode)

    def test_resolve_empty_is_unresolved(self) -> None:
        self.assertEqual(
            resolve_operator_interaction_mode(""),
            OperatorInteractionMode.UNRESOLVED,
        )

    def test_resolve_none_like_is_unresolved(self) -> None:
        self.assertEqual(
            resolve_operator_interaction_mode("  "),
            OperatorInteractionMode.UNRESOLVED,
        )

    def test_resolve_garbage_is_unresolved(self) -> None:
        self.assertEqual(
            resolve_operator_interaction_mode("banana"),
            OperatorInteractionMode.UNRESOLVED,
        )

    def test_is_remote_mode(self) -> None:
        self.assertTrue(is_remote_mode("remote_control"))
        self.assertTrue(is_remote_mode("dual_agent"))
        self.assertFalse(is_remote_mode("local_terminal"))
        self.assertFalse(is_remote_mode("single_agent"))
        self.assertFalse(is_remote_mode("unresolved"))

    def test_is_resolved(self) -> None:
        self.assertTrue(is_resolved("local_terminal"))
        self.assertTrue(is_resolved("remote_control"))
        self.assertTrue(is_resolved("dual_agent"))
        self.assertTrue(is_resolved("single_agent"))
        self.assertFalse(is_resolved("unresolved"))
        self.assertFalse(is_resolved(""))


# -------------------------------------------------------
# MP-380: Parse layer (project_governance_parse)
# -------------------------------------------------------

class TestBridgeConfigParseFailClosed(unittest.TestCase):
    """Verify bridge_config_from_mapping does not silently default to local_terminal."""

    def test_missing_mode_resolves_to_unresolved(self) -> None:
        config = bridge_config_from_mapping({})
        self.assertEqual(config.operator_interaction_mode, "unresolved")

    def test_empty_mode_resolves_to_unresolved(self) -> None:
        config = bridge_config_from_mapping({"operator_interaction_mode": ""})
        self.assertEqual(config.operator_interaction_mode, "unresolved")

    def test_explicit_local_terminal_preserved(self) -> None:
        config = bridge_config_from_mapping({"operator_interaction_mode": "local_terminal"})
        self.assertEqual(config.operator_interaction_mode, "local_terminal")

    def test_remote_control_preserved(self) -> None:
        config = bridge_config_from_mapping({"operator_interaction_mode": "remote_control"})
        self.assertEqual(config.operator_interaction_mode, "remote_control")

    def test_unknown_value_resolves_to_unresolved(self) -> None:
        config = bridge_config_from_mapping({"operator_interaction_mode": "magic"})
        self.assertEqual(config.operator_interaction_mode, "unresolved")


# -------------------------------------------------------
# MP-380: Startup context layer
# -------------------------------------------------------

class TestStartupContextFailClosed(unittest.TestCase):
    """Verify startup_context interaction mode resolution fails closed."""

    def test_reviewer_gate_default_is_unresolved(self) -> None:
        gate = ReviewerGateState()
        self.assertEqual(gate.operator_interaction_mode, "unresolved")

    def test_governance_remote_control_takes_precedence(self) -> None:
        result = _interaction_mode_from_reviewer_mode(
            "single_agent", governance_mode="remote_control",
        )
        self.assertEqual(result, "remote_control")

    def test_governance_dual_agent_takes_precedence(self) -> None:
        result = _interaction_mode_from_reviewer_mode(
            "single_agent", governance_mode="dual_agent",
        )
        self.assertEqual(result, "dual_agent")

    def test_empty_governance_empty_reviewer_is_unresolved(self) -> None:
        """No governance + unknown reviewer mode = unresolved, not local_terminal."""
        result = _interaction_mode_from_reviewer_mode(
            "paused", governance_mode="",
        )
        self.assertEqual(result, "unresolved")



# -------------------------------------------------------
# MP-380: Control plane read model layer
# -------------------------------------------------------

class TestControlPlaneReadModelFailClosed(unittest.TestCase):
    """Verify ControlPlaneReadModel does not silently default to local_terminal."""

    def test_default_read_model_is_unresolved(self) -> None:
        model = _default_read_model()
        self.assertEqual(model.operator_interaction_mode, "unresolved")

    def test_from_mapping_missing_mode_is_unresolved(self) -> None:
        model = control_plane_read_model_from_mapping({})
        self.assertEqual(model.operator_interaction_mode, "unresolved")

    def test_from_mapping_explicit_remote_control_preserved(self) -> None:
        model = control_plane_read_model_from_mapping({
            "operator_interaction_mode": "remote_control",
        })
        self.assertEqual(model.operator_interaction_mode, "remote_control")


# -------------------------------------------------------
# MP-380: Session resume layer
# -------------------------------------------------------

class TestSessionResumeFailClosed(unittest.TestCase):
    """Verify session-resume does not silently default to local_terminal."""

    def test_packet_default_is_unresolved(self) -> None:
        pkt = SessionCachePacket()
        self.assertEqual(pkt.interaction_mode, "unresolved")
        self.assertEqual(pkt.operator_interaction_mode, "unresolved")

    def test_derive_interaction_mode_no_sources(self) -> None:
        result = derive_interaction_mode(None, governance=None)
        self.assertEqual(result, "unresolved")

    def test_derive_interaction_mode_empty_compact(self) -> None:
        result = derive_interaction_mode({}, governance=None)
        self.assertEqual(result, "unresolved")

    def test_packet_from_mapping_missing_mode(self) -> None:
        pkt = packet_from_mapping({})
        self.assertEqual(pkt.interaction_mode, "unresolved")
        self.assertEqual(pkt.operator_interaction_mode, "unresolved")

    def test_packet_from_mapping_explicit_remote_control(self) -> None:
        pkt = packet_from_mapping({
            "interaction_mode": "remote_control",
            "operator_interaction_mode": "remote_control",
        })
        self.assertEqual(pkt.interaction_mode, "remote_control")
        self.assertEqual(pkt.operator_interaction_mode, "remote_control")


# -------------------------------------------------------
# MP-380: Full chain integration
# -------------------------------------------------------

class TestFullChainPreservesRemoteControl(unittest.TestCase):
    """Verify remote_control survives parse -> startup -> control-plane -> session-resume."""

    def test_remote_control_flows_through_parse(self) -> None:
        config = bridge_config_from_mapping({
            "operator_interaction_mode": "remote_control",
        })
        self.assertEqual(config.operator_interaction_mode, "remote_control")

    def test_remote_control_flows_through_startup(self) -> None:
        result = _interaction_mode_from_reviewer_mode(
            "active_dual_agent", governance_mode="remote_control",
        )
        self.assertEqual(result, "remote_control")

    def test_remote_control_flows_through_read_model(self) -> None:
        model = control_plane_read_model_from_mapping({
            "operator_interaction_mode": "remote_control",
        })
        self.assertEqual(model.operator_interaction_mode, "remote_control")

    def test_remote_control_flows_through_session_resume(self) -> None:
        pkt = packet_from_mapping({
            "interaction_mode": "remote_control",
            "operator_interaction_mode": "remote_control",
        })
        self.assertEqual(pkt.interaction_mode, "remote_control")
        self.assertEqual(pkt.operator_interaction_mode, "remote_control")

    def test_unresolved_never_becomes_local_terminal(self) -> None:
        """The full chain must never silently produce local_terminal from nothing."""
        config = bridge_config_from_mapping({})
        self.assertNotEqual(config.operator_interaction_mode, "local_terminal")

        gate = ReviewerGateState()
        self.assertNotEqual(gate.operator_interaction_mode, "local_terminal")

        model = _default_read_model()
        self.assertNotEqual(model.operator_interaction_mode, "local_terminal")

        pkt = SessionCachePacket()
        self.assertNotEqual(pkt.operator_interaction_mode, "local_terminal")


# -------------------------------------------------------
# MP-382: Headless launch proof-of-life
# -------------------------------------------------------

class TestHeadlessLaunchProofOfLife(unittest.TestCase):
    """Verify headless launch surfaces missing script / dead PID as typed truth."""

    def test_missing_script_returns_script_missing(self) -> None:
        result = _spawn_one_headless_session({"script_path": "/nonexistent/path.sh"})
        self.assertEqual(result.status, HeadlessLaunchStatus.SCRIPT_MISSING)
        self.assertIsNone(result.pid)

    def test_empty_script_path_returns_script_missing(self) -> None:
        result = _spawn_one_headless_session({"script_path": ""})
        self.assertEqual(result.status, HeadlessLaunchStatus.SCRIPT_MISSING)

    def test_no_script_path_key_returns_script_missing(self) -> None:
        result = _spawn_one_headless_session({})
        self.assertEqual(result.status, HeadlessLaunchStatus.SCRIPT_MISSING)

    def test_result_is_typed_dataclass(self) -> None:
        result = _spawn_one_headless_session({})
        self.assertIsInstance(result, HeadlessLaunchResult)
        self.assertIsInstance(result.status, HeadlessLaunchStatus)

    def test_headless_launch_status_enum_values(self) -> None:
        self.assertEqual(HeadlessLaunchStatus.ALIVE, "alive")
        self.assertEqual(HeadlessLaunchStatus.DEAD_ON_ARRIVAL, "dead_on_arrival")
        self.assertEqual(HeadlessLaunchStatus.SPAWN_FAILED, "spawn_failed")
        self.assertEqual(HeadlessLaunchStatus.SCRIPT_MISSING, "script_missing")


if __name__ == "__main__":
    unittest.main()
