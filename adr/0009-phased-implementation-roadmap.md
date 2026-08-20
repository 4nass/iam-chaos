# ADR-0009: Deliver the system in four implementation milestones

- Status: Accepted
- Date: 2026-08-19

## Context

The current repository is a prototype. A large rewrite would create risk if generation, scenario execution, and live integrations were built at the same time.

The project needs an incremental path that creates useful value early.

## Decision

The implementation will follow four milestones.

## Milestone 1: Core engine and offline reports

- Pydantic canonical identity model;
- deterministic seed and identity IDs;
- provenance metadata;
- virtual clock;
- identity state machine;
- first five mutators;
- YAML scenario loader;
- offline SCIM JSON exporter;
- offline Keycloak JSON exporter;
- JSON and JUnit reports.

## Milestone 2: Dynamic lifecycle and event stream

- create, update, disable, restore, and delete events;
- event dependencies and sequence numbers;
- duplicate and out-of-order delivery;
- replay and delay support;
- expected-state assertions;
- generic asynchronous SCIM driver.

## Milestone 3: Local target execution

- Keycloak Admin REST adapter;
- capability profile for the selected Keycloak version;
- read-back state comparison;
- retry and timeout policies;
- HTML report;
- CI exit codes and command-line integration.

## Milestone 4: Cloud connectors

- Microsoft Graph / Entra ID;
- Okta Management API;
- AWS Cognito;
- rate-limit handling;
- cleanup and run isolation;
- provider-specific capability profiles.

## Consequences

Positive consequences:

- The first milestone is useful without external credentials.
- Each milestone can be validated independently.
- Local Keycloak and SCIM provide realistic integration coverage.
- Cloud-specific complexity is delayed until the core model is stable.

Costs:

- Some features will initially be offline-only.
- The canonical model and report schema must remain backward compatible.
- Cloud connectors will require separate credentials, cleanup, and integration tests.
