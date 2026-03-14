"""Tests for code-shape namespace layout guard support."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import (
    init_temp_repo_root,
    load_repo_module,
    override_module_attrs,
)
from dev.scripts.devctl.quality_scan_mode import ADOPTION_BASE_REF

SCRIPT = load_repo_module(
    "package_layout_support",
    "dev/scripts/checks/package_layout/support.py",
)


class CodeShapeLayoutSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(
            self,
            "dev/scripts/devctl",
            "dev/scripts/devctl/review_channel",
            "dev/scripts/checks",
            "dev/scripts",
            "dev/guides",
            "dev/active",
        )
        self._write("AGENTS.md", "# Agents\n")
        self._write("dev/scripts/README.md", "# Scripts\n")
        self._write("dev/guides/DEVELOPMENT.md", "# Development\n")
        self._write("dev/active/MASTER_PLAN.md", "# Master Plan\n")

    def _write(self, relative_path: str, text: str = "pass\n") -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_flags_new_flat_file_for_crowded_review_channel_family(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")
        self._write("dev/scripts/devctl/review_channel_new.py")
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl"),
                flat_prefix="review_channel_",
                namespace_subdir="review_channel",
                min_family_size=8,
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel_new.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref=None,
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["reason"],
            "new_flat_namespace_module_in_crowded_family",
        )
        self.assertIn("dev/scripts/devctl/review_channel", violations[0]["guidance"])

    def test_flags_new_non_entrypoint_helper_in_flat_root(self) -> None:
        self._write("dev/scripts/checks/helper_new.py")
        flat_root_rules = (
            SCRIPT.FlatRootRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                allowed_new_globs=("check_*.py", "probe_*.py", "run_*.py", "__init__.py"),
                guidance="helpers belong in a family directory",
            ),
        )

        violations, scanned = SCRIPT.collect_flat_root_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/checks/helper_new.py")],
            read_text_from_ref=lambda path, ref: None,
            since_ref=None,
            flat_root_rules=flat_root_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["reason"], "new_flat_root_module_not_allowed")
        self.assertIn("helpers belong in a family directory", violations[0]["guidance"])

    def test_allows_new_public_entrypoint_in_flat_root(self) -> None:
        self._write("dev/scripts/checks/check_new_guard.py")
        flat_root_rules = (
            SCRIPT.FlatRootRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                allowed_new_globs=("check_*.py", "probe_*.py", "run_*.py", "__init__.py"),
            ),
        )

        violations, scanned = SCRIPT.collect_flat_root_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/checks/check_new_guard.py")],
            read_text_from_ref=lambda path, ref: None,
            since_ref=None,
            flat_root_rules=flat_root_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(violations, [])

    def test_ignores_existing_flat_file_modification(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl"),
                flat_prefix="review_channel_",
                namespace_subdir="review_channel",
                min_family_size=8,
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del ref
            if path.as_posix() == "dev/scripts/devctl/review_channel_2.py":
                return "existing content\n"
            return None

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel_2.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref=None,
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(violations, [])

    def test_ignores_files_already_under_namespace_directory(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")
        self._write("dev/scripts/devctl/review_channel/new_parser.py")
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl"),
                flat_prefix="review_channel_",
                namespace_subdir="review_channel",
                min_family_size=8,
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel/new_parser.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref="origin/develop",
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 0)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(violations, [])

    def test_flags_docs_sync_when_new_namespace_path_lacks_doc_token(self) -> None:
        self._write("dev/scripts/devctl/review_channel/new_lane.py")
        docs_sync_rules = (
            SCRIPT.NamespaceDocsSyncRule(
                namespace_root=Path("dev/scripts/devctl/review_channel"),
                required_docs=(
                    Path("AGENTS.md"),
                    Path("dev/scripts/README.md"),
                    Path("dev/guides/DEVELOPMENT.md"),
                    Path("dev/active/MASTER_PLAN.md"),
                ),
                required_token="dev/scripts/devctl/review_channel",
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, scanned = SCRIPT.collect_namespace_docs_sync_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel/new_lane.py")],
            read_text_from_ref=_read_text_from_ref,
            read_text_from_worktree=lambda path: (self.root / path).read_text(encoding="utf-8"),
            since_ref=None,
            docs_sync_rules=docs_sync_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["reason"], "new_namespace_path_missing_docs_reference")

    def test_docs_sync_passes_when_required_token_is_documented(self) -> None:
        self._write(
            "dev/scripts/README.md",
            "# Scripts\n\n- Namespace: `dev/scripts/devctl/review_channel`\n",
        )
        self._write("dev/scripts/devctl/review_channel/new_lane.py")
        docs_sync_rules = (
            SCRIPT.NamespaceDocsSyncRule(
                namespace_root=Path("dev/scripts/devctl/review_channel"),
                required_docs=(
                    Path("AGENTS.md"),
                    Path("dev/scripts/README.md"),
                    Path("dev/guides/DEVELOPMENT.md"),
                    Path("dev/active/MASTER_PLAN.md"),
                ),
                required_token="dev/scripts/devctl/review_channel",
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del path
            del ref
            return None

        violations, scanned = SCRIPT.collect_namespace_docs_sync_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel/new_lane.py")],
            read_text_from_ref=_read_text_from_ref,
            read_text_from_worktree=lambda path: (self.root / path).read_text(encoding="utf-8"),
            since_ref=None,
            docs_sync_rules=docs_sync_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(violations, [])

    def test_rules_can_be_loaded_from_guard_config(self) -> None:
        for idx in range(8):
            self._write(f"dev/scripts/devctl/review_channel_{idx}.py")
        self._write("dev/scripts/devctl/review_channel_new.py")
        override_module_attrs(
            self,
            SCRIPT,
            resolve_guard_config=lambda script_id, repo_root: {
                "namespace_family_rules": [
                    {
                        "root": "dev/scripts/devctl",
                        "flat_prefix": "review_channel_",
                        "namespace_subdir": "review_channel",
                        "min_family_size": 8,
                    }
                ]
            },
        )

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/review_channel_new.py")],
            read_text_from_ref=lambda path, ref: None,
            since_ref=None,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(len(violations), 1)

    def test_namespace_family_freeze_reports_baseline_without_blocking_existing_edit(
        self,
    ) -> None:
        for idx in range(6):
            self._write(f"dev/scripts/devctl/commands/check_guard_{idx}.py")
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl/commands"),
                flat_prefix="check_",
                namespace_subdir="check",
                min_family_size=4,
                enforcement_mode="freeze",
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del ref
            if path.as_posix() == "dev/scripts/devctl/commands/check_guard_2.py":
                return "existing content\n"
            return None

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/commands/check_guard_2.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref=None,
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(violations, [])

    def test_namespace_family_strict_blocks_existing_edit(self) -> None:
        for idx in range(6):
            self._write(f"dev/scripts/devctl/commands/check_guard_{idx}.py")
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl/commands"),
                flat_prefix="check_",
                namespace_subdir="check",
                min_family_size=4,
                enforcement_mode="strict",
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del ref
            if path.as_posix() == "dev/scripts/devctl/commands/check_guard_2.py":
                return "existing content\n"
            return None

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/devctl/commands/check_guard_2.py")],
            read_text_from_ref=_read_text_from_ref,
            since_ref=None,
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["reason"],
            "changed_flat_namespace_module_in_crowded_family",
        )

    def test_namespace_family_adoption_scan_blocks_baseline_crowding(self) -> None:
        for idx in range(6):
            self._write(f"dev/scripts/devctl/commands/check_guard_{idx}.py")
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl/commands"),
                flat_prefix="check_",
                namespace_subdir="check",
                min_family_size=4,
                enforcement_mode="freeze",
            ),
        )

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[],
            read_text_from_ref=lambda path, ref: None,
            since_ref=ADOPTION_BASE_REF,
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 6)
        self.assertEqual(len(crowded_families), 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["reason"],
            "crowded_namespace_family_baseline_violation",
        )

    def test_namespace_family_adoption_scan_excludes_approved_shims_from_baseline(self) -> None:
        for idx in range(4):
            self._write(f"dev/scripts/devctl/commands/check_guard_{idx}.py")
        for idx in range(2):
            self._write(
                f"dev/scripts/devctl/commands/check_legacy_{idx}.py",
                '"""Backward-compat shim -- use devctl.commands.check."""\n'
                f"from .check.legacy_{idx} import *  # noqa: F401,F403\n",
            )
        family_rules = (
            SCRIPT.NamespaceFamilyRule(
                root=Path("dev/scripts/devctl/commands"),
                flat_prefix="check_",
                namespace_subdir="check",
                min_family_size=5,
                enforcement_mode="freeze",
            ),
        )

        violations, crowded_families, scanned = SCRIPT.collect_namespace_layout_violations(
            repo_root=self.root,
            changed_paths=[],
            read_text_from_ref=lambda path, ref: None,
            since_ref=ADOPTION_BASE_REF,
            family_rules=family_rules,
        )

        self.assertEqual(scanned, 0)
        self.assertEqual(crowded_families, [])
        self.assertEqual(violations, [])

    def test_flat_root_rules_can_be_loaded_from_package_layout_guard_config(self) -> None:
        self._write("dev/scripts/checks/helper_new.py")
        override_module_attrs(
            self,
            SCRIPT,
            resolve_guard_config=lambda script_id, repo_root: {
                "flat_root_rules": [
                    {
                        "root": "dev/scripts/checks",
                        "include_globs": ["*.py"],
                        "allowed_new_globs": ["check_*.py", "probe_*.py", "run_*.py"],
                    }
                ]
            }
            if script_id == "package_layout"
            else {},
        )

        violations, scanned = SCRIPT.collect_flat_root_violations(
            repo_root=self.root,
            changed_paths=[Path("dev/scripts/checks/helper_new.py")],
            read_text_from_ref=lambda path, ref: None,
            since_ref=None,
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)

    def test_directory_crowding_freeze_blocks_new_file_in_crowded_root(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write("dev/scripts/checks/check_guard_new.py")
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                guidance="crowded roots are frozen",
                recommended_subdir="package_layout",
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(crowded_directories[0]["root"], "dev/scripts/checks")
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["reason"], "new_file_in_crowded_directory")
        self.assertIn("package_layout", violations[0]["guidance"])

    def test_directory_crowding_freeze_reports_baseline_without_blocking_existing_edit(
        self,
    ) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del ref
            if path.as_posix() == "dev/scripts/checks/check_guard_2.py":
                return "existing content\n"
            return None

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_2.py")],
                read_text_from_ref=_read_text_from_ref,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(violations, [])

    def test_directory_crowding_allows_new_thin_wrapper_shim(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write(
            "dev/scripts/checks/check_guard_new.py",
            '"""Backward-compat shim."""\nfrom package_layout.command import main\n',
        )
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
                shim_contains_all=("Backward-compat shim", "from package_layout.command import main"),
                shim_max_nonblank_lines=4,
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(violations, [])

    def test_directory_crowding_allows_shim_with_export_list(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write(
            "dev/scripts/checks/check_guard_new.py",
            '"""Backward-compat shim."""\n'
            "from package_layout.command import main\n"
            '__all__ = ["main"]\n',
        )
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
                shim_contains_all=("Backward-compat shim", "from package_layout.command import main"),
                shim_max_nonblank_lines=6,
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(violations, [])

    def test_directory_crowding_allows_generic_package_layout_wrapper_with_metadata(
        self,
    ) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write(
            "dev/scripts/checks/check_guard_new.py",
            '"""Backward-compat shim -- use `package_layout.probe_compatibility_shims`.'
            '"""\n'
            "# shim-owner: tooling/code-governance\n"
            "# shim-reason: preserve the stable probe entrypoint during package split\n"
            "# shim-expiry: 2026-06-30\n"
            "# shim-target: dev/scripts/checks/package_layout/probe_compatibility_shims.py\n"
            "from __future__ import annotations\n"
            "from package_layout.probe_compatibility_shims import main\n"
            'if __name__ == "__main__":\n'
            "    raise SystemExit(main())\n",
        )
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
                shim_max_nonblank_lines=6,
                shim_required_metadata_fields=("owner", "reason", "expiry", "target"),
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(violations, [])

    def test_directory_crowding_rejects_short_wrapper_with_extra_logic(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write(
            "dev/scripts/checks/check_guard_new.py",
            '"""Backward-compat shim."""\n'
            "from package_layout.command import main\n"
            "FLAG = True\n",
        )
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
                shim_contains_all=("Backward-compat shim", "from package_layout.command import main"),
                shim_max_nonblank_lines=4,
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["reason"], "new_file_in_crowded_directory")

    def test_directory_crowding_metadata_required_for_shim_exemption(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write(
            "dev/scripts/checks/check_guard_new.py",
            '"""Backward-compat shim."""\nfrom package_layout.command import main\n',
        )
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
                shim_contains_all=("Backward-compat shim", "from package_layout.command import main"),
                shim_max_nonblank_lines=6,
                shim_required_metadata_fields=("owner", "reason", "expiry", "target"),
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(len(violations), 1)
        self.assertIn("shim-owner", violations[0]["guidance"])
        self.assertIn("shim-target", violations[0]["guidance"])

    def test_directory_crowding_adoption_scan_excludes_approved_shims_from_baseline(self) -> None:
        for idx in range(4):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write(
            "dev/scripts/checks/check_guard_shim.py",
            '"""Backward-compat shim."""\nfrom package_layout.command import main\n',
        )
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
                shim_contains_all=("Backward-compat shim", "from package_layout.command import main"),
                shim_max_nonblank_lines=4,
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[],
                read_text_from_ref=lambda path, ref: None,
                since_ref=ADOPTION_BASE_REF,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 0)
        self.assertEqual(crowded_directories, [])
        self.assertEqual(violations, [])

    def test_directory_crowding_adoption_scan_blocks_baseline_crowding(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="freeze",
                recommended_subdir="package_layout",
            ),
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[],
                read_text_from_ref=lambda path, ref: None,
                since_ref=ADOPTION_BASE_REF,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 5)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["reason"],
            "crowded_directory_baseline_violation",
        )

    def test_directory_crowding_strict_blocks_existing_edit_in_crowded_root(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        crowding_rules = (
            SCRIPT.DirectoryCrowdingRule(
                root=Path("dev/scripts/checks"),
                include_globs=("*.py",),
                max_files=4,
                enforcement_mode="strict",
                guidance="strict crowded roots block all flat edits",
            ),
        )

        def _read_text_from_ref(path: Path, ref: str) -> str | None:
            del ref
            if path.as_posix() == "dev/scripts/checks/check_guard_2.py":
                return "existing content\n"
            return None

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_2.py")],
                read_text_from_ref=_read_text_from_ref,
                since_ref=None,
                crowding_rules=crowding_rules,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["reason"], "changed_file_in_crowded_directory")

    def test_directory_crowding_rules_can_be_loaded_from_guard_config(self) -> None:
        for idx in range(5):
            self._write(f"dev/scripts/checks/check_guard_{idx}.py")
        self._write("dev/scripts/checks/check_guard_new.py")
        override_module_attrs(
            self,
            SCRIPT,
            resolve_guard_config=lambda script_id, repo_root: {
                "directory_crowding_rules": [
                    {
                        "root": "dev/scripts/checks",
                        "include_globs": ["*.py"],
                        "max_files": 4,
                        "enforcement_mode": "freeze",
                        "recommended_subdir": "package_layout",
                    }
                ]
            }
            if script_id == "package_layout"
            else {},
        )

        violations, crowded_directories, scanned = (
            SCRIPT.collect_directory_crowding_violations(
                repo_root=self.root,
                changed_paths=[Path("dev/scripts/checks/check_guard_new.py")],
                read_text_from_ref=lambda path, ref: None,
                since_ref=None,
            )
        )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(crowded_directories), 1)
        self.assertEqual(len(violations), 1)


if __name__ == "__main__":
    unittest.main()
