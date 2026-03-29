"""Tests for check_mobile_relay_protocol guard script."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import init_temp_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "check_mobile_relay_protocol",
    "dev/scripts/checks/check_mobile_relay_protocol.py",
)

# ---------------------------------------------------------------------------
# Minimal fixtures that mirror the real protocol shape without bloat
# ---------------------------------------------------------------------------

RUST_SIMPLE = """\
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
pub(crate) struct AgentInfo {
    pub session_id: String,
    pub provider: String,
    pub label: String,
    pub is_alive: bool,
}
"""

SWIFT_SIMPLE_MATCHING = """\
import Foundation

public struct AgentInfo: Codable, Equatable, Sendable {
    public let sessionID: String?
    public let provider: String?
    public let label: String?
    public let isAlive: Bool?

    enum CodingKeys: String, CodingKey {
        case sessionID = "session_id"
        case provider
        case label
        case isAlive = "is_alive"
    }
}
"""

SWIFT_SIMPLE_MISSING_FIELD = """\
import Foundation

public struct AgentInfo: Codable, Equatable, Sendable {
    public let sessionID: String?
    public let provider: String?

    enum CodingKeys: String, CodingKey {
        case sessionID = "session_id"
        case provider
    }
}
"""

SWIFT_SIMPLE_EXTRA_FIELD = """\
import Foundation

public struct AgentInfo: Codable, Equatable, Sendable {
    public let sessionID: String?
    public let provider: String?
    public let label: String?
    public let isAlive: Bool?
    public let extraField: String?

    enum CodingKeys: String, CodingKey {
        case sessionID = "session_id"
        case provider
        case label
        case isAlive = "is_alive"
        case extraField = "extra_field"
    }
}
"""

RUST_WITH_SERDE_RENAME = """\
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
pub struct SourceRun {
    #[serde(rename = "run_id")]
    pub run_id: i32,
    pub run_sha: String,
}
"""

SWIFT_WITH_CODING_KEYS = """\
import Foundation

public struct SourceRun: Codable, Equatable, Sendable {
    public let runID: Int?
    public let runSHA: String?

    enum CodingKeys: String, CodingKey {
        case runID = "run_id"
        case runSHA = "run_sha"
    }
}
"""

SWIFT_DIFFERENT_STRUCT = """\
import Foundation

public struct RelayEnvelope: Codable, Equatable, Sendable {
    public let sessionID: String?

    enum CodingKeys: String, CodingKey {
        case sessionID = "session_id"
    }
}
"""

RUST_NON_SERDE = """\
#[derive(Debug, Clone)]
pub(crate) struct DaemonConfig {
    pub socket_path: PathBuf,
    pub ws_port: u16,
}
"""

RUST_ENUM_TAGGED = """\
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "event")]
pub(crate) enum DaemonEvent {
    #[serde(rename = "agent_spawned")]
    AgentSpawned {
        session_id: String,
        provider: String,
        label: String,
    },

    #[serde(rename = "agent_output")]
    AgentOutput {
        session_id: String,
        text: String,
    },

