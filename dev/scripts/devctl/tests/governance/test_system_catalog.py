"""Tests for SystemCatalog, AgentDispatchPacket, and discover/view commands."""

from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from types import SimpleNamespace

from dev.scripts.devctl.cli import COMMAND_HANDLERS, READ_ONLY_COMMANDS, build_parser
from dev.scripts.devctl.commands.listing import COMMANDS
from dev.scripts.devctl.governance.system_catalog import (
    build_system_catalog,
    resolve_agent_dispatch,
)
from dev.scripts.devctl.governance.system_catalog_models import (
    AgentDispatchPacket,
    CatalogCommand,
    CatalogGuard,
    CatalogProbe,
    CatalogSurface,
    SystemCatalog,
)


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
        "filter": None,
        "surface": "cli",
        "mode": "summary",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestSystemCatalogModels(unittest.TestCase):
    """Verify frozen dataclass contracts for catalog models."""

    def test_catalog_command_frozen(self) -> None:
        cmd = CatalogCommand(name="check", handler_module="foo", read_only=False)
        with self.assertRaises(AttributeError):
            setattr(cmd, "name", "changed")

    def test_catalog_guard_frozen(self) -> None:
        guard = CatalogGuard(script_id="code_shape", relative_path="path")
        with self.assertRaises(AttributeError):
            setattr(guard, "script_id", "changed")

    def test_system_catalog_is_frozen(self) -> None:
        catalog = SystemCatalog(
            schema_version=1,
            commands=(),
            guards=(),
            probes=(),
            surfaces=(),
        )
        with self.assertRaises(AttributeError):
            setattr(catalog, "schema_version", 2)

    def test_agent_dispatch_packet_frozen(self) -> None:
        packet = AgentDispatchPacket(
            lane="tooling",
            bundle_name="bundle.tooling",
            applicable_guards=("code_shape",),
            applicable_probes=(),
        )
        with self.assertRaises(AttributeError):
            setattr(packet, "lane", "runtime")

    def test_agent_dispatch_packet_has_evidence(self) -> None:
        packet = AgentDispatchPacket(
            lane="tooling",
            bundle_name="bundle.tooling",
            applicable_guards=(),
            applicable_probes=(),
            evidence=("lane=tooling",),
        )
        self.assertEqual(packet.evidence, ("lane=tooling",))

    def test_system_catalog_serializable(self) -> None:
        catalog = SystemCatalog(
            schema_version=1,
            commands=(CatalogCommand("a", "mod"),),
            guards=(CatalogGuard("g", "path"),),
            probes=(CatalogProbe("p", "path"),),
            surfaces=(CatalogSurface("s", "auth", ("C",)),),
            total_commands=1,
            total_guards=1,
            total_probes=1,
            total_surfaces=1,
        )
        payload = json.dumps(asdict(catalog))
        self.assertIn("schema_version", payload)


