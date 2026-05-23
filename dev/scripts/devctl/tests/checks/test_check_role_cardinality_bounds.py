"""Tests for ``check_role_cardinality_bounds`` (A18 G31).

RED+GREEN coverage for each RULE_* constant plus assignment/occupancy
indexing, fallback-policy validation, merge-owner detection, output
schema, and markdown rendering.
"""

from __future__ import annotations

import json

import pytest

from dev.scripts.checks import check_role_cardinality_bounds as guard


def _assignment(
    *,
    role_id: str,
    min_actors: int = 1,
    desired_actors: int = 1,
    max_actors: int = 1,
    fallback_policy: str = "block",
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "role_id": role_id,
        "min_actors": min_actors,
        "desired_actors": desired_actors,
        "max_actors": max_actors,
        "fallback_policy": fallback_policy,
    }
    payload.update(extra)
    return payload


def _occupancy(
    *,
    role_id: str,
    actor_id: str,
    live: bool = True,
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "role_id": role_id,
        "actor_id": actor_id,
        "live": live,
    }
    payload.update(extra)
    return payload


# ---- GREEN baseline ---------------------------------------------------


def test_green_no_violations_with_balanced_role_state() -> None:
    """A live actor count inside [min, max] with a valid fallback policy passes."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                desired_actors=1,
                max_actors=2,
                fallback_policy="block",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="claude"),
        ],
    )
    assert report["ok"] is True
    assert report["evaluated_role_count"] == 1
    assert report["violation_count"] == 0
    assert report["violations"] == []
    assert report["display_text"] == ""


def test_green_with_no_assignments_and_no_occupancies() -> None:
    report = guard.build_report(role_assignments=[], role_occupancies=[])
    assert report["ok"] is True
    assert report["evaluated_role_count"] == 0


# ---- RULE_BELOW_MIN_ACTORS -------------------------------------------


def test_red_below_min_actors_when_no_live_actor() -> None:
    """Zero live actors against min_actors=1 fails BELOW_MIN_ACTORS."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="reviewer", min_actors=1, desired_actors=1, max_actors=1
            ),
        ],
        role_occupancies=[],
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BELOW_MIN_ACTORS in rule_ids
    below = next(
        v for v in report["violations"] if v["rule_id"] == guard.RULE_BELOW_MIN_ACTORS
    )
    assert below["role_id"] == "reviewer"
    assert below["live_actor_count"] == 0
    assert below["min_actors"] == 1


def test_green_above_min_actors_passes_below_check() -> None:
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="reviewer", min_actors=2, desired_actors=2, max_actors=3
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="reviewer", actor_id="codex"),
            _occupancy(role_id="reviewer", actor_id="claude"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BELOW_MIN_ACTORS not in rule_ids
    assert report["ok"] is True


def test_red_below_min_ignores_dead_occupancies() -> None:
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="operator", min_actors=1, desired_actors=1, max_actors=1
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="operator", actor_id="ghost", live=False),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_BELOW_MIN_ACTORS in rule_ids


# ---- RULE_ABOVE_MAX_ACTORS -------------------------------------------


def test_red_above_max_actors_with_overflow() -> None:
    """Three live implementers against max_actors=1 fails ABOVE_MAX_ACTORS.

    This mirrors the A18 drift example: one implementer expected, three
    implementers active.
    """
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                desired_actors=1,
                max_actors=1,
                fallback_policy="block",
                merge_owner_role_id="implementation_lead",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="claude"),
            _occupancy(role_id="implementer", actor_id="codex"),
            _occupancy(role_id="implementer", actor_id="extra"),
        ],
    )
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ABOVE_MAX_ACTORS in rule_ids
    above = next(
        v for v in report["violations"] if v["rule_id"] == guard.RULE_ABOVE_MAX_ACTORS
    )
    assert above["live_actor_count"] == 3
    assert above["max_actors"] == 1
    assert set(above["evidence_actor_ids"]) == {"claude", "codex", "extra"}