    #[serde(rename = "daemon_shutdown")]
    DaemonShutdown,
}
"""


class RustParsingTests(unittest.TestCase):
    """Verify regex-based Rust struct extraction."""

    def test_parses_simple_struct(self) -> None:
        structs = SCRIPT.parse_rust_structs(RUST_SIMPLE)
        self.assertIn("AgentInfo", structs)
        fields = structs["AgentInfo"]["fields"]
        self.assertEqual(
            fields,
            {
                "session_id": "session_id",
                "provider": "provider",
                "label": "label",
                "is_alive": "is_alive",
            },
        )

    def test_parses_struct_with_serde_rename(self) -> None:
        structs = SCRIPT.parse_rust_structs(RUST_WITH_SERDE_RENAME)
        self.assertIn("SourceRun", structs)
        fields = structs["SourceRun"]["fields"]
        # The first field has an explicit #[serde(rename = "run_id")]
        self.assertIn("run_id", fields)
        self.assertIn("run_sha", fields)

    def test_ignores_non_serde_struct(self) -> None:
        structs = SCRIPT.parse_rust_structs(RUST_NON_SERDE)
        self.assertNotIn("DaemonConfig", structs)

    def test_parses_enum_variants(self) -> None:
        variants = SCRIPT.parse_rust_enum_variants(RUST_ENUM_TAGGED)
        self.assertIn("agent_spawned", variants)
        self.assertIn("agent_output", variants)
        self.assertIn("daemon_shutdown", variants)
        spawned = variants["agent_spawned"]
        self.assertEqual(spawned["variant"], "AgentSpawned")
        self.assertEqual(
            spawned["fields"],
            {
                "session_id": "session_id",
                "provider": "provider",
                "label": "label",
            },
        )

    def test_enum_variant_without_fields(self) -> None:
        variants = SCRIPT.parse_rust_enum_variants(RUST_ENUM_TAGGED)
        shutdown = variants["daemon_shutdown"]
        self.assertEqual(shutdown["fields"], {})


class SwiftParsingTests(unittest.TestCase):
    """Verify regex-based Swift struct extraction."""

    def test_parses_struct_with_coding_keys(self) -> None:
        structs = SCRIPT.parse_swift_structs(SWIFT_SIMPLE_MATCHING)
        self.assertIn("AgentInfo", structs)
        fields = structs["AgentInfo"]["fields"]
        self.assertEqual(
            fields,
            {
                "session_id": "sessionID",
                "provider": "provider",
                "label": "label",
                "is_alive": "isAlive",
            },
        )

    def test_parses_struct_with_wire_names(self) -> None:
        structs = SCRIPT.parse_swift_structs(SWIFT_WITH_CODING_KEYS)
        self.assertIn("SourceRun", structs)
        fields = structs["SourceRun"]["fields"]
        self.assertIn("run_id", fields)
        self.assertIn("run_sha", fields)

    def test_ignores_non_codable_struct(self) -> None:
        text = """\
