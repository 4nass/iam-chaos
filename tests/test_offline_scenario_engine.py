"""Tests for the deterministic offline scenario engine."""

import json
import unicodedata

import pytest

from iam_chaos.engine import ScenarioEngine
from iam_chaos.mutators import UnicodeMutator
from iam_chaos.reporting import write_artifacts
from iam_chaos.spec import ScenarioSpecError, load_scenario


def base_scenario(seed=20260819):
    return {
        "version": 1,
        "name": "test-scenario",
        "seed": seed,
        "identities": {"count": 2, "tenant_id": "tenant-test"},
        "steps": [{"id": "create", "at": "0s", "action": "create"}],
    }


def test_public_library_import_and_determinism():
    first = ScenarioEngine().run(base_scenario())
    second = ScenarioEngine().run(base_scenario())

    assert isinstance(UnicodeMutator(), UnicodeMutator)
    assert first.to_dict() == second.to_dict()
    assert first.payloads[0]["metadata"]["index"] == 0
    assert first.payloads[0]["metadata"]["seed_hash"] == second.seed_hash


def test_versioned_yaml_and_virtual_time_lifecycle():
    yaml_text = """
version: 1
name: lifecycle
seed: 20260819
identities:
  count: 1
steps:
  - id: create
    at: 0s
    action: create
  - id: disable
    at: 5s
    action: disable
  - id: enable
    at: 10s
    action: enable
  - id: delete
    at: 15s
    action: delete
"""
    spec = load_scenario(yaml_text)
    report = ScenarioEngine().run(spec)

    assert [event["time"] for event in report.events] == [
        "T+0s",
        "T+5s",
        "T+10s",
        "T+15s",
    ]
    assert [event["actual"]["state_after"] for event in report.events] == [
        "ACTIVE",
        "DISABLED",
        "ACTIVE",
        "DELETED",
    ]
    assert report.summary["failed"] == 0


def test_mutators_cover_unicode_collision_invalid_missing_and_replay():
    scenario = base_scenario(seed=4)
    scenario["steps"] = [
        {"id": "create", "at": "0s", "action": "create"},
        {
            "id": "unicode",
            "at": "5s",
            "action": "update",
            "identities": [0],
            "mutations": [{"type": "unicode_nfc_nfd", "form": "nfd"}],
        },
        {
            "id": "collision",
            "at": "10s",
            "action": "update",
            "identities": [1],
            "mutations": [
                {"type": "username_collision", "target_index": 0}
            ],
        },
        {
            "id": "invalid-email",
            "at": "15s",
            "action": "update",
            "identities": [0],
            "mutations": [
                {"type": "invalid_email", "value": "not-an-email"}
            ],
        },
        {
            "id": "missing-username",
            "at": "20s",
            "action": "update",
            "identities": [0],
            "mutations": [
                {
                    "type": "missing_required_field",
                    "field": "username",
                }
            ],
        },
        {
            "id": "replay-disable",
            "at": "25s",
            "action": "disable",
            "identities": [0],
            "mutations": [{"type": "event_replay"}],
        },
    ]

    report = ScenarioEngine().run(scenario)
    outcomes = {event["actual"]["outcome"] for event in report.events}
    unicode_event = next(
        event for event in report.events if event["action"] == "update"
        and event["identity_index"] == 0
        and event["time_seconds"] == 5.0
    )

    assert report.summary["failed"] == 0
    assert report.summary["replayed_events"] == 1
    assert "username_conflict" in outcomes
    assert "invalid_payload" in outcomes
    assert "idempotent" in outcomes
    assert unicodedata.is_normalized(
        "NFD", unicode_event["payload"]["username"]
    )
    assert "unicode_nfc_nfd_nfd" in unicode_event["payload"]["metadata"][
        "applied_mutations"
    ]


def test_out_of_order_event_is_visible_as_expected_actual_mismatch():
    scenario = {
        "version": 1,
        "name": "out-of-order",
        "seed": 1,
        "identities": {"count": 1},
        "steps": [
            {"id": "create", "at": 0, "action": "create"},
            {
                "id": "update",
                "at": "5s",
                "action": "update",
                "mutations": [{"type": "out_of_order"}],
            },
        ],
    }

    report = ScenarioEngine().run(scenario)

    assert report.summary["failed"] == 1
    assert report.events[0]["action"] == "update"
    assert report.events[0]["expected"]["outcome"] == "accepted"
    assert report.events[0]["actual"]["outcome"] == "identity_not_found"
    assert report.assertions[0]["passed"] is False


def test_json_artifacts_are_written(tmp_path):
    report = ScenarioEngine().run(base_scenario())
    paths = write_artifacts(report, tmp_path / "artifacts")

    for path in paths.values():
        assert path.exists()

    assert json.loads(paths["payloads"].read_text()) == report.payloads
    assert json.loads(paths["events"].read_text()) == report.events
    assert json.loads(paths["report"].read_text()) == report.to_dict()


def test_invalid_scenario_version_is_rejected():
    scenario = base_scenario()
    scenario["version"] = 2

    with pytest.raises(ScenarioSpecError):
        ScenarioEngine().run(scenario)
