"""Tests for the bridge action-request surface."""

from __future__ import annotations

import pytest

from dev.scripts.devctl.review_channel.action_request import (
    ActionKind,
    ActionRequest,
    ActionStatus,
    SECTION_HEADING,
    VALID_ACTION_KINDS,
    action_requests_from_packets,
    default_section_body,
    parse_action_requests,
    pending_action_requests,
    render_action_request_line,
    render_action_requests_from_packets,
    render_action_requests_section,
    validate_action_request,
)
from dev.scripts.devctl.review_channel.bridge_sanitize import (
    BRIDGE_ALLOWED_H2,
    BRIDGE_SECTION_LINE_LIMITS,
    sanitize_bridge_sections,
)
from dev.scripts.devctl.review_channel.handoff_constants import (
    TRACKED_BRIDGE_SECTIONS,
)


class TestParseActionRequests:
    """Parsing the canonical action-request line format."""

    def test_parses_single_pending_commit(self) -> None:
        line = "- [ar-001] commit: -m 'fix typo' (status: pending)"
        result = parse_action_requests(line)
        assert len(result) == 1
        assert result[0].id == "ar-001"
        assert result[0].action == "commit"
        assert result[0].payload == "-m 'fix typo'"
        assert result[0].status == "pending"

    def test_parses_multiple_requests(self) -> None:
        text = "\n".join([
            "- [ar-001] commit: -m 'fix typo' (status: pending)",
            "- [ar-002] push: origin feature/foo (status: completed)",
            "- [ar-003] run_check: --profile ci (status: failed)",
        ])
        result = parse_action_requests(text)
        assert len(result) == 3
        assert result[0].status == "pending"
        assert result[1].status == "completed"
        assert result[2].status == "failed"

    def test_skips_malformed_lines(self) -> None:
        text = "\n".join([
            "- [ar-001] commit: -m 'fix typo' (status: pending)",
            "- This is not an action request.",
            "Some random text",
            "",
            "- [ar-002] push: origin main (status: completed)",
        ])
        result = parse_action_requests(text)
        assert len(result) == 2

    def test_empty_text_returns_empty(self) -> None:
        assert parse_action_requests("") == []

    def test_parses_kill_process_action(self) -> None:
        line = "- [ar-004] kill_process: pid 12345 (status: pending)"
        result = parse_action_requests(line)
        assert len(result) == 1
        assert result[0].action == "kill_process"
        assert result[0].payload == "pid 12345"

    def test_rejects_unknown_status(self) -> None:
        line = "- [ar-001] commit: -m 'fix' (status: unknown)"
        result = parse_action_requests(line)
        assert len(result) == 0


class TestPendingActionRequests:
    """Filtering to only pending requests."""

    def test_filters_pending_only(self) -> None:
        text = "\n".join([
            "- [ar-001] commit: -m 'fix' (status: pending)",
            "- [ar-002] push: origin main (status: completed)",
            "- [ar-003] run_check: --profile ci (status: pending)",
        ])
        result = pending_action_requests(text)
        assert len(result) == 2
        assert all(r.status == "pending" for r in result)

    def test_empty_when_none_pending(self) -> None:
        text = "- [ar-001] commit: -m 'fix' (status: completed)"
        assert pending_action_requests(text) == []


class TestValidateActionRequest:
    """Validation of parsed action requests."""

    def test_valid_commit_passes(self) -> None:
        req = ActionRequest(id="ar-001", action="commit", payload="-m 'fix'", status="pending")
        assert validate_action_request(req) == []

    def test_valid_push_passes(self) -> None:
        req = ActionRequest(id="ar-002", action="push", payload="origin main", status="pending")
        assert validate_action_request(req) == []

    def test_valid_run_check_passes(self) -> None:
        req = ActionRequest(id="ar-003", action="run_check", payload="--profile ci", status="pending")
        assert validate_action_request(req) == []

    def test_valid_kill_process_passes(self) -> None:
        req = ActionRequest(id="ar-004", action="kill_process", payload="pid 12345", status="pending")
        assert validate_action_request(req) == []

    def test_unsupported_action_fails(self) -> None:
        req = ActionRequest(id="ar-001", action="reboot", payload="now", status="pending")
        errors = validate_action_request(req)
        assert len(errors) == 1
        assert "Unsupported action kind" in errors[0]

    def test_missing_id_fails(self) -> None:
        req = ActionRequest(id="", action="commit", payload="-m 'fix'", status="pending")
        errors = validate_action_request(req)
        assert any("missing an id" in e for e in errors)

    def test_missing_payload_fails(self) -> None:
        req = ActionRequest(id="ar-001", action="commit", payload="", status="pending")
        errors = validate_action_request(req)
        assert any("missing a payload" in e for e in errors)


class TestRenderActionRequests:
    """Rendering action requests back to canonical bridge lines."""

    def test_round_trip_single_request(self) -> None:
        req = ActionRequest(id="ar-001", action="commit", payload="-m 'fix typo'", status="pending")
        rendered = render_action_request_line(req)
        parsed = parse_action_requests(rendered)
        assert len(parsed) == 1
        assert parsed[0] == req

    def test_render_section_empty(self) -> None:
        body = render_action_requests_section([])
        assert body == default_section_body()

    def test_render_section_multiple(self) -> None:
        requests = [
            ActionRequest(id="ar-001", action="commit", payload="-m 'fix'", status="pending"),
            ActionRequest(id="ar-002", action="push", payload="origin main", status="completed"),
        ]
        body = render_action_requests_section(requests)
        parsed = parse_action_requests(body)
        assert len(parsed) == 2


