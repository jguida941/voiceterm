"""Tests for platform.system_catalog -- SystemCatalog builder and AgentDispatchPacket routing."""

from __future__ import annotations

from pathlib import Path

import pytest

from dev.scripts.devctl.platform.system_catalog import (
    _classify_lane_simple,
    _collect_guards_from_filesystem,
    _collect_probes_from_filesystem,
    _detect_languages,
    _filter_by_languages,
    build_system_catalog,
    resolve_agent_dispatch,
)
from dev.scripts.devctl.platform.system_catalog_models import (
    AgentDispatchPacket,
    CommandEntry,
    ContractEntry,
    GuardEntry,
    ProbeEntry,
    SurfaceEntry,
    SystemCatalog,
)


# ---------------------------------------------------------------------------
# 1. Model dataclasses are frozen and have expected fields
# ---------------------------------------------------------------------------


class TestModelsAreFrozen:
    """Verify that all entry dataclasses are frozen (immutable)."""

    def test_command_entry_is_frozen(self) -> None:
        entry = CommandEntry(name="check", path="devctl check", category="devctl")
        with pytest.raises(AttributeError):
            entry.name = "other"  # type: ignore[misc]

    def test_guard_entry_is_frozen(self) -> None:
        entry = GuardEntry(
            name="code_shape",
            path="dev/scripts/checks/check_code_shape.py",
            category="hard_guard",
        )
        with pytest.raises(AttributeError):
            entry.name = "other"  # type: ignore[misc]

    def test_probe_entry_is_frozen(self) -> None:
        entry = ProbeEntry(
            name="probe_concurrency",
            path="dev/scripts/checks/probe_concurrency.py",
            category="review_probe",
        )
        with pytest.raises(AttributeError):
            entry.name = "other"  # type: ignore[misc]

    def test_system_catalog_is_frozen(self) -> None:
        catalog = SystemCatalog()
        with pytest.raises(AttributeError):
            catalog.schema_version = 2  # type: ignore[misc]

    def test_agent_dispatch_packet_is_frozen(self) -> None:
        packet = AgentDispatchPacket()
        with pytest.raises(AttributeError):
            packet.lane = "runtime"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. build_system_catalog produces a valid catalog
# ---------------------------------------------------------------------------


class TestBuildSystemCatalog:
    """Verify the catalog builder works with the current worktree."""

    def test_catalog_has_commands_from_listing(self) -> None:
        catalog = build_system_catalog()
        assert len(catalog.commands) > 0, "Expected at least one command from listing.py"
        names = {c.name for c in catalog.commands}
        assert "check" in names, "Expected 'check' in command list"
        assert "list" in names, "Expected 'list' in command list"

    def test_catalog_has_guards(self) -> None:
        catalog = build_system_catalog()
        assert len(catalog.guards) > 0, "Expected at least one guard"

    def test_catalog_has_schema_version(self) -> None:
        catalog = build_system_catalog()
        assert catalog.schema_version == 1

    def test_catalog_has_generated_timestamp(self) -> None:
        catalog = build_system_catalog()
        assert catalog.generated_at_utc != ""
        assert "T" in catalog.generated_at_utc, "Expected ISO format timestamp"

    def test_catalog_to_dict_keys(self) -> None:
        catalog = build_system_catalog()
        d = catalog.to_dict()
        expected_keys = {
            "schema_version",
            "generated_at_utc",
            "commands",
            "guards",
            "probes",
            "surfaces",
            "contracts",
            "total_commands",
            "total_guards",
            "total_probes",
            "total_surfaces",
            "total_contracts",
        }
        assert expected_keys == set(d.keys())

    def test_catalog_to_dict_counts_match(self) -> None:
        catalog = build_system_catalog()
        d = catalog.to_dict()
        assert d["total_commands"] == len(catalog.commands)
        assert d["total_guards"] == len(catalog.guards)
        assert d["total_probes"] == len(catalog.probes)


# ---------------------------------------------------------------------------
# 3. Filesystem fallback collectors work
# ---------------------------------------------------------------------------


class TestFilesystemFallback:
    """Verify guard/probe collection from filesystem when registries are unavailable."""

    def test_guards_from_filesystem_with_scripts(self, tmp_path: Path) -> None:
        checks_dir = tmp_path / "dev" / "scripts" / "checks"
        checks_dir.mkdir(parents=True)
        (checks_dir / "check_code_shape.py").write_text("# guard\n")
        (checks_dir / "check_naming.py").write_text("# guard\n")
        (checks_dir / "not_a_guard.py").write_text("# ignored\n")

        guards = _collect_guards_from_filesystem(tmp_path)
        assert len(guards) == 2
        names = {g.name for g in guards}
        assert "code_shape" in names
        assert "naming" in names
        assert all(g.category == "hard_guard" for g in guards)

    def test_probes_from_filesystem_with_scripts(self, tmp_path: Path) -> None:
        checks_dir = tmp_path / "dev" / "scripts" / "checks"
        checks_dir.mkdir(parents=True)
        (checks_dir / "probe_concurrency.py").write_text("# probe\n")
        (checks_dir / "probe_magic.py").write_text("# probe\n")
        (checks_dir / "check_not_probe.py").write_text("# not a probe\n")

        probes = _collect_probes_from_filesystem(tmp_path)
        assert len(probes) == 2
        names = {p.name for p in probes}
        assert "probe_concurrency" in names
        assert "probe_magic" in names
        assert all(p.category == "review_probe" for p in probes)

    def test_guards_from_nonexistent_dir(self, tmp_path: Path) -> None:
        guards = _collect_guards_from_filesystem(tmp_path)
        assert guards == ()

    def test_probes_from_nonexistent_dir(self, tmp_path: Path) -> None:
        probes = _collect_probes_from_filesystem(tmp_path)
        assert probes == ()


