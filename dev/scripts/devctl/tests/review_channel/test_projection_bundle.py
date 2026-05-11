"""Focused tests for review-channel projection bundle writes."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel import agent_work_board_posture
from dev.scripts.devctl.review_channel import projection_bundle as projection_bundle_mod
from dev.scripts.devctl.review_channel.event_reducer import (
    load_or_refresh_event_bundle,
    load_projected_event_bundle,
)
from dev.scripts.devctl.review_channel.event_store import resolve_artifact_paths
from dev.scripts.devctl.review_channel.projection_bundle import write_projection_bundle


def _minimal_review_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_id": "ReviewState",
        "command": "review-channel",
        "action": "status",
        "timestamp": "2026-05-07T00:00:00Z",
        "ok": True,
        "review": {"session_id": "session-1"},
        "queue": {"pending_total": 0},
        "current_session": {},
        "bridge": {"reviewer_mode": "tools_only"},
        "packets": [],
    }


def test_projection_bundle_writes_machine_json_compactly(tmp_path: Path) -> None:
    review_state = _minimal_review_state()
    review_state["packets"] = [
        {
            "packet_id": "rev_pkt_1",
            "requested_action": "review_only",
            "status": "pending",
        }
    ]

    paths = write_projection_bundle(
        output_root=tmp_path / "latest",
        review_state=review_state,
        agent_registry={"schema_version": 1, "agents": []},
        action="status",
    )

    for path_text in (
        paths.review_state_path,
        paths.compact_path,
        paths.full_path,
        paths.actions_path,
        paths.agent_registry_path,
        paths.commit_pipeline_path,
    ):
        text = Path(path_text).read_text(encoding="utf-8")
        assert "\n" not in text
        assert isinstance(json.loads(text), dict)


def test_projection_bundle_mirror_uses_single_canonical_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    original = projection_bundle_mod.canonicalize_projection_review_state
    calls = 0

    def canonicalize_once_per_publication(
        payload: dict[str, object],
    ) -> dict[str, object]:
        nonlocal calls
        calls += 1
        result = original(payload)
        result["snapshot_id"] = f"snap-{calls}"
        result["zref"] = f"zref_{calls}"
        return result

    monkeypatch.setattr(
        projection_bundle_mod,
        "canonicalize_projection_review_state",
        canonicalize_once_per_publication,
    )

    projection_bundle_mod.write_projection_bundle_mirrors(
        output_root=tmp_path / "projections/latest",
        mirror_roots=(tmp_path / "latest",),
        review_state=_minimal_review_state(),
        agent_registry={"schema_version": 1, "agents": []},
        action="status",
    )

    canonical_compact = json.loads(
        (tmp_path / "projections/latest/compact.json").read_text(encoding="utf-8")
    )
    mirror_compact = json.loads(
        (tmp_path / "latest/compact.json").read_text(encoding="utf-8")
    )

    assert calls == 1
    assert canonical_compact["snapshot_id"] == "snap-1"
    assert mirror_compact["snapshot_id"] == "snap-1"
    assert canonical_compact == mirror_compact


def test_prepare_projection_bundle_applies_work_board_posture_once(
    tmp_path: Path,
    monkeypatch,
) -> None:
    del tmp_path
    original = agent_work_board_posture.apply_work_board_session_posture
    calls = 0

    def count_posture_application(payload):
        nonlocal calls
        calls += 1
        return original(payload)

    monkeypatch.setattr(
        agent_work_board_posture,
        "apply_work_board_session_posture",
        count_posture_application,
    )
    review_state = _minimal_review_state()
    review_state["reviewer_runtime"] = {
        "session_posture": {
            "actors": [{"actor_id": "codex", "live": False}],
        }
    }
    review_state["agent_work_board"] = {
        "rows": [
            {
                "actor_id": "codex",
                "role": "reviewer",
                "status": "working",
                "idle_seconds": 0,
            }
        ]
    }

    contents = projection_bundle_mod.prepare_projection_bundle_contents(
        review_state=review_state,
        agent_registry={"schema_version": 1, "agents": []},
        action="status",
    )
    persisted = json.loads(contents.review_state_json)
    actors = persisted["reviewer_runtime"]["session_posture"]["actors"]

    assert calls == 1
    assert actors[0]["live"] is True
    assert actors[0]["source"] == "agent_work_board"


def test_prepare_projection_bundle_freezes_parity_fields_across_surfaces() -> None:
    review_state = _minimal_review_state()
    review_state.update(
        {
            "snapshot_id": "snap-frozen",
            "zref": "zref_frozen",
            "attention": {"status": "needs_review"},
            "recovery_assessment": {
                "diagnosis": {"status": "needs_review"},
                "decision": {
                    "action_id": "repair_surface",
                    "command": "python3 dev/scripts/checks/check_review_surface_consistency.py",
                },
            },
            "coordination": {"ownership_status": "scope_known"},
            "commit_pipeline": {
                "snapshot_id": "snap-frozen",
                "zref": "zref_frozen",
                "generation_id": "gen-frozen",
            },
            "_compat": {
                "doctor": {"diagnosis_status": "needs_review"},
                "push_decision": {"decision": "blocked"},
            },
        }
    )

    contents = projection_bundle_mod.prepare_projection_bundle_contents(
        review_state=review_state,
        agent_registry={"schema_version": 1, "agents": []},
        action="status",
    )
    persisted = json.loads(contents.review_state_json)
    compact = json.loads(contents.compact_json)
    full = json.loads(contents.full_json)
    actions = json.loads(contents.actions_json)
    commit_pipeline = json.loads(contents.commit_pipeline_json)

    for payload in (persisted, compact, full, actions, commit_pipeline):
        assert payload["snapshot_id"] == "snap-frozen"
        assert payload["zref"] == "zref_frozen"
    assert full["review_state"]["coordination"]["ownership_status"] == "scope_known"
    assert compact["recovery_assessment"]["diagnosis"]["status"] == "needs_review"
    assert compact["recovery_assessment"]["decision"]["action_id"] == "repair_surface"
    assert compact["doctor"]["snapshot_id"] == "snap-frozen"
    assert compact["doctor"]["zref"] == "zref_frozen"


def test_read_only_event_bundle_reduces_event_log_without_artifact_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    projections_root = Path(artifact_paths.projections_root)
    projections_root.mkdir(parents=True, exist_ok=True)
    projected_state = {
        "schema_version": 1,
        "contract_id": "ReviewState",
        "command": "review-channel",
        "queue": {"pending_total": 99},
        "packets": [],
    }
    (projections_root / "review_state.json").write_text(
        json.dumps(projected_state),
        encoding="utf-8",
    )
    event_log_path = Path(artifact_paths.event_log_path)
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    event_log_path.write_text(
        json.dumps(
            {
                "event_id": "rev_evt_0001",
                "packet_id": "rev_pkt_event_only",
                "event_type": "packet_posted",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "finding",
                "summary": "event log row",
                "body": "event body",
                "status": "pending",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
    monkeypatch.setenv("DEVCTL_NO_ARTIFACT_WRITES", "1")

    bundle = load_or_refresh_event_bundle(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )

    assert bundle.review_state["queue"]["pending_total"] == 1
    assert bundle.events[0]["packet_id"] == "rev_pkt_event_only"


def test_projected_event_bundle_can_load_raw_events_for_post_ids(
    tmp_path: Path,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    projections_root = Path(artifact_paths.projections_root)
    projections_root.mkdir(parents=True, exist_ok=True)
    (projections_root / "review_state.json").write_text(
        json.dumps({"schema_version": 1, "packets": []}),
        encoding="utf-8",
    )
    event_log_path = Path(artifact_paths.event_log_path)
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    event_log_path.write_text(
        json.dumps({"event_id": "rev_evt_0001", "event_type": "packet_posted"})
        + "\n",
        encoding="utf-8",
    )

    bundle = load_projected_event_bundle(
        artifact_paths=artifact_paths,
        include_events=True,
    )

    assert bundle is not None
    assert [event["event_id"] for event in bundle.events] == ["rev_evt_0001"]
