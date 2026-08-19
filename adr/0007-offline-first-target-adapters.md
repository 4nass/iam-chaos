# ADR-0007: Use offline-first target adapters and safe execution

- Status: Accepted
- Date: 2026-08-19

## Context

The project must be useful before it has access to real IAM accounts. Directly creating and deleting users in a cloud tenant is risky and makes local development difficult.

The current adapters are incomplete and mix payload formatting with execution.

## Decision

Target adapters will have two separate responsibilities:

1. translate the canonical model into target payloads;
2. execute operations against a target when explicitly enabled.

The first implementation will support offline exporters for:

- SCIM 2.0 JSON;
- Keycloak import JSON.

The first live target will be a local Keycloak instance. A generic SCIM HTTP driver will follow.

Cloud connectors for Microsoft Entra ID, Okta, and AWS Cognito will be added after the offline and local flows are stable.

## Adapter contract

An adapter should expose operations such as:

~~~text
capabilities()
format_identity(identity)
format_event(event)
execute(event)
read_state(identity_id)
cleanup(run_id)
~~~

The execution layer must support:

- dry-run mode;
- explicit target selection;
- retry policy;
- timeout policy;
- request correlation IDs;
- cleanup after a run.

## Safety rules

- No live execution by default.
- No credentials in source-controlled configuration.
- No real email delivery by default.
- No destructive scenario against an unapproved target.
- Secrets must never be written to reports or logs.
- Every run must have a run ID for cleanup and traceability.

## Consequences

Positive consequences:

- Offline tests run without IAM credentials.
- Payload mapping can be tested independently from network behavior.
- Local Keycloak provides a realistic first integration target.
- Cloud connectors can be added without changing the core engine.

Costs:

- The adapter interface is more explicit.
- Some tests need both an exporter and an executor.
- Cleanup and secret management require extra implementation work.
