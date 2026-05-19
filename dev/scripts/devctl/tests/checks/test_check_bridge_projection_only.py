"""Tests for check_bridge_projection_only governance guard."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = (
    REPO_ROOT / "dev/scripts/checks/bridge_projection_only/command.py"
)


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_bridge_projection_only_script",
        SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load bridge_projection_only.command")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckBridgeProjectionOnlyTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _repo(self) -> Path:
        tmp_dir = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.addCleanup(tmp_dir.cleanup)
        return Path(tmp_dir.name)

    def _write(self, root: Path, rel_path: str, text: str) -> Path:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _report_for(self, root: Path) -> dict[str, object]:
        return self.script._build_report(root=root)

    def _rules(self, report: dict[str, object]) -> set[str]:
        return {
            str(violation["rule"])
            for violation in report.get("violations", [])
            if isinstance(violation, dict)
        }

    def test_current_repo_repaired_surfaces_pass(self) -> None:
        report = self.script._build_report(root=REPO_ROOT)

        self.assertTrue(report["ok"], report.get("violations"))
        self.assertEqual(report["violation_count"], 0)

    def test_flags_bridge_metadata_reviewer_mode_in_authority_surface(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/review_state_parse_support.py",
            """
def bad(bridge):
    return bridge.get("bridge_metadata_reviewer_mode")
""",
        )

        report = self._report_for(root)

        self.assertFalse(report["ok"])
        self.assertIn("bridge_metadata_reviewer_mode_forbidden", self._rules(report))

    def test_flags_bridge_projection_authority_and_provider_role_text(self) -> None:
        root = self._repo()
        self._write(
            root,
            "bridge.md",
            """
# Review Bridge

Use this file as the live Codex<->Claude coordination authority.
Codex is the reviewer. Claude is the coder.
When `Reviewer mode` is `active_dual_agent`, this file is the live reviewer/coder authority.
""",
        )

        report = self._report_for(root)

        self.assertFalse(report["ok"])
        rules = self._rules(report)
        self.assertIn("bridge_live_coordination_authority_forbidden", rules)
        self.assertIn("bridge_provider_role_assignment_forbidden", rules)
        self.assertIn("bridge_reviewer_coder_authority_forbidden", rules)
        self.assertIn("bridge_backend_authority_language_forbidden", rules)

    def test_flags_bridge_validation_without_typed_current_session(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/commands/review_channel/_bridge_poll.py",
            """
def bad(snapshot):
    return validate_live_bridge_contract(snapshot)
""",
        )

        report = self._report_for(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "bridge_validation_requires_typed_current_session",
            self._rules(report),
        )

    def test_allows_bridge_validation_with_typed_current_session(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/commands/review_channel/_bridge_poll.py",
            """
def good(snapshot, current_session):
    return validate_live_bridge_contract(
        snapshot,
        typed_current_session=current_session,
    )
""",
        )

        report = self._report_for(root)

        self.assertTrue(report["ok"], report.get("violations"))

    def test_flags_push_authorization_effective_mode_string(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/push_authorization.py",
            """
def bad(runtime):
    return runtime.effective_reviewer_mode == "tools_only"
""",
        )

        report = self._report_for(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "push_authorization_effective_mode_string_forbidden",
            self._rules(report),
        )

    def test_flags_push_authorization_active_dual_literal(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/push_authorization.py",
            """
def bad(mode):
    return mode == "active_dual_agent"
""",
        )

        report = self._report_for(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "push_authorization_active_dual_literal_forbidden",
            self._rules(report),
        )

    def test_flags_ack_literal_filter_in_bridge_poll(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/commands/review_channel/_bridge_poll.py",
            '''
_ACK_ONLY_ERROR_PREFIXES = ("Claude Ack", "Implementer Ack")

def good(snapshot, current_session):
    return validate_live_bridge_contract(
        snapshot,
        typed_current_session=current_session,
    )
''',
        )

        report = self._report_for(root)

        self.assertFalse(report["ok"])
        rules = self._rules(report)
        self.assertIn("bridge_poll_ack_filter_forbidden", rules)
        self.assertIn("bridge_poll_ack_literal_authority_forbidden", rules)
