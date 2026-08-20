# ADR-0006: Evaluate target behavior through capabilities and semantic outcomes

- Status: Accepted
- Date: 2026-08-19

## Context

Different IAM products can return different HTTP status codes for the same semantic result. A duplicate create may return 409, 412, or an idempotent 200. A delete of a missing user may return 404 or 204.

The test engine must not hard-code one HTTP response for every target.

## Decision

Each target will provide versioned capabilities.

Capabilities describe:

- field constraints;
- Unicode and case rules;
- supported operations;
- lifecycle transition rules;
- accepted duplicate and replay outcomes;
- concurrency behavior;
- retryable errors;
- postcondition checks.

The evaluator will compare semantic outcomes, not only status codes.

## Evaluation pipeline

~~~text
HTTP response
    |
Response classifier
    |
Observed semantic outcome
    |
Expectation evaluator
    |
Post-state comparison
    |
Assertion result
~~~

Possible semantic outcomes:

~~~text
accepted
rejected
conflict
idempotent
not_found
retryable_error
unknown
~~~

## Post-state validation

An HTTP response is not enough. The evaluator may need to read the target again and check:

- the user exists or does not exist;
- only one user was created;
- the expected fields were stored;
- the target did not silently truncate or normalize data incorrectly;
- group and role relationships are correct.

## Example

For duplicate_create, a target profile may accept:

~~~text
conflict
idempotent
~~~

The test passes only if the observed outcome is allowed and the final target state matches the selected policy.

## Consequences

Positive consequences:

- The same test scenario can run against different IAM products.
- Provider-specific behavior is explicit and versioned.
- Reports can distinguish transport errors from semantic errors.
- State verification catches false positives.

Costs:

- Each target needs a capability profile.
- Adapters need read-back operations for strong assertions.
- Some SaaS behavior cannot be fully deterministic.
