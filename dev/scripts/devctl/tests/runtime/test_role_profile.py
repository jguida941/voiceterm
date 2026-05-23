"""Tests for runtime/role_profile.py — provider-agnostic role profiles."""

from __future__ import annotations

from dev.scripts.devctl.runtime.role_profile import (
    DEFAULT_PROVIDER_ROLE_MAP,
    OPERATOR_DIRECTIVE_CAPABILITIES,
    OperatorDirectivePacket,
    default_provider_for_role,
    normalize_role_id,
    normalize_tandem_role,
    OperatorRole,
    role_capability_classes,
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
    def test_provider_identity_does_not_imply_role_without_typed_map(self):
        assert role_for_provider("codex") is None
        assert role_for_provider("claude") is None
        assert role_for_provider("cursor") is None

    def test_operator_is_operator(self):
        custom = {
            "operator": TandemRole.OPERATOR,
            "human_operator": TandemRole.OPERATOR,
            "remote_operator": TandemRole.OPERATOR,
        }
        assert role_for_provider("operator", custom) == TandemRole.OPERATOR
        assert role_for_provider("human_operator", custom) == TandemRole.OPERATOR
        assert role_for_provider("remote_operator", custom) == TandemRole.OPERATOR

    def test_unknown_fails_closed_without_typed_map(self):
        assert role_for_provider("gemini") is None

    def test_case_insensitive(self):
        custom = {"codex": TandemRole.IMPLEMENTER, "claude": TandemRole.REVIEWER}
        assert role_for_provider("Codex", custom) == TandemRole.IMPLEMENTER
        assert role_for_provider("CLAUDE", custom) == TandemRole.REVIEWER

    def test_custom_map(self):
        custom = {
            "codex": TandemRole.IMPLEMENTER,
            "claude": TandemRole.REVIEWER,
            "gemini": TandemRole.REVIEWER,
        }
        assert role_for_provider("codex", custom) == TandemRole.IMPLEMENTER
        assert role_for_provider("claude", custom) == TandemRole.REVIEWER
        assert role_for_provider("gemini", custom) == TandemRole.REVIEWER


class TestRoleHelpers:
    def test_normalize_tandem_role_accepts_aliases(self):
        assert normalize_tandem_role("review") == TandemRole.REVIEWER
        assert normalize_tandem_role("coder") == TandemRole.IMPLEMENTER
        assert normalize_tandem_role("approver") == TandemRole.OPERATOR
        assert normalize_tandem_role("remote operator") == TandemRole.OPERATOR

    def test_normalize_role_id_preserves_typed_roles_and_canonical_aliases(self):
        assert normalize_role_id("TDDFirstRole") == "tdd_first_role"
        assert normalize_role_id("tdd_discovery") == "tdd_discovery"
        assert normalize_role_id("dogfooder") == "dogfood_test"
        assert normalize_role_id("DogfoodTestRole") == "dogfood_test"
        assert normalize_role_id("GovernanceReceiptRole") == "governance_receipt"
        assert normalize_role_id("operator inquiry role") == "operator_inquiry_role"
        assert normalize_role_id("custom future role") == "custom_future_role"

    def test_role_capability_classes_are_secondary_metadata(self):
        assert role_capability_classes("tdd_first_role") == ("test",)
        assert role_capability_classes("architecture_review") == (
            "review",
            "architecture",
        )
        assert role_capability_classes("custom future role") == ()

    def test_default_provider_for_role_requires_typed_map(self):
        assert default_provider_for_role("reviewer") == ""
        assert default_provider_for_role("implementer") == ""
        assert default_provider_for_role("operator") == ""
        custom = {"claude": TandemRole.REVIEWER, "codex": TandemRole.IMPLEMENTER}
        assert default_provider_for_role("reviewer", custom) == "claude"
        assert default_provider_for_role("implementer", custom) == "codex"


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

    def test_provider_only_does_not_infer_role(self):
        payload = {"provider": "claude"}
        profile = role_profile_from_mapping(payload)
        assert profile.role == ""

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
        assert tp.by_provider("codex") is None
        assert tp.by_provider("claude") is None
        assert tp.by_provider("unassigned") is not None
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
        assert d["reviewer"]["provider"] == "unassigned"
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