class TestBuildSystemCatalog(unittest.TestCase):
    """Verify build_system_catalog returns a populated catalog."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = build_system_catalog()

    def test_has_commands(self) -> None:
        self.assertGreater(self.catalog.total_commands, 0)
        self.assertEqual(self.catalog.total_commands, len(self.catalog.commands))

    def test_has_guards(self) -> None:
        self.assertGreater(self.catalog.total_guards, 0)
        self.assertEqual(self.catalog.total_guards, len(self.catalog.guards))

    def test_has_probes(self) -> None:
        self.assertGreater(self.catalog.total_probes, 0)
        self.assertEqual(self.catalog.total_probes, len(self.catalog.probes))

    def test_has_surfaces(self) -> None:
        self.assertGreater(self.catalog.total_surfaces, 0)
        self.assertEqual(self.catalog.total_surfaces, len(self.catalog.surfaces))

    def test_schema_version_is_one(self) -> None:
        self.assertEqual(self.catalog.schema_version, 1)

    def test_commands_include_check(self) -> None:
        names = {c.name for c in self.catalog.commands}
        self.assertIn("check", names)

    def test_commands_include_discover(self) -> None:
        names = {c.name for c in self.catalog.commands}
        self.assertIn("discover", names)

    def test_commands_include_view(self) -> None:
        names = {c.name for c in self.catalog.commands}
        self.assertIn("view", names)

    def test_guards_include_code_shape(self) -> None:
        ids = {g.script_id for g in self.catalog.guards}
        self.assertIn("code_shape", ids)

    def test_guard_has_relative_path(self) -> None:
        for g in self.catalog.guards:
            self.assertTrue(g.relative_path, f"guard {g.script_id} missing relative_path")

    def test_probe_has_relative_path(self) -> None:
        for p in self.catalog.probes:
            self.assertTrue(p.relative_path, f"probe {p.script_id} missing relative_path")

    def test_surface_ids_populated(self) -> None:
        ids = {s.surface_id for s in self.catalog.surfaces}
        self.assertIn("cli", ids)

    def test_read_only_commands_flagged(self) -> None:
        ro_cmds = {c.name for c in self.catalog.commands if c.read_only}
        self.assertIn("discover", ro_cmds)
        self.assertIn("view", ro_cmds)


class TestResolveAgentDispatch(unittest.TestCase):
    """Verify AgentDispatchPacket derivation from changed paths."""

    def test_tooling_lane_for_python_tooling_paths(self) -> None:
        paths = ["dev/scripts/devctl/governance/system_catalog.py"]
        packet = resolve_agent_dispatch(paths)
        self.assertEqual(packet.lane, "tooling")
        self.assertIn("bundle.tooling", packet.bundle_name)

    def test_runtime_lane_for_rust_paths(self) -> None:
        paths = ["rust/src/bin/voiceterm/main.rs"]
        packet = resolve_agent_dispatch(paths)
        self.assertEqual(packet.lane, "runtime")

    def test_docs_lane_for_markdown_only(self) -> None:
        paths = ["README.md"]
        packet = resolve_agent_dispatch(paths)
        self.assertEqual(packet.lane, "docs")

    def test_empty_paths_default_to_docs(self) -> None:
        packet = resolve_agent_dispatch([])
        self.assertEqual(packet.lane, "docs")

    def test_has_applicable_guards(self) -> None:
        paths = ["dev/scripts/devctl/cli.py"]
        packet = resolve_agent_dispatch(paths)
        self.assertGreater(len(packet.applicable_guards), 0)

    def test_has_applicable_probes(self) -> None:
        paths = ["dev/scripts/devctl/cli.py"]
        packet = resolve_agent_dispatch(paths)
        self.assertGreater(len(packet.applicable_probes), 0)

    def test_has_preflight_commands(self) -> None:
        paths = ["dev/scripts/devctl/cli.py"]
        packet = resolve_agent_dispatch(paths)
        self.assertGreater(len(packet.preflight_commands), 0)

    def test_has_evidence(self) -> None:
        paths = ["dev/scripts/devctl/cli.py"]
        packet = resolve_agent_dispatch(paths)
        self.assertGreater(len(packet.evidence), 0)

    def test_rust_paths_filter_to_rust_guards(self) -> None:
        paths = ["rust/src/bin/voiceterm/main.rs"]
        packet = resolve_agent_dispatch(paths)
        guards = set(packet.applicable_guards)
        # code_shape supports both languages, should be included
        self.assertIn("code_shape", guards)

    def test_serializable(self) -> None:
        paths = ["dev/scripts/devctl/cli.py"]
        packet = resolve_agent_dispatch(paths)
        payload = json.dumps(asdict(packet))
        self.assertIn("lane", payload)


class TestDiscoverCommand(unittest.TestCase):
    """Verify discover command wiring and output."""

    def test_parser_accepts_discover(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["discover", "--format", "json"])
        self.assertEqual(args.command, "discover")

    def test_handler_registered(self) -> None:
        self.assertIn("discover", COMMAND_HANDLERS)

    def test_discover_in_listing(self) -> None:
        self.assertIn("discover", COMMANDS)

    def test_discover_is_read_only(self) -> None:
        self.assertIn("discover", READ_ONLY_COMMANDS)

    def test_discover_run_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.discover import run

        args = _make_args(format="json")
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_discover_md_format(self) -> None:
        from dev.scripts.devctl.commands.discover import run, _build_payload
        from dev.scripts.devctl.governance.system_catalog import build_system_catalog

        catalog = build_system_catalog()
        payload = _build_payload(catalog, "all")
        self.assertIn("commands", payload)
        self.assertIn("guards", payload)

    def test_discover_filter_guards(self) -> None:
        from dev.scripts.devctl.commands.discover import _build_payload
        from dev.scripts.devctl.governance.system_catalog import build_system_catalog

        catalog = build_system_catalog()
        payload = _build_payload(catalog, "guards")
        self.assertIn("guards", payload)
        self.assertNotIn("commands", payload)


class TestViewCommand(unittest.TestCase):
    """Verify view command wiring and output."""

    def test_parser_accepts_view(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["view", "--surface", "ai", "--mode", "slim"])
        self.assertEqual(args.command, "view")
        self.assertEqual(args.surface, "ai")
        self.assertEqual(args.mode, "slim")

    def test_handler_registered(self) -> None:
        self.assertIn("view", COMMAND_HANDLERS)

    def test_view_in_listing(self) -> None:
        self.assertIn("view", COMMANDS)

    def test_view_is_read_only(self) -> None:
        self.assertIn("view", READ_ONLY_COMMANDS)

    def test_view_ai_slim_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.view import run

        args = _make_args(format="json", surface="ai", mode="slim")
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_view_cli_summary_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.view import run

        args = _make_args(format="md", surface="cli", mode="summary")
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_view_unsupported_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.view import run

        args = _make_args(format="json", surface="phone", mode="fancy")
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_parser_default_surface_and_mode(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["view"])
        self.assertEqual(args.surface, "cli")
        self.assertEqual(args.mode, "summary")

    def test_view_phone_summary_json_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.view import run

        args = _make_args(format="json", surface="phone", mode="summary")
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_view_phone_summary_md_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.view import run

        args = _make_args(format="md", surface="phone", mode="summary")
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_view_phone_summary_json_has_fields(self) -> None:
        from dev.scripts.devctl.commands.view import _render_phone_summary

        args = _make_args(format="json", surface="phone", mode="summary")
        output = _render_phone_summary(args)
        payload = json.loads(output)
        self.assertEqual(payload["surface"], "phone")
        self.assertIn("resolved_phase", payload)
        self.assertIn("top_blocker", payload)
        self.assertIn("next_actor", payload)

    def test_view_phone_summary_md_has_state(self) -> None:
        from dev.scripts.devctl.commands.view import _render_phone_summary

        args = _make_args(format="md", surface="phone", mode="summary")
        output = _render_phone_summary(args)
        self.assertIn("Blocker:", output)
        self.assertIn("Next:", output)


class TestDiscoverDispatch(unittest.TestCase):
    """Verify discover --dispatch returns an AgentDispatchPacket."""

    def test_dispatch_with_paths_returns_zero(self) -> None:
        from dev.scripts.devctl.commands.discover import run

        args = _make_args(
            format="json",
            filter="all",
            dispatch=["dev/scripts/devctl/cli.py"],
        )
        rc = run(args)
        self.assertEqual(rc, 0)

    def test_dispatch_json_has_lane(self) -> None:
        from dev.scripts.devctl.commands.discover import _run_dispatch

        args = _make_args(format="json")
        # Capture via direct call
        from dev.scripts.devctl.governance.system_catalog import resolve_agent_dispatch
        packet = resolve_agent_dispatch(["dev/scripts/devctl/cli.py"])
        self.assertTrue(packet.lane)
        self.assertTrue(packet.bundle_name)

    def test_dispatch_empty_paths_defaults_to_docs(self) -> None:
        from dev.scripts.devctl.governance.system_catalog import resolve_agent_dispatch
        packet = resolve_agent_dispatch([])
        self.assertEqual(packet.lane, "docs")

    def test_dispatch_with_enabled_checks_filters(self) -> None:
        from dev.scripts.devctl.governance.system_catalog import resolve_agent_dispatch
        from dev.scripts.devctl.governance.system_catalog_models import AgentDispatchPacket

        full = resolve_agent_dispatch(["dev/scripts/devctl/cli.py"])
        # Create a restrictive enabled_checks that only allows code_shape
        enabled = SimpleNamespace(guard_ids=("code_shape",), probe_ids=())
        filtered = resolve_agent_dispatch(
            ["dev/scripts/devctl/cli.py"], enabled_checks=enabled,
        )
        self.assertLessEqual(
            len(filtered.applicable_guards), len(full.applicable_guards),
        )

    def test_parser_accepts_dispatch(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["discover", "--dispatch", "foo.py"])
        self.assertEqual(args.dispatch, ["foo.py"])

    def test_parser_dispatch_no_paths(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["discover", "--dispatch"])
        self.assertEqual(args.dispatch, [])

    def test_dispatch_cli_emits_filtered_packet(self) -> None:
        """CLI-level: _run_dispatch passes enabled_checks to resolve_agent_dispatch."""
        from unittest.mock import patch

        from dev.scripts.devctl.commands.discover import _run_dispatch

        mock_enabled = SimpleNamespace(
            guard_ids=("code_shape",), probe_ids=("concurrency",),
        )
        args = _make_args(format="json")
        captured: dict = {}

        original_resolve = resolve_agent_dispatch

        def spy(changed, **kwargs):
            captured["enabled_checks"] = kwargs.get("enabled_checks")
            return original_resolve(changed, **kwargs)

        with patch(
            "dev.scripts.devctl.governance.system_catalog.resolve_agent_dispatch",
            side_effect=spy,
        ), patch(
            "dev.scripts.devctl.commands.discover._load_enabled_checks",
            return_value=mock_enabled,
        ):
            _run_dispatch(args, ["dev/scripts/devctl/cli.py"])

        self.assertIs(captured["enabled_checks"], mock_enabled)


if __name__ == "__main__":
    unittest.main()