public struct PlainThing: Equatable {
    public let value: String
}
"""
        structs = SCRIPT.parse_swift_structs(text)
        self.assertEqual(structs, {})


class ComparisonTests(unittest.TestCase):
    """Verify field matching between parsed Rust and Swift data."""

    def test_matching_fields_no_violations(self) -> None:
        rust = SCRIPT.parse_rust_structs(RUST_SIMPLE)
        swift = SCRIPT.parse_swift_structs(SWIFT_SIMPLE_MATCHING)
        pairs = SCRIPT.match_struct_pairs(rust, swift)
        self.assertEqual(pairs, [("AgentInfo", "AgentInfo")])

        rust_only, swift_only = SCRIPT.compare_fields(
            rust["AgentInfo"]["fields"],
            swift["AgentInfo"]["fields"],
        )
        self.assertEqual(rust_only, [])
        self.assertEqual(swift_only, [])

    def test_detects_swift_missing_fields(self) -> None:
        rust = SCRIPT.parse_rust_structs(RUST_SIMPLE)
        swift = SCRIPT.parse_swift_structs(SWIFT_SIMPLE_MISSING_FIELD)
        rust_only, swift_only = SCRIPT.compare_fields(
            rust["AgentInfo"]["fields"],
            swift["AgentInfo"]["fields"],
        )
        self.assertIn("label", rust_only)
        self.assertIn("is_alive", rust_only)
        self.assertEqual(swift_only, [])

    def test_detects_swift_extra_fields(self) -> None:
        rust = SCRIPT.parse_rust_structs(RUST_SIMPLE)
        swift = SCRIPT.parse_swift_structs(SWIFT_SIMPLE_EXTRA_FIELD)
        rust_only, swift_only = SCRIPT.compare_fields(
            rust["AgentInfo"]["fields"],
            swift["AgentInfo"]["fields"],
        )
        self.assertEqual(rust_only, [])
        self.assertIn("extra_field", swift_only)


class ReportTests(unittest.TestCase):
    """Verify end-to-end report building."""

    def _report(self, **kwargs):
        return SCRIPT.build_report(SCRIPT.ProtocolReportRequest(**kwargs))

    def test_report_ok_when_fields_match(self) -> None:
        report = self._report(rust_text=RUST_SIMPLE, swift_text=SWIFT_SIMPLE_MATCHING, mode="test")
        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertGreaterEqual(report["matched_pairs"], 1)

    def test_report_fails_when_field_missing(self) -> None:
        report = self._report(rust_text=RUST_SIMPLE, swift_text=SWIFT_SIMPLE_MISSING_FIELD, mode="test")
        self.assertFalse(report["ok"])
        self.assertGreater(len(report["violations"]), 0)
        wire_names = {v["wire_name"] for v in report["violations"]}
        self.assertIn("label", wire_names)
        self.assertIn("is_alive", wire_names)

    def test_report_skips_when_no_protocol_files_changed(self) -> None:
        report = self._report(
            rust_text=RUST_SIMPLE,
            swift_text=SWIFT_SIMPLE_MISSING_FIELD,
            mode="commit-range",
            changed_paths=[Path("rust/src/main.rs")],
        )
        self.assertTrue(report["ok"])
        self.assertTrue(report.get("skipped"))

    def test_report_runs_when_rust_types_changed(self) -> None:
        report = self._report(
            rust_text=RUST_SIMPLE,
            swift_text=SWIFT_SIMPLE_MISSING_FIELD,
            mode="commit-range",
            changed_paths=[Path("rust/src/bin/voiceterm/daemon/types.rs")],
        )
        self.assertFalse(report["ok"])
        self.assertGreater(len(report["violations"]), 0)

    def test_report_runs_when_swift_models_changed(self) -> None:
        report = self._report(
            rust_text=RUST_SIMPLE,
            swift_text=SWIFT_SIMPLE_MISSING_FIELD,
            mode="commit-range",
            changed_paths=[
                Path(
                    "app/ios/VoiceTermMobile/Sources/"
                    "VoiceTermMobileCore/MobileRelayModels.swift"
                )
            ],
        )
        self.assertFalse(report["ok"])

    def test_report_handles_missing_files_gracefully(self) -> None:
        report = self._report(rust_text=None, swift_text=None, mode="test")
        self.assertTrue(report["ok"])
        self.assertTrue(report.get("skipped"))

    def test_report_fails_when_no_struct_pairs_match(self) -> None:
        report = self._report(rust_text=RUST_SIMPLE, swift_text=SWIFT_DIFFERENT_STRUCT, mode="test")
        self.assertFalse(report["ok"])
        self.assertEqual(report["matched_pairs"], 0)
        self.assertEqual(report["violations"][0]["side"], "no_shared_structs")

    def test_report_violation_structure(self) -> None:
        report = self._report(rust_text=RUST_SIMPLE, swift_text=SWIFT_SIMPLE_EXTRA_FIELD, mode="test")
        swift_only_violations = [
            v for v in report["violations"] if v["side"] == "swift_only"
        ]
        self.assertTrue(len(swift_only_violations) > 0)
        v = swift_only_violations[0]
        self.assertIn("rust_struct", v)
        self.assertIn("swift_struct", v)
        self.assertIn("wire_name", v)
        self.assertIn("reason", v)


class RendererTests(unittest.TestCase):
    """Verify markdown rendering."""

    def test_render_ok_report(self) -> None:
        report = SCRIPT.build_report(SCRIPT.ProtocolReportRequest(rust_text=RUST_SIMPLE, swift_text=SWIFT_SIMPLE_MATCHING, mode="test"))
        md = SCRIPT._render_md(report)
        self.assertIn("check_mobile_relay_protocol", md)
        self.assertIn("ok: True", md)

    def test_render_violation_report(self) -> None:
        report = SCRIPT.build_report(SCRIPT.ProtocolReportRequest(rust_text=RUST_SIMPLE, swift_text=SWIFT_SIMPLE_MISSING_FIELD, mode="test"))
        md = SCRIPT._render_md(report)
        self.assertIn("Violations", md)
        self.assertIn("rust_only", md)

    def test_render_skipped_report(self) -> None:
        report = SCRIPT.build_report(SCRIPT.ProtocolReportRequest(rust_text=RUST_SIMPLE, swift_text=SWIFT_SIMPLE_MATCHING, mode="commit-range", changed_paths=[Path("some/other/file.rs")]))
        md = SCRIPT._render_md(report)
        self.assertIn("skipped", md)


if __name__ == "__main__":
    unittest.main()
