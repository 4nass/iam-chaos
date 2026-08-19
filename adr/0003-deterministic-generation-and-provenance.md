# ADR-0003: Make generation deterministic and traceable

- Status: Accepted
- Date: 2026-08-19

## Context

The current generator uses shared mutable state and random values from several processes. This makes it difficult to reproduce a failing test.

An IAM test tool must produce the same identity, event, and schedule when it receives the same scenario, seed, and version.

## Decision

Generation will be based on pure inputs:

~~~text
identity = f(scenario_id, scenario_version, seed, identity_index)
event = f(scenario_id, scenario_version, seed, identity_id, sequence)
~~~

The generator must not depend on process order, global random state, or a shared mutable uniqueness dictionary.

## Deterministic identifiers

Identity IDs will use a deterministic ULID when time ordering is useful:

- timestamp: fixed epoch plus logical time;
- entropy: deterministic bytes derived from scenario, seed, and index.

Event IDs will be deterministic and derived from the scenario, identity ID, and event sequence.

If a target does not need time-sortable IDs, UUIDv5 is an acceptable simpler implementation.

The identifier algorithm must be documented and covered by cross-process tests.

## Seed hash

The raw seed is not required in every report. The engine will compute:

~~~text
seed_hash = SHA-256(scenario_id + scenario_version + seed)
~~~

The report will include the hash and the identity index. This provides provenance without exposing the complete scenario input in every record.

## Parallel execution

Identity generation may run in parallel because each identity is a pure function of its inputs.

HTTP execution may also run in parallel, but events for the same identity must remain ordered. The scheduler will use one ordered queue per identity or aggregate.

## Consequences

Positive consequences:

- A failing identity can be regenerated exactly.
- Parallel generation does not change the result.
- Test artifacts can be compared between runs.
- Dataset provenance is visible in reports.

Costs:

- The implementation must control all sources of randomness.
- Faker instances must be seeded independently.
- The logical clock and event scheduler become part of the deterministic input.
