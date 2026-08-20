# Architecture Decision Records

This directory records the main architecture decisions for IAMChaos.

The project is moving from a generic fake identity generator to an IAM chaos engineering and acceptance test suite. These records explain what we build, why we build it, and what is intentionally out of scope.

## Decision index

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-iam-chaos-engineering-test-suite.md) | Reposition the product as an IAM chaos engineering and acceptance test suite | Accepted |
| [0002](0002-canonical-identity-model.md) | Use a provider-neutral canonical identity model | Accepted |
| [0003](0003-deterministic-generation-and-provenance.md) | Make generation deterministic and traceable | Accepted |
| [0004](0004-state-machine-and-virtual-time.md) | Model lifecycle as a state machine with a virtual clock | Accepted |
| [0005](0005-mutations-and-fault-injection.md) | Separate data mutations, lifecycle mutations, and delivery faults | Accepted |
| [0006](0006-target-capabilities-and-expectation-evaluation.md) | Evaluate target behavior through capabilities and semantic outcomes | Accepted |
| [0007](0007-offline-first-target-adapters.md) | Use offline-first target adapters and safe execution | Accepted |
| [0008](0008-reporting-and-ci-integration.md) | Produce machine-readable reports and CI-friendly results | Accepted |
| [0009](0009-phased-implementation-roadmap.md) | Deliver the system in four implementation milestones | Accepted |
| [0010](0010-public-python-package-boundary.md) | Separate CLI internals from the future public Python library | Accepted |

## ADR format

Each ADR contains:

- Status: the current decision status.
- Context: the problem that required a decision.
- Decision: the choice made by the project.
- Consequences: the benefits and costs of the choice.

These ADRs describe architecture and product decisions. Detailed implementation tasks belong in issues or pull requests.
