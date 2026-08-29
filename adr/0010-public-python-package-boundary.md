# ADR-0010: Separate the CLI internals from the future public Python library

- Status: Accepted
- Date: 2026-08-20
- Decision owners: IAMChaos maintainers

## Context

IAMChaos has two planned ways to be used:

1. The main interface is a command-line tool driven by YAML scenario files.
2. Teams may later import IAMChaos as a test library in their Pytest suites.

The current repository still contains the first-generation identity generator
and CLI. Its folders are implementation details and are not a stable Python
API. Moving them under the future public package name too early would make an
unfinished API look supported and would couple the CLI layout to the library
contract.

## Decision

We reserve the following public names:

| Concern | Name |
| --- | --- |
| GitHub repository | `iam-chaos` |
| PyPI distribution | `iam-chaos` |
| CLI command | `iam-chaos` |
| Future Python import namespace | `iam_chaos` |
| Product and README title | `IAMChaos` |

The current CLI keeps its internal entry point and folders. Those internals
must not be treated as public imports. The future library will expose its API
from `iam_chaos`, for example:

```python
from iam_chaos.engine import ScenarioEngine
from iam_chaos.mutators import UnicodeMutator
```

This ADR defines the namespace and the boundary. The current scenario-engine
implementation lives in `iam_chaos`; the legacy CLI folders are not moved
under that namespace.

## Consequences

### Positive

- Users get one stable CLI name: `iam-chaos`.
- The future PyPI library has a clear import contract: `iam_chaos`.
- CLI refactoring can continue without accidentally promising a public API.
- The public API can be designed around the scenario engine rather than the
  legacy identity generator modules.

### Trade-off

- The library API is intentionally small and experimental at this stage.
- The CLI and the library have an explicit integration boundary.

## Rejected alternatives

### Move the current CLI under `iam_chaos`

Rejected for now. This would expose an unfinished package structure and make
internal CLI modules appear to be supported library APIs.

### Use `iamchaos` as the Python import name

Rejected. The public import namespace is intentionally the underscore form
`iam_chaos`, matching normal Python package naming while the distribution and
CLI keep the hyphenated name `iam-chaos`.
