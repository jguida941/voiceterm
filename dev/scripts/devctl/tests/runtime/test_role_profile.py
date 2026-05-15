"""Tests for runtime/role_profile.py — provider-agnostic role profiles."""

from __future__ import annotations

from dev.scripts.devctl.runtime.role_profile import (
    DEFAULT_PROVIDER_ROLE_MAP,
    OPERATOR_DIRECTIVE_CAPABILITIES,
    OperatorDirectivePacket,
    default_provider_for_role,
    normalize_tandem_role,
    OperatorRole,
    RoleProfile,
    TandemProfile,
    TandemRole,
    build_default_tandem_profile,
    operator_directive_packet_from_mapping,
    role_for_provider,
    role_profile_from_mapping,
)


class TestTandemRole:
    def test_role_values(self):
        assert TandemRole.REVIEWER == "reviewer"
        assert TandemRole.IMPLEMENTER == "implementer"
        assert TandemRole.OPERATOR == "operator"

    def test_role_is_str_enum(self):
        assert isinstance(TandemRole.REVIEWER, str)


class TestOperatorRole:
    def test_human_operator_role_and_capabilities(self):
        assert OperatorRole.HUMAN_OPERATOR == "human_operator"
        assert OperatorRole.AGENT_RUNTIME == "agent_runtime"
        assert OperatorRole.AUTOMATION_LOOP == "automation_loop"
        assert OperatorRole.REMOTE_OPERATOR == "remote_operator"
        assert OPERATOR_DIRECTIVE_CAPABILITIES == (
            "directive_authority",
            "bypass_authority",
            "override_authority",
            "dogfood_witness",
        )


class TestOperatorDirectivePacket:
    def test_packet_marshal_defaults_to_operator_capabilities(self):
        packet = OperatorDirectivePacket(
            directive_id="directive-1",
            operator_role=OperatorRole.HUMAN_OPERATOR.value,
            issued_by="operator",
            target_role="implementer",
            target_session_id="session-1",
            scope="edit-only",
            summary="continue current slice",
        )

        payload = packet.to_dict()

        assert payload["contract_id"] == "OperatorDirectivePacket"
        assert payload["capabilities"] == OPERATOR_DIRECTIVE_CAPABILITIES
        assert payload["operator_role"] == "human_operator"

    def test_packet_from_mapping_normalizes_operator_source(self):
        packet = operator_directive_packet_from_mapping(
            {
                "directive_id": "directive-2",
                "operator_role": "remote operator",
                "target_role": "implementer",
                "target_session_id": "session-2",
                "scope": "edit-and-commit",
                "summary": "stage governed checkpoint",
                "evidence_refs": ["operator:2026-05-15"],
            }
        )

        assert packet.operator_role == OperatorRole.REMOTE_OPERATOR.value
        assert packet.issued_by == OperatorRole.REMOTE_OPERATOR.value
        assert packet.capabilities == OPERATOR_DIRECTIVE_CAPABILITIES
        assert packet.evidence_refs == ("operator:2026-05-15",)


class TestRoleForProvider:
    def test_codex_is_reviewer(self):
        assert role_for_provider("codex") == TandemRole.REVIEWER

    def test_claude_is_implementer(self):
        assert role_for_provider("claude") == TandemRole.IMPLEMENTER

    def test_cursor_is_implementer(self):
        assert role_for_provider("cursor") == TandemRole.IMPLEMENTER

    def test_operator_is_operator(self):
        assert role_for_provider("operator") == TandemRole.OPERATOR
        assert role_for_provider("human_operator") == TandemRole.OPERATOR
        assert role_for_provider("remote_operator") == TandemRole.OPERATOR

    def test_unknown_defaults_to_implementer(self):
        assert role_for_provider("gemini") == TandemRole.IMPLEMENTER

    def test_case_insensitive(self):
        assert role_for_provider("Codex") == TandemRole.REVIEWER
        assert role_for_provider("CLAUDE") == TandemRole.IMPLEMENTER

    def test_custom_map(self):
        custom = {"gemini": TandemRole.REVIEWER}
        assert role_for_provider("gemini", custom) == TandemRole.REVIEWER


class TestRoleHelpers:
    def test_normalize_tandem_role_accepts_aliases(self):
        assert normalize_tandem_role("review") == TandemRole.REVIEWER
        assert normalize_tandem_role("coder") == TandemRole.IMPLEMENTER
        assert normalize_tandem_role("approver") == TandemRole.OPERATOR
        assert normalize_tandem_role("remote operator") == TandemRole.OPERATOR

    def test_default_provider_for_role_uses_default_mapping(self):
        assert default_provider_for_role("reviewer") == "codex"
        assert default_provider_for_role("implementer") == "claude"
        assert default_provider_for_role("operator") == "operator"


class TestRoleProfile:
    def test_frozen(self):
        profile = RoleProfile(
            schema_version=1,
            contract_id="RoleProfile",
            role="reviewer",
            provider="codex",
            display_name="Codex",
            capabilities=("review",),
        )
        assert profile.role == "reviewer"
        assert profile.provider == "codex"
        assert profile.active is True

    def test_to_dict(self):
        profile = RoleProfile(
            schema_version=1,
            contract_id="RoleProfile",
            role="implementer",
            provider="claude",
            display_name="Claude",
            capabilities=("code", "fix"),
        )
        d = profile.to_dict()
        assert d["role"] == "implementer"
        assert d["provider"] == "claude"
        assert d["capabilities"] == ("code", "fix")


class TestRoleProfileFromMapping:
    def test_basic_parse(self):
        payload = {
            "provider": "codex",
            "role": "reviewer",
            "display_name": "Codex",
            "capabilities": ["review", "promote"],
        }
        profile = role_profile_from_mapping(payload)
        assert profile.role == "reviewer"
        assert profile.provider == "codex"
        assert profile.capabilities == ("review", "promote")

    def test_infers_role_from_provider(self):
        payload = {"provider": "claude"}
        profile = role_profile_from_mapping(payload)
        assert profile.role == "implementer"

    def test_missing_provider(self):
        payload = {"role": "operator"}
        profile = role_profile_from_mapping(payload)
        assert profile.provider == "unknown"


class TestTandemProfile:
    def test_all_roles(self):
        tp = build_default_tandem_profile()
        roles = tp.all_roles()
        assert len(roles) == 3
        assert roles[0].role == "reviewer"
        assert roles[1].role == "implementer"
        assert roles[2].role == "operator"

    def test_by_provider(self):
        tp = build_default_tandem_profile()
        assert tp.by_provider("codex").role == "reviewer"
        assert tp.by_provider("claude").role == "implementer"
        assert tp.by_provider("operator").role == "operator"
        assert tp.by_provider("unknown") is None

    def test_multiple_implementers(self):
        tp = build_default_tandem_profile(
            implementer_providers=("claude", "cursor"),
        )
        assert len(tp.implementers) == 2
        assert all(i.role == "implementer" for i in tp.implementers)

    def test_to_dict(self):
        tp = build_default_tandem_profile()
        d = tp.to_dict()
        assert d["schema_version"] == 1
        assert d["reviewer"]["provider"] == "codex"
        assert d["operator"]["provider"] == "operator"

    def test_custom_providers(self):
        tp = build_default_tandem_profile(
            reviewer_provider="gemini",
            implementer_providers=("claude",),
            operator_provider="human",
        )
        assert tp.reviewer.provider == "gemini"
        assert tp.reviewer.role == "reviewer"
        assert tp.operator.provider == "human"