# ---------------------------------------------------------------------------
# 4. Language detection and lane classification
# ---------------------------------------------------------------------------


class TestLanguageDetection:
    """Verify path-to-language mapping."""

    def test_python_detected(self) -> None:
        assert _detect_languages(["foo/bar.py"]) == {"python"}

    def test_rust_detected(self) -> None:
        assert _detect_languages(["rust/src/main.rs"]) == {"rust"}

    def test_mixed_languages(self) -> None:
        paths = ["dev/scripts/check.py", "rust/src/lib.rs"]
        assert _detect_languages(paths) == {"python", "rust"}

    def test_unknown_extension(self) -> None:
        assert _detect_languages(["README.md"]) == set()

    def test_empty_paths(self) -> None:
        assert _detect_languages([]) == set()


class TestLaneClassification:
    """Verify the simple lane classifier matches task-router semantics."""

    def test_rust_src_is_runtime(self) -> None:
        assert _classify_lane_simple(["rust/src/main.rs"]) == "runtime"

    def test_dev_scripts_is_tooling(self) -> None:
        assert _classify_lane_simple(["dev/scripts/devctl.py"]) == "tooling"

    def test_docs_is_docs(self) -> None:
        assert _classify_lane_simple(["docs/README.md"]) == "docs"

    def test_github_is_tooling(self) -> None:
        assert _classify_lane_simple([".github/workflows/ci.yml"]) == "tooling"

    def test_empty_defaults_to_tooling(self) -> None:
        assert _classify_lane_simple([]) == "tooling"

    def test_runtime_wins_over_tooling(self) -> None:
        paths = ["dev/scripts/check.py", "rust/src/lib.rs"]
        assert _classify_lane_simple(paths) == "runtime"


# ---------------------------------------------------------------------------
# 5. Guard/probe language filtering
# ---------------------------------------------------------------------------


class TestLanguageFiltering:
    """Verify guards/probes are filtered by language scope."""

    def test_universal_guard_always_matches(self) -> None:
        guards = (
            GuardEntry(name="universal", path="", category="hard_guard", languages=()),
        )
        result = _filter_by_languages(guards, {"python"})
        assert result == ("universal",)

    def test_language_scoped_guard_matches(self) -> None:
        guards = (
            GuardEntry(
                name="py_only", path="", category="hard_guard", languages=("python",)
            ),
            GuardEntry(
                name="rs_only", path="", category="hard_guard", languages=("rust",)
            ),
        )
        result = _filter_by_languages(guards, {"python"})
        assert result == ("py_only",)

    def test_empty_languages_returns_all_universal(self) -> None:
        guards = (
            GuardEntry(name="universal", path="", category="hard_guard", languages=()),
            GuardEntry(
                name="py_only", path="", category="hard_guard", languages=("python",)
            ),
        )
        result = _filter_by_languages(guards, set())
        assert result == ("universal",)


# ---------------------------------------------------------------------------
# 6. AgentDispatchPacket builder
# ---------------------------------------------------------------------------


class TestResolveAgentDispatch:
    """Verify dispatch packet routing uses lane classification and filtering."""

    def test_dispatch_for_python_files(self) -> None:
        packet = resolve_agent_dispatch(["dev/scripts/devctl/foo.py"])
        assert packet.lane == "tooling"
        assert packet.recommended_bundle == "bundle.tooling"
        assert packet.context_level == "standard"
        assert "dev/scripts/devctl/foo.py" in packet.changed_paths

    def test_dispatch_for_rust_files(self) -> None:
        packet = resolve_agent_dispatch(["rust/src/main.rs"])
        assert packet.lane == "runtime"
        assert packet.recommended_bundle == "bundle.runtime"
        assert packet.context_level == "full"

    def test_dispatch_has_preflight_command(self) -> None:
        packet = resolve_agent_dispatch(["README.md"])
        assert "check --profile ci" in packet.preflight_command

    def test_dispatch_has_evidence(self) -> None:
        packet = resolve_agent_dispatch(["dev/scripts/check.py"])
        assert len(packet.evidence) > 0
        evidence_str = " ".join(packet.evidence)
        assert "lane=" in evidence_str
        assert "bundle=" in evidence_str

    def test_dispatch_empty_paths(self) -> None:
        packet = resolve_agent_dispatch([])
        assert packet.lane in ("tooling", "docs")  # classify_lane default varies
        assert packet.changed_paths == ()
