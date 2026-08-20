# ADR-0005: Separate data mutations, lifecycle mutations, and delivery faults

- Status: Accepted
- Date: 2026-08-19

## Context

IAM failures can come from different layers. A malformed email is different from a duplicate lifecycle event. A timeout is different from a target rejecting a username.

If all of these are called an edge case without a category, reports become difficult to understand.

## Decision

The tool will use three mutation categories.

### Data mutations

These change identity data:

~~~text
unicode_nfc
unicode_nfd
case_collision
duplicate_username
duplicate_email
invalid_email
missing_required_field
overlong_value
forbidden_character
null_byte
non_breaking_space
~~~

Security-shaped payloads such as less-than script greater-than or SQL-like strings may be used for authorized robustness tests. They must be non-destructive and clearly labelled as input validation tests.

### Lifecycle mutations

These change the sequence of operations:

~~~text
disable_before_create
repeated_disable
delete_before_create
recreate_after_delete
update_after_delete
duplicate_create
~~~

### Delivery faults

These change how events reach the target:

~~~text
duplicate_event
out_of_order
delayed_event
dropped_event
retry_after_timeout
rate_limit_response
partial_failure
concurrent_patch
~~~

## Scenario timing

Mutations can be applied at a specific step or logical time:

~~~yaml
steps:
  - at: 0s
    event: CREATE
    mutations: [valid_create]
  - at: 5s
    event: UPDATE
    mutations: [invalid_email]
  - at: 6s
    delivery: [duplicate_event, delayed_event]
~~~

## Consequences

Positive consequences:

- Reports identify the layer that caused a failure.
- A valid user can become invalid later in its lifecycle.
- Network and lifecycle problems can be tested independently.
- New mutators can be added without changing the state machine.

Costs:

- Scenarios need more detailed metadata.
- The runner must preserve mutation provenance.
- Some failures need target-specific expectations.
