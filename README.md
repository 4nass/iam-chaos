# IAMChaos

IAMChaos is a Python tool for IAM and CIAM chaos engineering and acceptance testing. It generates deterministic identities, lifecycle events, edge cases, and delivery faults to test synchronization resilience across identity platforms.

## Features

- Generate synthetic IAM identities deterministically from a seed and an index.
- Run versioned YAML scenarios with identity lifecycle events and virtual time.
- Exercise Unicode, duplicate usernames, invalid values, and delivery order.
- Export payloads, events, and expected/actual assertions as JSON.

## Installation

From the repository root, install IAMChaos in a Python virtual environment:

```bash
python -m pip install .
```

## Running the tests

Use Python 3.11, the version used by CI. From the repository root on Linux or
WSL, create a fresh virtual environment and install the locked test dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest -q
```

If you use uv to manage Python, create the environment with
`uv venv --python 3.11 --seed .venv`.

The suite covers the offline scenario engine and the legacy generator and file
conversions. It runs without credentials or external IAM services.

Update the lockfile after editing `requirements-test.in`:

```bash
uv pip compile --universal --python-version 3.11 requirements-test.in -o requirements-test.txt
```

GitHub Actions runs the full suite on pull requests to `main` and on pushes to
`main`. A separate job installs the package into a clean environment and
checks the `iam-chaos` command and the `iam_chaos` Python import from outside
the checkout.

## Usage

Run a deterministic, versioned YAML scenario offline:

```bash
iam-chaos run examples/scenarios/iam-lifecycle-edge-cases.yaml --output-dir output/iam-chaos --allow-failures
```

The command writes `payloads.json`, `events.json`, and `report.json`. A
failed expected/actual assertion returns exit code 1; use `--allow-failures`
for exploratory chaos runs.

## Python library API

The main user interface is the CLI. The project also exposes a PyPI library
API for Pytest-based IAM acceptance tests under the public import namespace
`iam_chaos`:

```python
from iam_chaos.engine import ScenarioEngine
from iam_chaos.mutators import UnicodeMutator
```

The public API is intentionally small at this stage. The engine and its
mutators are implemented by the offline scenario runner.

## Legacy identity exporter

The repository also includes a standalone generator for French synthetic
identities and a converter for CSV, JSON, Excel, and Parquet. Run these commands
from the repository root:

```bash
python -m pip install -r requirements.txt
mkdir -p output
python -m cli.generate_identities 10 --output-file output/identities --output-format csv
python -m cli.convert_files csv-to-excel output/identities.csv output/identities.xlsx
```

Use `--help` for available formats, column mapping, and worker options.

## License

This project is licensed under the Apache License, Version 2.0.
