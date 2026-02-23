"""Tests for devctl ship release/distribution safety guards."""

import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.commands import ship
from dev.scripts.devctl.commands import release_guard


def make_args() -> SimpleNamespace:
    return SimpleNamespace(
        version="1.2.3",
        verify=False,
        verify_docs=False,
        tag=False,
        notes=False,
        github=False,
        github_fail_on_no_commits=False,
        pypi=False,
        homebrew=False,
        verify_pypi=False,
        notes_output=None,
        yes=True,
        allow_ci=True,
        dry_run=True,
        format="text",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )


class ShipReleaseParityTests(TestCase):
    def test_check_release_version_parity_matches_requested_version(self) -> None:
        payload = {"ok": True, "versions_present": ["1.2.3"], "missing": []}
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

        with patch("dev.scripts.devctl.commands.release_guard.subprocess.run", return_value=completed):
            ok, details = release_guard.check_release_version_parity("1.2.3")

        self.assertTrue(ok)
        self.assertEqual(details["version"], "1.2.3")

    def test_check_release_version_parity_rejects_mismatched_requested_version(self) -> None:
        payload = {"ok": True, "versions_present": ["2.0.0"], "missing": []}
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

        with patch("dev.scripts.devctl.commands.release_guard.subprocess.run", return_value=completed):
            ok, details = release_guard.check_release_version_parity("1.2.3")

        self.assertFalse(ok)
        self.assertEqual(details["reason"], "requested version does not match release metadata")

    def test_run_verify_fails_when_release_parity_fails(self) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship.check_release_version_parity",
            return_value=(False, {"reason": "release version parity check failed"}),
        ):
            result = ship._run_verify(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "verify")
        self.assertEqual(result["details"]["reason"], "release version parity check failed")

    def test_run_pypi_fails_when_release_parity_fails(self) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship.check_release_version_parity",
            return_value=(False, {"reason": "release version parity check failed"}),
        ):
            result = ship._run_pypi(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "pypi")
        self.assertEqual(result["details"]["reason"], "release version parity check failed")

    def test_run_homebrew_fails_when_release_parity_fails(self) -> None:
        args = make_args()
        context = {"version": "1.2.3", "tag": "v1.2.3", "notes_file": "/tmp/notes.md"}

        with patch(
            "dev.scripts.devctl.commands.ship.check_release_version_parity",
            return_value=(False, {"reason": "release version parity check failed"}),
        ):
            result = ship._run_homebrew(args, context)

        self.assertFalse(result["ok"])
        self.assertEqual(result["name"], "homebrew")
        self.assertEqual(result["details"]["reason"], "release version parity check failed")
