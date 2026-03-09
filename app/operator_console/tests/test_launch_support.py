from __future__ import annotations

import unittest
from unittest.mock import patch

from app.operator_console.launch_support import (
    build_pyqt6_install_command,
    ensure_pyqt6_installed,
)


class LaunchSupportTests(unittest.TestCase):
    def test_build_install_command_uses_user_site_outside_virtualenv(self) -> None:
        command = build_pyqt6_install_command(
            python_executable="/usr/bin/python3",
            in_virtualenv=False,
        )

        self.assertEqual(
            command,
            ["/usr/bin/python3", "-m", "pip", "install", "--user", "PyQt6"],
        )

    def test_build_install_command_omits_user_site_inside_virtualenv(self) -> None:
        command = build_pyqt6_install_command(
            python_executable="/venv/bin/python",
            in_virtualenv=True,
        )

        self.assertEqual(
            command,
            ["/venv/bin/python", "-m", "pip", "install", "PyQt6"],
        )

    @patch("app.operator_console.launch_support.pyqt6_installed", return_value=True)
    @patch("app.operator_console.launch_support.subprocess.run")
    def test_ensure_pyqt6_skips_install_when_available(
        self,
        run_mock,
        _installed_mock,
    ) -> None:
        ensure_pyqt6_installed()
        run_mock.assert_not_called()

    @patch("app.operator_console.launch_support._refresh_user_site_packages")
    @patch("app.operator_console.launch_support.subprocess.run")
    @patch(
        "app.operator_console.launch_support.pyqt6_installed",
        side_effect=[False, True],
    )
    def test_ensure_pyqt6_installs_when_missing(
        self,
        _installed_mock,
        run_mock,
        refresh_mock,
    ) -> None:
        ensure_pyqt6_installed()
        run_mock.assert_called_once()
        refresh_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