def test_green_at_max_actors_passes_above_check() -> None:
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                desired_actors=1,
                max_actors=2,
                fallback_policy="block",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="claude"),
            _occupancy(role_id="implementer", actor_id="codex"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ABOVE_MAX_ACTORS not in rule_ids


def test_above_max_skipped_when_max_is_zero() -> None:
    """``max_actors=0`` is treated as unbounded and skips the upper check."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="observer",
                min_actors=0,
                desired_actors=0,
                max_actors=0,
                fallback_policy="degrade",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="observer", actor_id=f"watcher_{i}")
            for i in range(5)
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ABOVE_MAX_ACTORS not in rule_ids


# ---- RULE_MISSING_FALLBACK_POLICY ------------------------------------


def test_red_missing_fallback_policy() -> None:
    """Assignment with an empty fallback_policy fails MISSING_FALLBACK_POLICY."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="reviewer",
                min_actors=1,
                desired_actors=1,
                max_actors=1,
                fallback_policy="",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="reviewer", actor_id="claude"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_FALLBACK_POLICY in rule_ids


def test_red_invalid_fallback_policy_value() -> None:
    """An unknown fallback policy literal fails MISSING_FALLBACK_POLICY."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="reviewer", fallback_policy="ignore"
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="reviewer", actor_id="claude"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_FALLBACK_POLICY in rule_ids


@pytest.mark.parametrize(
    "policy", ["block", "degrade", "queue", "operator_decision"]
)
def test_green_valid_fallback_policies(policy: str) -> None:
    report = guard.build_report(
        role_assignments=[
            _assignment(role_id="reviewer", fallback_policy=policy),
        ],
        role_occupancies=[
            _occupancy(role_id="reviewer", actor_id="claude"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_FALLBACK_POLICY not in rule_ids
    assert report["ok"] is True


# ---- RULE_NO_MERGE_OWNER_FOR_OVERFLOW --------------------------------


def test_red_overflow_without_merge_owner() -> None:
    """The A18 canonical example: 3 implementers, no typed merge owner."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                desired_actors=1,
                max_actors=1,
                fallback_policy="block",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="claude"),
            _occupancy(role_id="implementer", actor_id="codex"),
            _occupancy(role_id="implementer", actor_id="rogue"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ABOVE_MAX_ACTORS in rule_ids
    assert guard.RULE_NO_MERGE_OWNER_FOR_OVERFLOW in rule_ids


def test_green_overflow_with_assignment_merge_owner() -> None:
    """Overflow with a typed assignment merge_owner does not trigger merge rule."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                desired_actors=1,
                max_actors=1,
                fallback_policy="queue",
                merge_owner_role_id="implementation_lead",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="claude"),
            _occupancy(role_id="implementer", actor_id="codex"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    # Overflow itself still fails ABOVE_MAX_ACTORS:
    assert guard.RULE_ABOVE_MAX_ACTORS in rule_ids
    # But the merge-owner sub-rule should not fire when a typed owner exists:
    assert guard.RULE_NO_MERGE_OWNER_FOR_OVERFLOW not in rule_ids


def test_green_overflow_with_occupancy_merge_owner_flag() -> None:
    """A live occupancy carrying is_merge_owner=True satisfies the merge rule."""
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                desired_actors=1,
                max_actors=1,
                fallback_policy="queue",
            ),
        ],
        role_occupancies=[
            _occupancy(
                role_id="implementer",
                actor_id="claude",
                is_merge_owner=True,
            ),
            _occupancy(role_id="implementer", actor_id="codex"),
        ],
    )
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_NO_MERGE_OWNER_FOR_OVERFLOW not in rule_ids


# ---- Schema + rendering ----------------------------------------------


def test_output_schema_includes_required_fields() -> None:
    report = guard.build_report(role_assignments=[], role_occupancies=[])
    for field in (
        "ok",
        "evaluated_role_count",
        "violation_count",
        "checked_surfaces",
        "violations",
        "warnings",
        "command",
        "timestamp",
        "schema_version",
        "contract_id",
    ):
        assert field in report, f"missing required field {field!r}"
    assert report["command"] == guard.COMMAND
    assert report["contract_id"] == guard.CONTRACT_ID


def test_render_markdown_includes_violations() -> None:
    report = guard.build_report(
        role_assignments=[
            _assignment(
                role_id="implementer",
                min_actors=1,
                max_actors=1,
                fallback_policy="block",
            ),
        ],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="a"),
            _occupancy(role_id="implementer", actor_id="b"),
        ],
    )
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert guard.RULE_ABOVE_MAX_ACTORS in md
    assert "implementer" in md


def test_loads_role_state_from_path(tmp_path) -> None:
    """build_report falls back to role_state_path JSON when args omitted."""
    state_path = tmp_path / "role_cardinality.json"
    state_path.write_text(
        json.dumps(
            {
                "role_assignments": [
                    _assignment(
                        role_id="implementer",
                        min_actors=1,
                        max_actors=1,
                        fallback_policy="block",
                    ),
                ],
                "role_occupancies": [
                    _occupancy(role_id="implementer", actor_id="claude"),
                    _occupancy(role_id="implementer", actor_id="codex"),
                ],
            }
        ),
        encoding="utf-8",
    )
    report = guard.build_report(role_state_path=state_path)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_ABOVE_MAX_ACTORS in rule_ids
    assert str(state_path) in report["checked_surfaces"]


def test_missing_role_state_file_yields_warning(tmp_path) -> None:
    state_path = tmp_path / "missing.json"
    report = guard.build_report(role_state_path=state_path)
    assert report["ok"] is True
    assert any("role state missing" in w for w in report["warnings"])


def test_unknown_role_id_in_occupancies_is_evaluated() -> None:
    """Occupancies without a matching assignment still register in the role count."""
    report = guard.build_report(
        role_assignments=[],
        role_occupancies=[
            _occupancy(role_id="implementer", actor_id="claude"),
        ],
    )
    # Without an assignment we have no bounds to violate, so report stays ok.
    assert report["ok"] is True
    assert report["evaluated_role_count"] == 1
