"""A16 G19 focused tests: provider pre-tool hook coverage guard.

Five named scenarios per delete_after_ingest.md A16 G19:

1. Claude settings with the current PreToolUse command pass the configured
   portion (state == hook_configured).
2. Claude settings missing ``--tool-input-stdin`` fail.
3. A non-Claude provider with no hook metadata fails as
   ``provider_pre_tool_hook_missing``.
4. A non-Claude provider with hook metadata but no execution receipt fails as
   ``provider_pre_tool_hook_unproven``.
5. A provider-neutral fixture with a tested equivalent hook passes.
"""

from __future__ import annotations

from typing import Any

from dev.scripts.checks.check_provider_pre_tool_hook_coverage import (
    HOOK_STATE_CONFIGURED,
    HOOK_STATE_MISSING,
    HOOK_STATE_TESTED,
    HOOK_STATE_UNAVAILABLE_BLOCKER,
    PROVIDER_HOOK_CLAIM_WITHOUT_TEST_REASON,
    PROVIDER_HOOK_MISSING_REASON,
    PROVIDER_HOOK_NOT_PRE_MUTATION_REASON,
    PROVIDER_HOOK_UNPROVEN_REASON,
    build_report,
    evaluate_claude_settings,
)


def _claude_valid_settings() -> dict[str, Any]:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                'python3 "$CLAUDE_PROJECT_DIR/dev/scripts/checks/'
                                'check_role_lane_mutation_authority.py" '
                                "--mode pre_mutation --tool-input-stdin --format md"
                            ),
                        }
                    ],
                }
            ]
        }
    }


def _claude_missing_stdin_settings() -> dict[str, Any]:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write|MultiEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                'python3 "$CLAUDE_PROJECT_DIR/dev/scripts/checks/'
                                'check_role_lane_mutation_authority.py" '
                                "--mode pre_mutation --format md"
                            ),
                        }
                    ],
                }
            ]
        }
    }


def _reasons(report: dict[str, Any]) -> set[str]:
    return {v["reason"] for v in report.get("violations", []) if isinstance(v, dict)}


def _state_for_provider(report: dict[str, Any], provider: str) -> str:
    for s in report.get("provider_states", []):
        if isinstance(s, dict) and s.get("provider") == provider:
            return s.get("state", "")
    return ""


def test_claude_settings_configured_portion_passes_classification() -> None:
    """A16 G19 named test #1: Claude settings with the current PreToolUse
    command pass the configured portion (state == hook_configured).
    """
    state = evaluate_claude_settings(_claude_valid_settings())
    assert state.provider == "claude"
    assert state.state == HOOK_STATE_CONFIGURED


def test_claude_settings_missing_stdin_flag_fails() -> None:
    """A16 G19 named test #2: Claude settings missing --tool-input-stdin must
    fail with provider_pre_tool_hook_not_pre_mutation reason.
    """
    report = build_report(
        report_override={"claude_settings": _claude_missing_stdin_settings()}
    )
    assert report["ok"] is False
    reasons = _reasons(report)
    assert PROVIDER_HOOK_NOT_PRE_MUTATION_REASON in reasons


def test_other_provider_with_no_hook_metadata_fails_as_missing() -> None:
    """A16 G19 named test #3: a non-Claude provider declared with no hook
    metadata must fail as provider_pre_tool_hook_missing.
    """
    report = build_report(
        report_override={
            "provider_states": [
                {
                    "provider": "codex-impl",
                    "state": HOOK_STATE_MISSING,
                    "source": "fixture",
                    "detail": "No pre-tool hook declared",
                }
            ]
        }
    )
    assert report["ok"] is False
    reasons = _reasons(report)
    assert PROVIDER_HOOK_MISSING_REASON in reasons


def test_other_provider_with_metadata_but_no_execution_receipt_fails_unproven() -> None:
    """A16 G19 named test #4: a non-Claude provider with hook metadata but no
    execution receipt fails as provider_pre_tool_hook_unproven.
    """
    report = build_report(
        report_override={
            "provider_metadata": [
                {
                    "provider": "codex-impl",
                    "state": HOOK_STATE_CONFIGURED,
                    "detail": "Hook declared in launcher wrapper, no execution receipt observed yet.",
                }
            ]
        }
    )
    assert report["ok"] is False
    reasons = _reasons(report)
    assert PROVIDER_HOOK_UNPROVEN_REASON in reasons


def test_provider_neutral_tested_fixture_passes() -> None:
    """A16 G19 named test #5: a provider-neutral fixture with a tested
    equivalent hook passes (state == hook_tested, no violations).
    """
    report = build_report(
        report_override={
            "provider_states": [
                {
                    "provider": "impl-provider-A",
                    "state": HOOK_STATE_TESTED,
                    "source": "fixture",
                    "detail": "Tested via dev/scripts/devctl/tests/checks/test_provider_A_pre_tool.py",
                },
                {
                    "provider": "impl-provider-B",
                    "state": HOOK_STATE_TESTED,
                    "source": "fixture",
                    "detail": "Tested via dev/scripts/devctl/tests/checks/test_provider_B_pre_tool.py",
                },
            ]
        }
    )
    assert report["ok"] is True, report


