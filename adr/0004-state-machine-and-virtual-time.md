# ADR-0004: Model identity lifecycle with a state machine and a virtual clock

- Status: Accepted
- Date: 2026-08-19

## Context

Identity mutations can happen at any point in the lifecycle. A valid user can later receive an invalid email update. A delete event can arrive before a create event. A disable event can be delivered twice.

A simple linear pipeline cannot express these cases well.

## Decision

The engine will use an identity state machine.

The state machine owns the expected state. It receives commands and produces lifecycle events.

Example states:

~~~text
PENDING
ACTIVE
DISABLED
DELETED
QUARANTINED
~~~

Example events:

~~~text
CREATE
UPDATE
DISABLE
RESTORE
DELETE
~~~

An invalid event is still recorded as a test event. It must not silently change the expected state. This lets the test compare the target state with the correct expected state after an invalid operation.

## Event envelope

Every event contains:

~~~text
event_id
aggregate_id
sequence
type
payload
occurred_at
logical_time_ms
delivery_plan
applied_mutations[]
~~~

## Virtual time

The engine will use a virtual clock for offline tests and controlled test environments.

The scenario can express:

~~~text
T+0 ms
T+5 seconds
T+15 minutes
~~~

The virtual clock is required for testing token expiration, retry windows, session locks, delayed events, and inactivity policies.

For real SaaS targets, the tool will record the planned logical time and the actual wall-clock time. Real execution is not assumed to be perfectly deterministic.

## Consequences

Positive consequences:

- Lifecycle and mutation timing are explicit.
- Out-of-order and replay tests are first-class scenarios.
- Expected state is independent from the target IAM response.
- Expiration and retry windows can be tested offline.

Costs:

- The engine needs a formal transition model.
- Invalid transitions need explicit test semantics.
- Real-world execution timing must be reported separately from logical timing.
