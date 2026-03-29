"""Tests for runtime/role_profile.py — provider-agnostic role profiles."""

from __future__ import annotations

from dev.scripts.devctl.runtime.role_profile import (
    DEFAULT_PROVIDER_ROLE_MAP,
    RoleProfile,
    TandemProfile,
    TandemRole,
    build_default_tandem_profile,
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


class TestRoleForProvider:
    def test_codex_is_reviewer(self):
        assert role_for_provider("codex") == TandemRole.REVIEWER

    def test_claude_is_implementer(self):
        assert role_for_provider("claude") == TandemRole.IMPLEMENTER

    def test_cursor_is_implementer(self):
        assert role_for_provider("cursor") == TandemRole.IMPLEMENTER

    def test_operator_is_operator(self):
        assert role_for_provider("operator") == TandemRole.OPERATOR

    def test_unknown_defaults_to_implementer(self):
        assert role_for_provider("gemini") == TandemRole.IMPLEMENTER

    def test_case_insensitive(self):
        assert role_for_provider("Codex") == TandemRole.REVIEWER
        assert role_for_provider("CLAUDE") == TandemRole.IMPLEMENTER

    def test_custom_map(self):
        custom = {"gemini": TandemRole.REVIEWER}
        assert role_for_provider("gemini", custom) == TandemRole.REVIEWER


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