def test_unavailable_blocker_with_ref_passes() -> None:
    """A provider that declares hook_unavailable_blocker WITH a blocker_ref
    passes (acknowledged typed blocker). Without a ref it should downgrade to
    hook_missing.
    """
    report = build_report(
        report_override={
            "provider_metadata": [
                {
                    "provider": "ide-only-provider",
                    "state": HOOK_STATE_UNAVAILABLE_BLOCKER,
                    "blocker_ref": "packet:rev_pkt_blocker_42",
                    "detail": "IDE provider lacks pre-tool hooks; blocker filed",
                }
            ]
        }
    )
    assert report["ok"] is True


def test_unavailable_blocker_without_ref_downgrades_to_missing() -> None:
    report = build_report(
        report_override={
            "provider_metadata": [
                {
                    "provider": "claimed-blocker-provider",
                    "state": HOOK_STATE_UNAVAILABLE_BLOCKER,
                    "detail": "Provider claims blocker but no ref provided",
                }
            ]
        }
    )
    assert report["ok"] is False
    reasons = _reasons(report)
    assert PROVIDER_HOOK_MISSING_REASON in reasons


def test_a16_g19_live_review_channel_registry_agents_emit_all_providers() -> None:
    """rev_pkt_4816: live review-channel state's registry.agents must be a
    provider discovery source so the guard never silently omits an active
    provider. Fixture mimics the live shape with codex+claude both present.
    """
    report = build_report(
        report_override={
            "review_channel_state": {
                "registry": {
                    "agents": [
                        {"agent_id": "claude-impl", "provider": "claude"},
                        {"agent_id": "codex-rev", "provider": "codex"},
                    ]
                }
            },
            # Claude has a working settings.json fixture so it gets classified
            "claude_settings": _claude_valid_settings(),
        }
    )
    providers_reported = {s["provider"] for s in report["provider_states"]}
    assert "claude" in providers_reported
    assert "codex" in providers_reported, report["provider_states"]
    # Codex must show as hook_missing (no metadata, no settings file analogue)
    codex_state = _state_for_provider(report, "codex")
    assert codex_state == HOOK_STATE_MISSING
    # And a typed blocker fires for codex
    reasons = _reasons(report)
    assert PROVIDER_HOOK_MISSING_REASON in reasons


def test_a16_g19_live_provider_already_in_metadata_not_duplicated() -> None:
    """If a provider appears in BOTH review_channel_state.registry.agents AND
    provider_metadata, only the metadata-derived entry is kept.
    """
    report = build_report(
        report_override={
            "provider_metadata": [
                {
                    "provider": "codex",
                    "state": HOOK_STATE_TESTED,
                    "detail": "metadata declares hook_tested",
                }
            ],
            "review_channel_state": {
                "registry": {
                    "agents": [
                        {"provider": "codex"},
                        {"provider": "claude"},
                    ]
                }
            },
            "claude_settings": _claude_valid_settings(),
        }
    )
    codex_entries = [
        s for s in report["provider_states"] if s.get("provider") == "codex"
    ]
    assert len(codex_entries) == 1
    assert codex_entries[0]["state"] == HOOK_STATE_TESTED


def _codex_valid_hooks() -> dict[str, Any]:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "edit|write|multiedit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "python3 dev/scripts/checks/check_role_lane_mutation_authority.py "
                                "--mode pre_mutation --tool-input-stdin --format md"
                            ),
                        }
                    ],
                }
            ]
        }
    }


def test_a16_g19_codex_hooks_configured_classification() -> None:
    """rev_pkt_4818: a valid .codex/hooks.json with the required PreToolUse
    config classifies codex as hook_configured (passes config check, fails
    on execution receipt).
    """
    report = build_report(
        report_override={"codex_hooks": _codex_valid_hooks()}
    )
    codex_state = _state_for_provider(report, "codex")
    assert codex_state == HOOK_STATE_CONFIGURED
    reasons = _reasons(report)
    # hook_configured without execution receipt fails as unproven
    assert PROVIDER_HOOK_UNPROVEN_REASON in reasons


def test_a16_g19_codex_hooks_missing_stdin_flag_fails_not_pre_mutation() -> None:
    """If .codex/hooks.json declares a PreToolUse but omits --tool-input-stdin,
    classify hook_configured with detail naming missing pieces; surface
    provider_pre_tool_hook_not_pre_mutation per the same rule as Claude.
    """
    bad = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "edit|write|multiedit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "python3 dev/scripts/checks/check_role_lane_mutation_authority.py "
                                "--mode pre_mutation --format md"
                            ),
                        }
                    ],
                }
            ]
        }
    }
    report = build_report(report_override={"codex_hooks": bad})
    reasons = _reasons(report)
    assert PROVIDER_HOOK_NOT_PRE_MUTATION_REASON in reasons


