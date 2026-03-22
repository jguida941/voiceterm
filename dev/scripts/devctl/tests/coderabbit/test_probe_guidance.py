"""Unit tests for the CodeRabbit probe-guidance helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.coderabbit.probe_guidance import attach_probe_guidance, load_probe_guidance


def _structured_items() -> list[dict]:
    return [
        {
            "severity": "high",
            "category": "rust",
            "path": "rust/src/auth.rs",
            "line": 12,
            "summary": "Unused import in auth.rs",
        },
        {
            "severity": "medium",
            "category": "python",
            "path": "dev/scripts/tool.py",
            "line": 4,
            "summary": "Broad except clause",
        },
    ]


def _legacy_summary_items() -> list[dict]:
    return [
        {
            "severity": "high",
            "category": "rust",
            "summary": "rust/src/auth.rs:12 - Unused import in auth.rs",
        }
    ]


class LoadProbeGuidanceTests(unittest.TestCase):
    def test_reads_review_targets_findings_with_ai_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "rust/src/auth.rs",
                                "symbol": "validate_auth",
                                "check_id": "probe_design_smells",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Extract the auth validator helper.",
                            },
                            {
                                "file_path": "docs/README.md",
                                "symbol": "",
                                "check_id": "probe_stringly_typed",
                                "severity": "medium",
                                "ai_instruction": "Ignore me after relevant match fills the slice.",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(_structured_items(), report_root=root)

            self.assertEqual(len(guidance), 1)
            self.assertEqual(guidance[0]["file_path"], "rust/src/auth.rs")
            self.assertIn("Extract the auth validator helper", guidance[0]["ai_instruction"])

    def test_requires_review_targets_for_ralph_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest = root / "latest"
            latest.mkdir(parents=True)
            (latest / "review_packet.json").write_text(
                json.dumps(
                    {
                        "hotspots": [
                            {
                                "file": "rust/src/auth.rs",
                                "representative_hints": [
                                    {
                                        "probe": "probe_design_smells",
                                        "severity": "high",
                                        "ai_instruction": "This path is no longer canonical for Ralph.",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(_structured_items(), report_root=root)

            self.assertEqual(guidance, [])

    def test_structured_path_and_line_match_without_summary_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "rust/src/auth.rs",
                                "check_id": "probe_design_smells",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Extract the auth validator helper.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(_structured_items(), report_root=root)

            self.assertEqual(len(guidance), 1)
            self.assertEqual(guidance[0]["file_path"], "rust/src/auth.rs")

    def test_legacy_summary_parsing_remains_as_compatibility_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "rust/src/auth.rs",
                                "check_id": "probe_design_smells",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Extract the auth validator helper.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(_legacy_summary_items(), report_root=root)

            self.assertEqual(len(guidance), 1)
            self.assertEqual(guidance[0]["file_path"], "rust/src/auth.rs")

    def test_exact_path_matching_skips_unrelated_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "docs/README.md",
                                "check_id": "probe_design_smells",
                                "severity": "high",
                                "ai_instruction": "This should not match.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(_structured_items(), report_root=root)

            self.assertEqual(guidance, [])

    def test_attach_probe_guidance_dedupes_same_instruction_per_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "rust/src/auth.rs",
                                "check_id": "probe_design_smells",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Extract the auth validator helper.",
                            },
                            {
                                "file_path": "rust/src/auth.rs",
                                "check_id": "probe_design_smells",
                                "severity": "medium",
                                "line": 11,
                                "end_line": 12,
                                "ai_instruction": "Extract the auth validator helper.",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            enriched = attach_probe_guidance(_structured_items(), report_root=root)

            self.assertEqual(len(enriched[0]["probe_guidance"]), 1)

    def test_symbol_mismatch_skips_same_file_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "rust/src/auth.rs",
                                "symbol": "validate_auth",
                                "check_id": "probe_design_smells",
                                "severity": "high",
                                "line": 10,
                                "end_line": 14,
                                "ai_instruction": "Extract the auth validator helper.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(
                [
                    {
                        "severity": "high",
                        "category": "rust",
                        "path": "rust/src/auth.rs",
                        "symbol": "call_auth",
                        "line": 12,
                        "summary": "Unused import in auth.rs",
                    }
                ],
                report_root=root,
            )

        self.assertEqual(guidance, [])

    def test_symbol_match_beats_same_file_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "review_targets.json").write_text(
                json.dumps(
                    {
                        "contract_id": "ReviewTargets",
                        "findings": [
                            {
                                "file_path": "rust/src/auth.rs",
                                "symbol": "validate_auth",
                                "check_id": "probe_design_smells",
                                "severity": "medium",
                                "line": 10,
                                "end_line": 40,
                                "ai_instruction": "Wrong symbol guidance.",
                            },
                            {
                                "file_path": "rust/src/auth.rs",
                                "symbol": "call_auth",
                                "check_id": "probe_side_effect_mixing",
                                "severity": "high",
                                "line": 12,
                                "end_line": 12,
                                "ai_instruction": "Extract the caller orchestration.",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guidance = load_probe_guidance(
                [
                    {
                        "severity": "high",
                        "category": "rust",
                        "path": "rust/src/auth.rs",
                        "symbol": "call_auth",
                        "line": 12,
                        "summary": "Unused import in auth.rs",
                    }
                ],
                report_root=root,
            )

        self.assertEqual(len(guidance), 1)
        self.assertEqual(guidance[0]["probe"], "probe_side_effect_mixing")
