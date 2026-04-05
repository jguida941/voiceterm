"""Tests verifying phone, mobile-status, and view-phone use ControlPlaneReadModel.

Each command derives governance state from the single frozen read model
rather than computing it independently.  Tests inject controlled sources
via ``sources_override`` / ``git_override`` so no filesystem or git is needed.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.view_phone import (
    _derive_next_actor,
    phone_payload_from_read_model,
    render_phone_summary,
)
from dev.scripts.devctl.runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)

_DUMMY_ROOT = Path("/tmp/nonexistent")


def _empty_sources() -> dict:
    return {
        "receipt": None, "review_state": None, "push_report": None,
        "publisher_hb": None, "supervisor_hb": None,
        "codex_conductor": None, "claude_conductor": None,
        "full_json": None, "compact_json": None,
    }


def _base_git() -> dict:
    return {"branch": "feature/test", "head": "abc1234", "clean": True, "ahead": 0}


def _build_model(**overrides: object) -> ControlPlaneReadModel:
    """Build a read model with controlled sources, applying field overrides."""
    sources = _empty_sources()
    git = _base_git()
    for key, val in overrides.items():
        if key in sources:
            sources[key] = val
        elif key in git:
            git[key] = val
    return build_control_plane_read_model(_DUMMY_ROOT, sources_override=sources, git_override=git)


def _phone_args(root: Path, **kw: object) -> SimpleNamespace:
    defaults = dict(
        phone_json=str(root / "latest.json"), repo_root=str(root),
        view="compact", emit_projections=None, format="json",
        output=str(root / "report.json"), json_output=None,
        pipe_command=None, pipe_args=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _mobile_args(root: Path, **kw: object) -> SimpleNamespace:
    defaults = dict(
        phone_json=str(root / "phone.json"),
        review_channel_path=str(root / "review_channel.md"),
        bridge_path=str(root / "bridge.md"),
        review_status_dir=str(root / "review-status"),
        repo_root=str(root), approval_mode="balanced", execution_mode="auto",
        view="compact", emit_projections=None, format="json",
        output=str(root / "report.json"), json_output=None,
        pipe_command=None, pipe_args=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


_REVIEW_CHANNEL_TEXT = "\n".join([
    "# Review Channel + Shared Screen Plan", "",
    "## Transitional Markdown Bridge (Current Operating Mode)", "",
    "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
    "|---|---|---|---|---|---|",
    "| `AGENT-1` | Codex review | `dev/active/review_channel.md` | `MP-340` | `../wt-a1` | `feature/a1` |",
    "| `AGENT-9` | Claude fixes | `dev/active/review_channel.md` | `MP-340` | `../wt-a9` | `feature/a9` |",
])

_BRIDGE_TEXT = "\n".join([
    "# Review Bridge", "",
    "- Last Codex poll: `2026-03-09T04:12:49Z`", "",
    "## Poll Status", "", "- active reviewer loop", "",
    "## Current Verdict", "", "- still in progress", "",
    "## Open Findings", "", "- none", "",
    "## Current Instruction For Claude", "", "- continue", "",
    "## Claude Status", "", "- working", "",
    "## Claude Questions", "", "- none", "",
    "## Claude Ack", "", "- ack", "",
    "## Last Reviewed Scope", "", "- bridge.md",
])


# -- view_phone: phone_payload_from_read_model tests -------------------------

class ViewPhonePayloadTests(unittest.TestCase):
    def test_payload_contains_resolved_phase(self) -> None:
        payload = phone_payload_from_read_model(_build_model())
        self.assertEqual(payload["resolved_phase"], "idle")
        self.assertEqual(payload["command"], "view")
        self.assertEqual(payload["surface"], "phone")

    def test_payload_reflects_push_eligible(self) -> None:
        payload = phone_payload_from_read_model(
            _build_model(receipt={"push_action": "run_devctl_push"}),
        )
        self.assertTrue(payload["push_eligible"])

    def test_infra_label_counts_running_daemons(self) -> None:
        payload = phone_payload_from_read_model(
            _build_model(publisher_hb={"pid": 1}, supervisor_hb={"pid": 2}),
        )
        self.assertIn("2 daemons running", payload["infra_label"])

    def test_infra_label_singular(self) -> None:
        payload = phone_payload_from_read_model(_build_model(publisher_hb={"pid": 1}))
        self.assertIn("1 daemon running", payload["infra_label"])

    def test_pending_actions_from_model(self) -> None:
        model = _build_model(review_state={"packets": [
            {"status": "pending", "packet_id": "p1"},
            {"status": "pending", "packet_id": "p2"},
        ]})
        self.assertEqual(phone_payload_from_read_model(model)["pending_actions"], 2)

    def test_top_blocker_from_guard_failure(self) -> None:
        model = _build_model(push_report={
            "preflight_step": {"returncode": 1},
            "violations": [{"step_name": "code_shape", "summary": "too long"}],
        })
        payload = phone_payload_from_read_model(model)
        self.assertIn("guard fail", payload["top_blocker"])
        self.assertFalse(payload["last_guard_ok"])


class DeriveNextActorTests(unittest.TestCase):
    def test_blocked_returns_operator(self) -> None:
        self.assertEqual(_derive_next_actor(_build_model(receipt={"implementation_blocked": True})), "operator")

    def test_guard_fail_returns_implementer(self) -> None:
        self.assertEqual(_derive_next_actor(_build_model(push_report={"preflight_step": {"returncode": 1}})), "implementer")

    def test_push_eligible_returns_operator(self) -> None:
        self.assertEqual(_derive_next_actor(_build_model(receipt={"push_action": "run_devctl_push"})), "operator")

    def test_default_returns_implementer(self) -> None:
        self.assertEqual(_derive_next_actor(_build_model()), "implementer")


class RenderPhoneSummaryTests(unittest.TestCase):
    def _patched_render(self, fmt: str) -> str:
        with patch("dev.scripts.devctl.commands.view_phone.build_control_plane_read_model", return_value=_build_model()):
            return render_phone_summary(SimpleNamespace(format=fmt))

    def test_json_output_is_valid(self) -> None:
        payload = json.loads(self._patched_render("json"))
        self.assertEqual(payload["surface"], "phone")
        self.assertIn("resolved_phase", payload)

    def test_markdown_output_has_phase_header(self) -> None:
        output = self._patched_render("md")
        self.assertIn("## IDLE", output)
        self.assertIn("Blocker:", output)


# -- phone_status: control_plane enrichment tests ----------------------------

class PhoneStatusControlPlaneTests(unittest.TestCase):
    def test_report_includes_control_plane_section(self) -> None:
        from dev.scripts.devctl.commands import phone_status
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "latest.json").write_text(
                json.dumps({"command": "autonomy-phone-status", "phase": "idle"}), encoding="utf-8",
            )
            args = _phone_args(root)
            with patch("dev.scripts.devctl.commands.phone_status.build_control_plane_read_model", return_value=_build_model()):
                rc = phone_status.run(args)
            self.assertEqual(rc, 0)
            cp = json.loads((root / "report.json").read_text(encoding="utf-8"))["control_plane"]
            self.assertEqual(cp["resolved_phase"], "idle")
            self.assertFalse(cp["push_eligible"])
            self.assertTrue(cp["last_guard_ok"])

    def test_control_plane_present_even_on_load_error(self) -> None:
        from dev.scripts.devctl.commands import phone_status
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            args = _phone_args(root, phone_json=str(root / "missing.json"))
            with patch("dev.scripts.devctl.commands.phone_status.build_control_plane_read_model", return_value=_build_model()):
                rc = phone_status.run(args)
            self.assertEqual(rc, 1)
            report = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertIn("resolved_phase", report["control_plane"])


# -- mobile_status: control_plane enrichment tests ---------------------------

class MobileStatusControlPlaneTests(unittest.TestCase):
    def test_report_includes_control_plane(self) -> None:
        from dev.scripts.devctl.commands import mobile_status
        model = _build_model(receipt={"push_action": "await_checkpoint"})
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "phone.json").write_text(json.dumps({
                "command": "autonomy-phone-status", "phase": "idle",
                "controller": {"plan_id": "MP-1"},
            }), encoding="utf-8")
            (root / "review_channel.md").write_text(_REVIEW_CHANNEL_TEXT, encoding="utf-8")
            (root / "bridge.md").write_text(_BRIDGE_TEXT, encoding="utf-8")
            args = _mobile_args(root)
            with patch("dev.scripts.devctl.commands.mobile_status.build_control_plane_read_model", return_value=model):
                rc = mobile_status.run(args)
            self.assertEqual(rc, 0)
            cp = json.loads((root / "report.json").read_text(encoding="utf-8"))["control_plane"]
            self.assertEqual(cp["resolved_phase"], "idle")
            self.assertFalse(cp["push_eligible"])
            self.assertEqual(cp["next_action"], "await_checkpoint")

    def test_control_plane_empty_on_error(self) -> None:
        from dev.scripts.devctl.commands import mobile_status
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            args = _mobile_args(
                root, phone_json=str(root / "missing.json"),
                review_channel_path=str(root / "missing.md"),
                bridge_path=str(root / "missing_bridge.md"),
                review_status_dir=str(root / "missing-status"),
            )
            rc = mobile_status.run(args)
            self.assertEqual(rc, 1)
            report = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertEqual(report["control_plane"], {})


class AutoModeImplementerLivenessWiringTests(unittest.TestCase):
    """Verify implementer liveness propagates from read model to auto-mode."""

    def test_claude_conductor_alive_maps_to_implementer_alive(self) -> None:
        """ControlPlaneReadModel.claude_conductor_alive drives implementer_alive."""
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )
        from dev.scripts.devctl.runtime.auto_mode import resolve_auto_mode_phase
        from dev.scripts.devctl.runtime.control_plane_read_model import (
            ControlPlaneReadModel,
        )

        model = ControlPlaneReadModel(
            timestamp="2026-04-04T12:00:00Z",
            branch="feature/test",
            head_sha="abc1234",
            worktree_clean=True,
            ahead_of_upstream=0,
            resolved_phase="idle",
            push_eligible=False,
            implementation_blocked=False,
            top_blocker="none",
            next_action="n/a",
            next_command="",
            reviewer_mode="single_agent",
            operator_interaction_mode="local_terminal",
            reviewer_freshness="--",
            review_accepted=False,
            last_reviewed_sha="",
            attention_status="n/a",
            attention_summary="n/a",
            publisher_running=False,
            supervisor_running=False,
            codex_conductor_alive=False,
            claude_conductor_alive=True,
            pending_action_requests=0,
            last_guard_ok=True,
            check_details=(),
        )
        inputs = inputs_from_read_model(model)
        self.assertEqual(inputs.implementer_status, "active")
        state = resolve_auto_mode_phase(inputs)
        self.assertTrue(state.implementer_alive)

    def test_dead_conductor_means_implementer_not_alive(self) -> None:
        """When claude_conductor_alive is False, implementer_alive must be False."""
        from dev.scripts.devctl.commands.auto_mode_status import (
            inputs_from_read_model,
        )
        from dev.scripts.devctl.runtime.auto_mode import resolve_auto_mode_phase

        model = _build_model()
        inputs = inputs_from_read_model(model)
        self.assertEqual(inputs.implementer_status, "")
        state = resolve_auto_mode_phase(inputs)
        self.assertFalse(state.implementer_alive)


if __name__ == "__main__":
    unittest.main()