def test_a16_g19_codex_hook_only_in_registry_remains_missing() -> None:
    """When registry.agents names codex but no .codex/hooks.json fixture is
    provided AND no metadata, codex must classify hook_missing.
    """
    report = build_report(
        report_override={
            "review_channel_state": {
                "registry": {"agents": [{"provider": "codex"}]}
            }
        }
    )
    codex_state = _state_for_provider(report, "codex")
    assert codex_state == HOOK_STATE_MISSING
    reasons = _reasons(report)
    assert PROVIDER_HOOK_MISSING_REASON in reasons


def test_a16_g19_codex_hook_tested_via_metadata_passes_for_codex() -> None:
    """rev_pkt_4819 hardened version: typed tested evidence via provider_metadata
    must (a) override the weaker .codex/hooks.json config-layer state,
    (b) leave exactly ONE codex entry in provider_states, AND
    (c) make report['ok'] = True (no provider_pre_tool_hook_unproven violation
    from the duplicate configured state).
    """
    report = build_report(
        report_override={
            "codex_hooks": _codex_valid_hooks(),
            "provider_metadata": [
                {
                    "provider": "codex",
                    "state": HOOK_STATE_TESTED,
                    "detail": "Execution receipt observed at attempted_action:abc123",
                }
            ],
        }
    )
    codex_entries = [
        s for s in report["provider_states"] if s.get("provider") == "codex"
    ]
    # Strongest-state precedence: exactly one codex entry survives.
    assert len(codex_entries) == 1, codex_entries
    assert codex_entries[0]["state"] == HOOK_STATE_TESTED
    # And the configured duplicate's unproven violation must NOT fire.
    reasons = _reasons(report)
    assert PROVIDER_HOOK_UNPROVEN_REASON not in reasons
    # When codex is the only provider declared in the fixture, ok=True.
    assert report["ok"] is True, report


def test_a16_g19_precedence_metadata_tested_beats_config_layer() -> None:
    """Per-provider precedence test: provider_metadata hook_tested must beat
    .codex/hooks.json hook_configured even when both list codex.
    """
    report = build_report(
        report_override={
            "codex_hooks": _codex_valid_hooks(),
            "provider_metadata": [
                {
                    "provider": "codex",
                    "state": HOOK_STATE_TESTED,
                    "detail": "stronger evidence",
                }
            ],
        }
    )
    codex_state = _state_for_provider(report, "codex")
    assert codex_state == HOOK_STATE_TESTED


def test_a16_g19_precedence_unavailable_blocker_beats_missing() -> None:
    """A provider listed as hook_missing in one source AND hook_unavailable_blocker
    (with valid blocker_ref) in another must end up as hook_unavailable_blocker.
    """
    report = build_report(
        report_override={
            "provider_states": [
                {
                    "provider": "ide-provider",
                    "state": HOOK_STATE_MISSING,
                    "source": "registry.agents",
                    "detail": "Discovered via registry observation only",
                }
            ],
            "provider_metadata": [
                {
                    "provider": "ide-provider",
                    "state": HOOK_STATE_UNAVAILABLE_BLOCKER,
                    "blocker_ref": "packet:rev_pkt_blocker_42",
                    "detail": "IDE provider acknowledged blocker",
                }
            ],
        }
    )
    state = _state_for_provider(report, "ide-provider")
    assert state == HOOK_STATE_UNAVAILABLE_BLOCKER
    assert report["ok"] is True


def test_a16_g19_precedence_does_not_demote_strong_to_weak() -> None:
    """Order shouldn't matter: a strong state appearing AFTER a weak one for
    the same provider must still win (insertion order preserved for the
    surviving entry, but strength wins over recency).
    """
    report = build_report(
        report_override={
            "provider_states": [
                {
                    "provider": "p1",
                    "state": HOOK_STATE_TESTED,
                    "source": "early",
                    "detail": "strong appeared first",
                },
                {
                    "provider": "p1",
                    "state": HOOK_STATE_CONFIGURED,
                    "source": "later",
                    "detail": "weaker appeared later",
                },
            ]
        }
    )
    assert _state_for_provider(report, "p1") == HOOK_STATE_TESTED
    # Only one entry per provider survives the dedupe.
    p1_entries = [
        s for s in report["provider_states"] if s.get("provider") == "p1"
    ]
    assert len(p1_entries) == 1


def test_unknown_state_classification_uses_claim_without_test() -> None:
    """An unrecognized state string must fail closed with
    provider_hook_claim_without_test.
    """
    report = build_report(
        report_override={
            "provider_states": [
                {
                    "provider": "unknown-state-provider",
                    "state": "make_believe_state",
                    "source": "fixture",
                    "detail": "",
                }
            ]
        }
    )
    assert report["ok"] is False
    reasons = _reasons(report)
    assert PROVIDER_HOOK_CLAIM_WITHOUT_TEST_REASON in reasons
