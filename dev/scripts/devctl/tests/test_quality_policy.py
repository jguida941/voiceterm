"""Tests for repo quality-policy resolution."""

from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl import cli
from dev.scripts.devctl import common_io
from dev.scripts.devctl import quality_policy
from dev.scripts.devctl.commands import quality_policy as quality_policy_command


class QualityPolicyTests(unittest.TestCase):
    def test_resolve_quality_policy_uses_repo_config_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            policy_path = root / "repo_policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "repo_name": "portable-demo",
                        "quality_scopes": {
                            "python_guard_roots": ["python"],
                            "python_probe_roots": ["python"],
                            "rust_guard_roots": ["crate/src"],
                            "rust_probe_roots": ["crate/src"],
                        },
                        "enabled_ai_guard_ids": [
                            "code_shape",
                            "rust_lint_debt",
                        ],
                        "enabled_review_probe_ids": [
                            "probe_concurrency",
                        ],
                        "ai_guard_overrides": {
                            "rust_lint_debt": {
                                "step_name": "lint-debt-custom",
                                "extra_args": ["--report-dead-code"],
                            }
                        },
                        "guard_configs": {
                            "code_shape": {
                                "namespace_family_rules": [
                                    {
                                        "root": "python",
                                        "flat_prefix": "family_",
                                        "namespace_subdir": "family",
                                        "min_family_size": 4,
                                    }
                                ]
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            resolved = quality_policy.resolve_quality_policy(
                repo_root=root,
                policy_path=policy_path,
            )

        self.assertEqual(resolved.schema_version, 2)
        self.assertEqual(resolved.repo_name, "portable-demo")
        self.assertFalse(resolved.capabilities.python)
        self.assertTrue(resolved.capabilities.rust)
        self.assertEqual(resolved.scopes.python_guard_roots, (Path("python"),))
        self.assertEqual(resolved.scopes.python_probe_roots, (Path("python"),))
        self.assertEqual(resolved.scopes.rust_guard_roots, (Path("crate/src"),))
        self.assertEqual(resolved.scopes.rust_probe_roots, (Path("crate/src"),))
        self.assertEqual(
            [spec.script_id for spec in resolved.ai_guard_checks],
            ["code_shape", "rust_lint_debt"],
        )
        self.assertEqual(resolved.ai_guard_checks[1].step_name, "lint-debt-custom")
        self.assertEqual(
            resolved.ai_guard_checks[1].extra_args,
            ("--report-dead-code",),
        )
        self.assertEqual(
            [spec.script_id for spec in resolved.review_probe_checks],
            ["probe_concurrency"],
        )
        self.assertEqual(
            resolved.guard_configs["code_shape"]["namespace_family_rules"][0]["root"],
            "python",
        )
        self.assertEqual(resolved.warnings, ())

    def test_resolve_quality_policy_skips_unsupported_language_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            policy_path = root / "repo_policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "enabled_ai_guard_ids": [
                            "code_shape",
                            "rust_best_practices",
                            "python_broad_except",
                        ],
                        "enabled_review_probe_ids": [
                            "probe_concurrency",
                            "probe_design_smells",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            resolved = quality_policy.resolve_quality_policy(
                repo_root=root,
                policy_path=policy_path,
            )

        self.assertEqual(
            [spec.script_id for spec in resolved.ai_guard_checks],
            ["code_shape", "python_broad_except"],
        )
        self.assertEqual(
            [spec.script_id for spec in resolved.review_probe_checks],
            ["probe_design_smells"],
        )
        self.assertEqual(resolved.scopes.python_guard_roots, ())
        self.assertEqual(resolved.scopes.python_probe_roots, ())
        self.assertEqual(resolved.scopes.rust_guard_roots, ())
        self.assertEqual(resolved.scopes.rust_probe_roots, ())
        self.assertTrue(
            any("rust_best_practices" in warning for warning in resolved.warnings)
        )
        self.assertTrue(any("probe_concurrency" in warning for warning in resolved.warnings))

    def test_resolve_quality_policy_warns_on_missing_policy_and_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "example.py").write_text("print('hi')\n", encoding="utf-8")

            resolved = quality_policy.resolve_quality_policy(
                repo_root=root,
                policy_path=root / "missing.json",
            )

        self.assertTrue(resolved.capabilities.python)
        self.assertGreater(len(resolved.ai_guard_checks), 0)
        self.assertGreater(len(resolved.review_probe_checks), 0)
        self.assertEqual(resolved.scopes.python_guard_roots, (Path("."),))
        self.assertEqual(resolved.scopes.python_probe_roots, (Path("."),))
        self.assertEqual(resolved.scopes.rust_guard_roots, ())
        self.assertEqual(resolved.scopes.rust_probe_roots, ())
        self.assertIn(
            "python_suppression_debt",
            {spec.script_id for spec in resolved.ai_guard_checks},
        )
        self.assertNotIn(
            "ide_provider_isolation",
            {spec.script_id for spec in resolved.ai_guard_checks},
        )
        self.assertTrue(any("quality policy unavailable" in warning for warning in resolved.warnings))

    def test_resolve_quality_policy_discovers_common_python_scope_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "app").mkdir()
            (root / "app" / "main.py").write_text("print('app')\n", encoding="utf-8")
            (root / "dev" / "scripts").mkdir(parents=True)
            (root / "dev" / "scripts" / "tool.py").write_text(
                "print('tool')\n",
                encoding="utf-8",
            )

            resolved = quality_policy.resolve_quality_policy(
                repo_root=root,
                policy_path=root / "missing.json",
            )

        self.assertEqual(
            resolved.scopes.python_guard_roots,
            (Path("app"), Path("dev/scripts")),
        )
        self.assertEqual(
            resolved.scopes.python_probe_roots,
            (Path("app"), Path("dev/scripts")),
        )

    def test_resolve_quality_policy_normalizes_scope_roots_and_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "pyproject.toml").write_text(
                "[project]\nname='demo'\n",
                encoding="utf-8",
            )
            (root / "app").mkdir()
            (root / "app" / "main.py").write_text("print('app')\n", encoding="utf-8")
            policy_path = root / "repo_policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "quality_scopes": {
                            "python_guard_roots": [
                                "app",
                                str(root / "app"),
                                ".",
                                "",
                                "../escape",
                                str(root.parent / "outside"),
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            resolved = quality_policy.resolve_quality_policy(
                repo_root=root,
                policy_path=policy_path,
            )

        self.assertEqual(
            resolved.scopes.python_guard_roots,
            (Path("app"), Path(".")),
        )
        self.assertTrue(
            any("ignored path escaping repo root" in warning for warning in resolved.warnings)
        )
        self.assertTrue(
            any(
                "ignored absolute path outside repo" in warning
                for warning in resolved.warnings
            )
        )

    def test_resolve_quality_policy_merges_extended_presets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            presets_dir = root / "presets"
            presets_dir.mkdir()
            (presets_dir / "portable_python.json").write_text(
                json.dumps(
                    {
                        "enabled_ai_guard_ids": [
                            "code_shape",
                            "python_broad_except",
                        ],
                        "enabled_review_probe_ids": [
                            "probe_design_smells",
                        ],
                        "guard_configs": {
                            "code_shape": {
                                "namespace_family_rules": [
                                    {
                                        "root": "python",
                                        "flat_prefix": "family_",
                                        "namespace_subdir": "family",
                                        "min_family_size": 4,
                                    }
                                ],
                                "docs": {"required": "base"},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (presets_dir / "portable_rust.json").write_text(
                json.dumps(
                    {
                        "enabled_ai_guard_ids": [
                            "code_shape",
                            "rust_best_practices",
                        ],
                        "enabled_review_probe_ids": [
                            "probe_concurrency",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            policy_path = root / "repo_policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "repo_name": "portable-demo",
                        "extends": [
                            "presets/portable_python.json",
                            "presets/portable_rust.json",
                        ],
                        "ai_guard_overrides": {
                            "python_broad_except": {"enabled": False},
                        },
                        "guard_configs": {
                            "code_shape": {
                                "docs": {"required": "override"},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            resolved = quality_policy.resolve_quality_policy(
                repo_root=root,
                policy_path=policy_path,
            )

        self.assertEqual(resolved.repo_name, "portable-demo")
        self.assertEqual(
            [spec.script_id for spec in resolved.ai_guard_checks],
            ["code_shape", "rust_best_practices"],
        )
        self.assertEqual(
            [spec.script_id for spec in resolved.review_probe_checks],
            ["probe_design_smells", "probe_concurrency"],
        )
        self.assertEqual(
            resolved.guard_configs["code_shape"]["namespace_family_rules"][0][
                "namespace_subdir"
            ],
            "family",
        )
        self.assertEqual(
            resolved.guard_configs["code_shape"]["docs"]["required"],
            "override",
        )

    def test_resolve_quality_policy_uses_env_override_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "example.py").write_text("print('hi')\n", encoding="utf-8")
            policy_path = root / "repo_policy.json"
            policy_path.write_text(
                json.dumps({"repo_name": "env-demo"}),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {quality_policy.QUALITY_POLICY_ENV_VAR: str(policy_path)},
            ):
                resolved = quality_policy.resolve_quality_policy(repo_root=root)

        self.assertEqual(resolved.repo_name, "env-demo")

    def test_resolve_quality_policy_uses_repo_root_default_policy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "example.py").write_text("print('hi')\n", encoding="utf-8")
            policy_path = root / "dev" / "config" / "devctl_repo_policy.json"
            policy_path.parent.mkdir(parents=True, exist_ok=True)
            policy_path.write_text(
                json.dumps(
                    {
                        "repo_name": "repo-root-default",
                        "guard_configs": {
                            "python_design_complexity": {
                                "max_branches": 9,
                                "max_returns": 5,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            resolved = quality_policy.resolve_quality_policy(repo_root=root)

        self.assertEqual(resolved.repo_name, "repo-root-default")
        self.assertEqual(
            resolved.guard_configs["python_design_complexity"]["max_branches"],
            9,
        )

    def test_build_env_exports_quality_policy_override(self) -> None:
        args = Namespace(
            offline=False,
            cargo_home=None,
            cargo_target_dir=None,
            quality_policy="~/portable-policy.json",
        )

        env = common_io.build_env(args)

        self.assertEqual(
            env[quality_policy.QUALITY_POLICY_ENV_VAR],
            str(Path("~/portable-policy.json").expanduser()),
        )


class QualityPolicyCommandTests(unittest.TestCase):
    def test_cli_parser_accepts_quality_policy_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "quality-policy",
                "--quality-policy",
                "/tmp/policy.json",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "quality-policy")
        self.assertEqual(args.quality_policy, "/tmp/policy.json")
        self.assertEqual(args.format, "json")

    def test_quality_policy_command_writes_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "example.py").write_text("print('hi')\n", encoding="utf-8")
            policy_path = root / "repo_policy.json"
            policy_path.write_text(
                json.dumps({"repo_name": "command-demo"}),
                encoding="utf-8",
            )
            output_path = root / "policy-report.json"
            args = Namespace(
                quality_policy=str(policy_path),
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            rc = quality_policy_command.run(args)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["command"], "quality-policy")
        self.assertEqual(payload["repo_name"], "command-demo")
        self.assertIn("quality_scopes", payload)
        self.assertIn("python_probe_roots", payload["quality_scopes"])
        self.assertIn("ai_guard_checks", payload)
        self.assertIn("guard_configs", payload)


if __name__ == "__main__":
    unittest.main()
