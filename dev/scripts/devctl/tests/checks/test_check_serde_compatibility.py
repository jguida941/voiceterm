"""Tests for check_serde_compatibility guard script."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import init_temp_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "check_serde_compatibility",
    "dev/scripts/checks/check_serde_compatibility.py",
)


class CheckSerdeCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_temp_repo_root(self, "rust/src", "rust/tests")

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_collects_tagged_deserialize_enum_without_fallback(self) -> None:
        enums = SCRIPT._collect_tagged_deserialize_enums(
            """
#[derive(Debug, Deserialize)]
#[serde(tag = "cmd")]
enum Command {
    SendPrompt,
}
"""
        )

        self.assertEqual(
            enums,
            [
                {
                    "name": "Command",
                    "line": 4,
                    "tag_style": "internal",
                    "has_other": False,
                    "documented_strictness": False,
                }
            ],
        )

    def test_collect_accepts_other_variant_and_adjacent_tagging(self) -> None:
        enums = SCRIPT._collect_tagged_deserialize_enums(
            """
#[derive(Debug, Deserialize)]
#[serde(tag = "kind", content = "data")]
enum Command {
    Ready { id: String },
    #[serde(other)]
    Unknown,
}
"""
        )

        self.assertEqual(enums[0]["tag_style"], "adjacent")
        self.assertTrue(enums[0]["has_other"])

    def test_collect_accepts_documented_strict_enum(self) -> None:
        enums = SCRIPT._collect_tagged_deserialize_enums(
            """
// serde-compat: allow reason=Protocol should fail closed on unknown command tags.
#[derive(Debug, Deserialize)]
#[serde(tag = "cmd")]
enum Command {
    SendPrompt,
}
"""
        )

        self.assertTrue(enums[0]["documented_strictness"])

    def test_collects_qualified_serde_deserialize(self) -> None:
        """Qualified path ``serde::Deserialize`` must be caught like bare ``Deserialize``."""
        enums = SCRIPT._collect_tagged_deserialize_enums(
            """
#[derive(Debug, serde::Deserialize)]
#[serde(tag = "cmd")]
enum Command {
    SendPrompt,
}
"""
        )

        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0]["name"], "Command")
        self.assertFalse(enums[0]["has_other"])

    def test_collects_global_qualified_serde_deserialize(self) -> None:
        """Global qualified path ``::serde::Deserialize`` must also be caught."""
        enums = SCRIPT._collect_tagged_deserialize_enums(
            """
#[derive(Debug, ::serde::Deserialize)]
#[serde(tag = "kind", content = "data")]
enum Event {
    Ready { id: String },
}
"""
        )

        self.assertEqual(len(enums), 1)
        self.assertEqual(enums[0]["name"], "Event")
        self.assertEqual(enums[0]["tag_style"], "adjacent")

    def test_collect_ignores_serialize_only_and_untagged_enums(self) -> None:
        enums = SCRIPT._collect_tagged_deserialize_enums(
            """
#[derive(Debug, Serialize)]
#[serde(tag = "event")]
enum Event {
    Ready,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
enum Entry {
    String(String),
}
"""
        )

        self.assertEqual(enums, [])

    def test_report_flags_new_missing_fallback_enum(self) -> None:
        path = self._write(
            "rust/src/ipc/protocol.rs",
            (
                "use serde::Deserialize;\n\n"
                "#[derive(Debug, Deserialize)]\n"
                "#[serde(tag = \"cmd\")]\n"
                "enum IpcCommand {\n"
                "    SendPrompt,\n"
                "}\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={"rust/src/ipc/protocol.rs": ""},
            mode="working-tree",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "path": "rust/src/ipc/protocol.rs",
                    "enum": "IpcCommand",
                    "line": 5,
                    "tag_style": "internal",
                    "reason": (
                        "tagged `Deserialize` enum is missing either a "
                        "`#[serde(other)]` fallback variant or a nearby "
                        "`serde-compat: allow reason=...` comment"
                    ),
                }
            ],
        )

    def test_report_ignores_existing_baseline_debt(self) -> None:
        base_text = (
            "use serde::Deserialize;\n\n"
            "#[derive(Debug, Deserialize)]\n"
            "#[serde(tag = \"cmd\")]\n"
            "enum IpcCommand {\n"
            "    SendPrompt,\n"
            "}\n"
        )
        path = self._write(
            "rust/src/ipc/protocol.rs",
            base_text + "\nfn unrelated_change() {}\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={"rust/src/ipc/protocol.rs": base_text},
            mode="working-tree",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["violations"], [])

    def test_report_ignores_test_paths(self) -> None:
        path = self._write(
            "rust/tests/protocol_tests.rs",
            (
                "use serde::Deserialize;\n\n"
                "#[derive(Debug, Deserialize)]\n"
                "#[serde(tag = \"cmd\")]\n"
                "enum IpcCommand {\n"
                "    SendPrompt,\n"
                "}\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={},
            mode="working-tree",
        )

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["files_scanned"], 0)
        self.assertEqual(report["files_skipped_tests"], 1)


if __name__ == "__main__":
    unittest.main()
