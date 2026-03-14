"""Tests for package-layout compatibility-shim detection rules."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.checks.package_layout.rules import (
    STANDARD_SHIM_METADATA_FIELDS,
    detect_compatibility_shim,
)
from dev.scripts.devctl.tests.conftest import init_temp_repo_root


def _shim_metadata(
    target: str = "dev/scripts/checks/package_layout/command.py",
    *,
    expiry: str = "2026-12-31",
) -> str:
    return (
        "# shim-owner: tooling/code-governance\n"
        "# shim-reason: staged split\n"
        f"# shim-expiry: {expiry}\n"
        f"# shim-target: {target}\n"
    )


class CompatibilityShimRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(self)

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_detect_compatibility_shim_accepts_thin_wrapper_with_metadata(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from package_layout.command import main\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=2,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.metadata["owner"], "tooling/code-governance")
        self.assertEqual(result.metadata["target"], "dev/scripts/checks/package_layout/command.py")

    def test_detect_compatibility_shim_rejects_extra_logic(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from package_layout.command import main\n"
                "FLAG = True\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=6,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(result.metadata, {})

    def test_detect_compatibility_shim_ignores_shebang_and_metadata_in_line_budget(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                "#!/usr/bin/env python3\n"
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from package_layout.command import main\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=2,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertTrue(result.is_valid)

    def test_detect_compatibility_shim_requires_backward_compat_docstring(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Compatibility shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from package_layout.command import main\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=2,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertFalse(result.is_valid)

    def test_detect_compatibility_shim_requires_metadata_fields_when_configured(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                "# shim-owner: tooling/code-governance\n"
                "# shim-reason: staged split\n"
                "# shim-expiry: 2026-12-31\n"
                "from package_layout.command import main\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=2,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(result.metadata["owner"], "tooling/code-governance")
        self.assertEqual(result.missing_metadata_fields, ("target",))

    def test_detect_compatibility_shim_accepts_package_layout_namespace_targets(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.bootstrap`."""\n'
                f"{_shim_metadata(target='dev/scripts/checks/package_layout/bootstrap.py')}"
                "from package_layout import bootstrap\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=2,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertTrue(result.is_valid)

    def test_detect_compatibility_shim_rejects_wrong_namespace_target(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from other_namespace.command import main\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=2,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertFalse(result.is_valid)

    def test_detect_compatibility_shim_allows_main_delegator_shape(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from package_layout.command import main\n"
                "\n"
                'if __name__ == "__main__":\n'
                "    raise SystemExit(main())\n"
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=4,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertTrue(result.is_valid)

    def test_detect_compatibility_shim_allows_reexport_shape(self) -> None:
        path = self._write(
            "check_guard.py",
            (
                '"""Backward-compat shim -- use `package_layout.command`."""\n'
                f"{_shim_metadata()}"
                "from package_layout.command import main\n"
                '__all__ = ["main"]\n'
            ),
        )

        result = detect_compatibility_shim(
            path,
            namespace_subdir="package_layout",
            shim_max_nonblank_lines=3,
            shim_required_metadata_fields=STANDARD_SHIM_METADATA_FIELDS,
        )

        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main()
