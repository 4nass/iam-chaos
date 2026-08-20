# ADR-0001: Reposition the project as an IAM chaos engineering and acceptance test suite

- Status: Accepted
- Date: 2026-08-19

## Context

IAMChaos started as a tool that generated fake identities and exported them to files.

Many tools can generate names, addresses, and emails. This is not enough for IAM testing. IAM failures often happen during synchronization, lifecycle changes, retries, duplicate events, Unicode normalization, and partial failures.

The project needs a clearer purpose and a stronger testing model.

## Decision

IAMChaos will become a specialized test tool for IAM and CIAM architectures.

The tool will generate:

- valid identity datasets;
- invalid and boundary-case identities;
- lifecycle events;
- delivery faults such as retries, delays, duplicates, and out-of-order events;
- expected outcomes for each target IAM.

The primary use case is acceptance testing and resilience testing of identity synchronization flows.

The product is not a production identity provider, an attack tool, or a general-purpose synthetic data platform.

## Main use cases

The tool must support:

1. Testing an initial user import.
2. Testing create, update, disable, restore, and delete flows.
3. Testing duplicate and out-of-order events.
4. Testing Unicode, normalization, length, and uniqueness rules.
5. Testing target behavior after timeout, retry, rate limit, or partial failure.
6. Comparing expected state with the state stored by the target IAM.

## Consequences

Positive consequences:

- The project has a clear IAM-specific purpose.
- Tests become reproducible and scenario-based.
- The same scenario can be executed against different IAM products.
- The project can produce CI/CD test reports.

Costs:

- The current generator must be refactored around scenarios and state transitions.
- Target-specific behavior must be described explicitly.
- The project needs a state machine, an event model, and an assertion engine.
