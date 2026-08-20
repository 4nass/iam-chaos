# ADR-0008: Produce machine-readable reports and CI-friendly results

- Status: Accepted
- Date: 2026-08-19

## Context

IAM recipe tests must be useful to developers, testers, and CI/CD pipelines. A console log alone is not enough to explain which identity, event, mutation, or target response caused a failure.

## Decision

Every run will produce a report containing:

- run ID;
- scenario ID and version;
- target and target version;
- seed hash;
- identity and event IDs;
- logical and wall-clock timing;
- applied mutations;
- expected outcome;
- observed outcome;
- HTTP status and provider error code;
- retry count and latency;
- expected state versus actual state;
- cleanup status.

The first reporting formats will be:

~~~text
JSON       detailed machine-readable report
JUnit XML  CI test result integration
HTML       human-readable investigation report
~~~

## Exit codes

The CLI will use stable exit codes:

~~~text
0  all assertions passed
1  one or more assertions failed
2  invalid scenario or configuration
3  target unavailable or execution error
4  cleanup failed
~~~

## Redaction

Reports must redact:

- passwords;
- access tokens;
- client secrets;
- authorization headers;
- private connection details.

The report may keep safe hashes and correlation IDs.

## Consequences

Positive consequences:

- The tool can run in CI/CD.
- Failures are reproducible and searchable.
- JUnit consumers can display IAM test results.
- HTML reports help manual test investigation.

Costs:

- Reporting becomes a first-class module.
- The report schema must be versioned.
- Redaction must be tested carefully.