class TestBridgeIntegration:
    """Action Requests integration with the bridge validation/sanitization stack."""

    def test_action_requests_in_tracked_sections(self) -> None:
        assert SECTION_HEADING in TRACKED_BRIDGE_SECTIONS

    def test_action_requests_in_allowed_h2(self) -> None:
        assert SECTION_HEADING in BRIDGE_ALLOWED_H2

    def test_action_requests_in_section_line_limits(self) -> None:
        assert SECTION_HEADING in BRIDGE_SECTION_LINE_LIMITS

    def test_sanitize_bridge_sections_handles_action_requests(self) -> None:
        sections = {
            "Action Requests": "\n".join([
                "- [ar-001] commit: -m 'fix typo' (status: pending)",
                "- [ar-002] push: origin main (status: completed)",
            ]),
        }
        sanitized, _ = sanitize_bridge_sections(
            sections,
            section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
        )
        assert "ar-001" in sanitized["Action Requests"]
        assert "ar-002" in sanitized["Action Requests"]

    def test_sanitize_bridge_sections_defaults_empty_action_requests(self) -> None:
        sections: dict[str, str] = {}
        sanitized, _ = sanitize_bridge_sections(
            sections,
            section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
        )
        assert sanitized["Action Requests"] == default_section_body()

    def test_sanitize_bridge_sections_drops_malformed_action_lines(self) -> None:
        sections = {
            "Action Requests": "\n".join([
                "- [ar-001] commit: -m 'fix typo' (status: pending)",
                "This line is garbage from a terminal dump.",
                "- [ar-002] push: origin main (status: completed)",
            ]),
        }
        sanitized, _ = sanitize_bridge_sections(
            sections,
            section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
        )
        parsed = parse_action_requests(sanitized["Action Requests"])
        assert len(parsed) == 2
        assert "garbage" not in sanitized["Action Requests"]


class TestActionKindEnum:
    """Action kind enum coverage."""

    def test_all_kinds_in_valid_set(self) -> None:
        for kind in ActionKind:
            assert kind.value in VALID_ACTION_KINDS

    def test_valid_set_has_four_members(self) -> None:
        assert len(VALID_ACTION_KINDS) == 4
        assert VALID_ACTION_KINDS == {"commit", "run_check", "push", "kill_process"}


class TestActionRequestsFromPackets:
    """Packet-projection helpers: canonical transport for action requests."""

    def test_projects_pending_action_request_packets(self) -> None:
        packets: list[dict[str, object]] = [
            {
                "packet_id": "rev_pkt_0001",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "commit",
                "body": "-m 'fix typo'",
            },
            {
                "packet_id": "rev_pkt_0002",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "push",
                "body": "origin main",
            },
        ]
        result = action_requests_from_packets(packets)
        assert len(result) == 2
        assert result[0].id == "rev_pkt_0001"
        assert result[0].action == "commit"
        assert result[0].payload == "-m 'fix typo'"
        assert result[0].status == "pending"
        assert result[1].action == "push"

    def test_excludes_non_pending_packets(self) -> None:
        packets: list[dict[str, object]] = [
            {
                "packet_id": "rev_pkt_0001",
                "kind": "action_request",
                "status": "applied",
                "requested_action": "commit",
                "body": "-m 'done'",
            },
            {
                "packet_id": "rev_pkt_0002",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "push",
                "body": "origin main",
            },
        ]
        result = action_requests_from_packets(packets)
        assert len(result) == 1
        assert result[0].id == "rev_pkt_0002"

    def test_excludes_non_action_request_packets(self) -> None:
        packets: list[dict[str, object]] = [
            {
                "packet_id": "rev_pkt_0001",
                "kind": "finding",
                "status": "pending",
                "requested_action": "review_only",
                "body": "Some finding.",
            },
            {
                "packet_id": "rev_pkt_0002",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "run_check",
                "body": "--profile ci",
            },
        ]
        result = action_requests_from_packets(packets)
        assert len(result) == 1
        assert result[0].action == "run_check"

    def test_empty_packets_returns_empty(self) -> None:
        assert action_requests_from_packets([]) == []

    def test_render_from_packets_matches_legacy_format(self) -> None:
        """Packet-projected rendering produces the same format as legacy parsing."""
        packets: list[dict[str, object]] = [
            {
                "packet_id": "ar-001",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "commit",
                "body": "-m 'fix typo'",
            },
        ]
        rendered = render_action_requests_from_packets(packets)
        parsed_back = parse_action_requests(rendered)
        assert len(parsed_back) == 1
        assert parsed_back[0].id == "ar-001"
        assert parsed_back[0].action == "commit"
        assert parsed_back[0].payload == "-m 'fix typo'"
        assert parsed_back[0].status == "pending"

    def test_render_from_packets_empty_returns_default(self) -> None:
        rendered = render_action_requests_from_packets([])
        assert rendered == default_section_body()

    def test_no_second_queue_packet_and_legacy_converge(self) -> None:
        """Prove there is no second queue: packet projection and legacy parsing
        produce identical ActionRequest rows for the same logical state."""
        packets: list[dict[str, object]] = [
            {
                "packet_id": "ar-001",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "commit",
                "body": "-m 'fix typo'",
            },
            {
                "packet_id": "ar-002",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "push",
                "body": "origin feature/foo",
            },
        ]
        # Packet projection path
        from_packets = action_requests_from_packets(packets)
        rendered_from_packets = render_action_requests_section(from_packets)

        # Legacy bridge-text path round-trips through the same markdown
        from_legacy = parse_action_requests(rendered_from_packets)
        rendered_from_legacy = render_action_requests_section(from_legacy)

        assert from_packets == from_legacy
        assert rendered_from_packets == rendered_from_legacy
