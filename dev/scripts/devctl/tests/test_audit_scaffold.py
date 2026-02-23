"""Tests for devctl audit-scaffold command behavior."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import audit_scaffold


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "since_ref": None,
        "head_ref": "HEAD",
        "source_guards": True,
        "output_path": "dev/active/RUST_AUDIT_FINDINGS.md",
        "template_path": "dev/config/templates/rust_audit_findings_template.md",
        "trigger": "manual",
        "trigger_steps": None,
        "force": False,
        "yes": True,
        "dry_run": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class AuditScaffoldParserTests(TestCase):
    def test_cli_accepts_audit_scaffold_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "audit-scaffold",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD",
                "--force",
                "--yes",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "audit-scaffold")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD")
        self.assertTrue(args.force)
        self.assertTrue(args.yes)
        self.assertEqual(args.format, "json")


class AuditScaffoldCommandTests(TestCase):
    @patch("dev.scripts.devctl.commands.audit_scaffold.write_output")
    def test_rejects_output_path_outside_active_root(self, write_output_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            template = root / "dev/config/templates/rust_audit_findings_template.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# template", encoding="utf-8")

            args = make_args(
                output_path="tmp/report.md",
                template_path="dev/config/templates/rust_audit_findings_template.md",
                force=True,
            )
            with patch("dev.scripts.devctl.commands.audit_scaffold.REPO_ROOT", root), patch(
                "dev.scripts.devctl.commands.audit_scaffold.ACTIVE_ROOT",
                (root / "dev/active").resolve(),
            ):
                rc = audit_scaffold.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(any("dev/active/" in error for error in payload["errors"]))

    @patch("dev.scripts.devctl.commands.audit_scaffold._run_guard")
    @patch("dev.scripts.devctl.commands.audit_scaffold.write_output")
    def test_generates_scaffold_markdown_from_guard_findings(
        self,
        write_output_mock,
        run_guard_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            active_dir = (root / "dev/active").resolve()
            active_dir.mkdir(parents=True, exist_ok=True)
            template = root / "dev/config/templates/rust_audit_findings_template.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text(
                "\n".join(
                    [
                        "# Template",
                        "{{SUMMARY_TABLE}}",
                        "{{FINDINGS}}",
                        "{{ACTION_ITEMS}}",
                        "{{RANGE}}",
                        "{{TRIGGER}}",
                        "{{TRIGGER_STEPS}}",
                    ]
                ),
                encoding="utf-8",
            )

            run_guard_mock.side_effect = [
                {
                    "name": "code-shape-guard",
                    "script_id": "code_shape",
                    "severity": "high",
                    "focus": "modularity",
                    "cmd": ["python3"],
                    "returncode": 1,
                    "ok": False,
                    "skipped": False,
                    "violations": [
                        {"path": "src/src/bin/voiceterm/event_loop.rs", "reason": "crossed_soft_limit"}
                    ],
                    "error": None,
                    "stderr_tail": "",
                    "report": {"ok": False},
                },
                {
                    "name": "rust-lint-debt-guard",
                    "script_id": "rust_lint_debt",
                    "severity": "high",
                    "focus": "lint debt",
                    "cmd": ["python3"],
                    "returncode": 0,
                    "ok": True,
                    "skipped": False,
                    "violations": [],
                    "error": None,
                    "stderr_tail": "",
                    "report": {"ok": True},
                },
                {
                    "name": "rust-best-practices-guard",
                    "script_id": "rust_best_practices",
                    "severity": "high",
                    "focus": "best practices",
                    "cmd": ["python3"],
                    "returncode": 0,
                    "ok": True,
                    "skipped": False,
                    "violations": [],
                    "error": None,
                    "stderr_tail": "",
                    "report": {"ok": True},
                },
                {
                    "name": "rust-audit-patterns-guard",
                    "script_id": "rust_audit_patterns",
                    "severity": "critical",
                    "focus": "known audit regressions",
                    "cmd": ["python3"],
                    "returncode": 0,
                    "ok": True,
                    "skipped": False,
                    "violations": [],
                    "error": None,
                    "stderr_tail": "",
                    "report": {"ok": True},
                },
                {
                    "name": "rust-security-footguns-guard",
                    "script_id": "rust_security_footguns",
                    "severity": "critical",
                    "focus": "security footguns",
                    "cmd": ["python3"],
                    "returncode": 0,
                    "ok": True,
                    "skipped": False,
                    "violations": [],
                    "error": None,
                    "stderr_tail": "",
                    "report": {"ok": True},
                },
            ]

            args = make_args(
                force=True,
                output_path="dev/active/RUST_AUDIT_FINDINGS.md",
                template_path="dev/config/templates/rust_audit_findings_template.md",
                trigger="check-ai-guard",
                trigger_steps="code-shape-guard",
                since_ref="origin/develop",
                head_ref="HEAD",
            )
            with patch("dev.scripts.devctl.commands.audit_scaffold.REPO_ROOT", root), patch(
                "dev.scripts.devctl.commands.audit_scaffold.ACTIVE_ROOT",
                active_dir,
            ):
                rc = audit_scaffold.run(args)

            generated_path = active_dir / "RUST_AUDIT_FINDINGS.md"
            generated_text = generated_path.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        self.assertIn("code-shape-guard", generated_text)
        self.assertIn("src/src/bin/voiceterm/event_loop.rs", generated_text)
        self.assertIn("origin/develop..HEAD", generated_text)
        self.assertIn("check-ai-guard", generated_text)
        self.assertIn("code-shape-guard", generated_text)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["findings_detected"])
