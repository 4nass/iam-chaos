"""Offline deterministic scenario engine."""

import copy
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

from .clock import VirtualClock, format_offset
from .generator import generate_identities, seed_hash
from .lifecycle import IdentityStateMachine
from .model import CanonicalIdentity
from .mutators import DELIVERY_MUTATIONS, MutationContext, apply_payload_mutation
from .reporting import OfflineReport
from .spec import MutationSpec, ScenarioSpec, load_scenario


class ScenarioEngine:
    """Generate identities and execute lifecycle scenarios offline."""

    def __init__(self, seed: Optional[Union[int, str]] = None) -> None:
        self.seed = seed

    @staticmethod
    def _event_id(
        seed: Union[int, str],
        step_position: int,
        identity_index: int,
        occurrence: str = "primary",
    ) -> str:
        value = "iam-chaos:{}:event:{}:{}:{}".format(
            seed, step_position, identity_index, occurrence
        )
        return "evt_{}".format(uuid.uuid5(uuid.NAMESPACE_URL, value))

    @staticmethod
    def _scenario_dict(spec: ScenarioSpec, seed: Any) -> Dict[str, Any]:
        return {
            "version": spec.version,
            "name": spec.name,
            "seed": seed,
            "identity_count": spec.identities.count,
            "step_count": len(spec.steps),
        }

    @staticmethod
    def _mutation_names(mutations: List[MutationSpec]) -> List[str]:
        return [mutation.type for mutation in mutations]

    def _make_event(
        self,
        seed: Union[int, str],
        step_position: int,
        step_id: str,
        action: str,
        time_seconds: float,
        identity: CanonicalIdentity,
        payload: Dict[str, Any],
        mutations: List[MutationSpec],
    ) -> Dict[str, Any]:
        payload["metadata"]["scenario_step"] = step_id
        return {
            "event_id": self._event_id(
                seed, step_position, identity.metadata.index
            ),
            "identity_id": identity.id,
            "identity_index": identity.metadata.index,
            "action": action,
            "time_seconds": time_seconds,
            "time": format_offset(time_seconds),
            "payload": payload,
            "mutations": self._mutation_names(mutations),
            "delivery_faults": [
                mutation.type
                for mutation in mutations
                if mutation.type in DELIVERY_MUTATIONS
            ],
            "logical_sequence": 0,
        }

    @staticmethod
    def _replay_expected(expected: Dict[str, Any]) -> Dict[str, Any]:
        if expected.get("accepted"):
            return {
                "accepted": True,
                "outcome": "idempotent",
                "state_before": expected.get("state_after"),
                "state_after": expected.get("state_after"),
                "reason": "event_replay",
            }
        return copy.deepcopy(expected)

    @staticmethod
    def _reorder_out_of_order(events: List[Dict[str, Any]]) -> None:
        marked = [
            event
            for event in events
            if "out_of_order" in event.get("mutations", [])
            and not event.get("replayed_from")
        ]
        for event in sorted(marked, key=lambda item: item["logical_sequence"]):
            current_position = next(
                index
                for index, item in enumerate(events)
                if item["event_id"] == event["event_id"]
            )
            candidates = [
                (index, item)
                for index, item in enumerate(events)
                if item.get("identity_id") == event.get("identity_id")
                and item.get("logical_sequence", -1)
                < event["logical_sequence"]
                and not item.get("replayed_from")
            ]
            if not candidates:
                continue
            previous_position = max(
                candidates, key=lambda item: item[1]["logical_sequence"]
            )[0]
            if previous_position < current_position:
                events[previous_position], events[current_position] = (
                    events[current_position],
                    events[previous_position],
                )

    def run(
        self,
        scenario: Union[str, Path, Mapping[str, Any], ScenarioSpec],
    ) -> OfflineReport:
        spec = scenario if isinstance(scenario, ScenarioSpec) else load_scenario(scenario)
        effective_seed = self.seed if self.seed is not None else spec.seed
        identities = generate_identities(
            seed=effective_seed,
            count=spec.identities.count,
            tenant_id=spec.identities.tenant_id,
            groups=spec.identities.groups,
            roles=spec.identities.roles,
            credential_profile=spec.identities.credential_profile,
            scenario_origin=spec.name,
        )
        base_payloads = {
            identity.metadata.index: identity.to_dict() for identity in identities
        }

        logical_machine = IdentityStateMachine()
        logical_events: List[Dict[str, Any]] = []
        clock = VirtualClock()
        logical_sequence = 0

        for step_position, step in enumerate(spec.steps):
            clock.advance_to(step.at_seconds)
            for index in step.target_indices(spec.identities.count):
                identity = identities[index]
                payload = copy.deepcopy(base_payloads[index])
                context = MutationContext(index, base_payloads)
                for mutation in step.mutations:
                    if mutation.type in DELIVERY_MUTATIONS:
                        continue
                    payload = apply_payload_mutation(
                        payload,
                        mutation.type,
                        mutation.params,
                        context,
                    )
                event = self._make_event(
                    seed=effective_seed,
                    step_position=step_position,
                    step_id=step.id,
                    action=step.action,
                    time_seconds=clock.current_seconds,
                    identity=identity,
                    payload=payload,
                    mutations=step.mutations,
                )
                logical_sequence += 1
                event["logical_sequence"] = logical_sequence
                event["expected"] = logical_machine.apply(event).to_dict()
                logical_events.append(event)

        delivery_events: List[Dict[str, Any]] = []
        for event in logical_events:
            delivery_events.append(event)
            if "event_replay" in event.get("mutations", []):
                replay = copy.deepcopy(event)
                replay["event_id"] = self._event_id(
                    effective_seed,
                    event["logical_sequence"],
                    event["identity_index"],
                    "replay",
                )
                replay["replayed_from"] = event["event_id"]
                replay["delivery_faults"] = ["event_replay"]
                replay["expected"] = self._replay_expected(event["expected"])
                delivery_events.append(replay)

        self._reorder_out_of_order(delivery_events)

        actual_machine = IdentityStateMachine()
        assertions: List[Dict[str, Any]] = []
        for delivery_sequence, event in enumerate(delivery_events, start=1):
            event["delivery_sequence"] = delivery_sequence
            actual = actual_machine.apply(event).to_dict()
            event["actual"] = actual
            expected = event["expected"]
            passed = (
                expected.get("outcome") == actual.get("outcome")
                and expected.get("state_after") == actual.get("state_after")
            )
            assertions.append(
                {
                    "event_id": event["event_id"],
                    "identity_id": event["identity_id"],
                    "passed": passed,
                    "expected_outcome": expected.get("outcome"),
                    "actual_outcome": actual.get("outcome"),
                    "expected_state_after": expected.get("state_after"),
                    "actual_state_after": actual.get("state_after"),
                    "reason": actual.get("reason", ""),
                }
            )

        passed_count = sum(1 for item in assertions if item["passed"])
        failed_count = len(assertions) - passed_count
        return OfflineReport(
            schema_version="iam-chaos.report/v1",
            scenario=self._scenario_dict(spec, effective_seed),
            seed=effective_seed,
            seed_hash=seed_hash(effective_seed),
            payloads=[
                base_payloads[index] for index in sorted(base_payloads)
            ],
            events=delivery_events,
            assertions=assertions,
            summary={
                "total_events": len(assertions),
                "passed": passed_count,
                "failed": failed_count,
                "replayed_events": sum(
                    1 for event in delivery_events if event.get("replayed_from")
                ),
                "out_of_order_events": sum(
                    1
                    for event in delivery_events
                    if "out_of_order" in event.get("mutations", [])
                ),
            },
        )
