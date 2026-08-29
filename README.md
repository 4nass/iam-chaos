# IAMChaos

IAMChaos is a Python tool for IAM and CIAM chaos engineering and acceptance testing. It generates deterministic identities, lifecycle events, edge cases, and delivery faults to test synchronization resilience across identity platforms.

## Features

- Generates unique usernames based on name and surname combinations.
- Optionally uses the `faker` library to generate random names if no input file is provided.
- Outputs identities in both CSV and Excel formats.
- Ensures there are no duplicate usernames and emails.
- Command-line arguments allow flexible input and output options.
- Runs versioned YAML lifecycle scenarios offline.
- Generates deterministic identities from seed and index.
- Exports payloads, events, and expected/actual assertions as JSON.

## Prerequisites

Before running the project, ensure you have the following installed:

- Python 3.8+
- `PyYAML` library (for loading versioned offline scenarios)
- `pandas` library (for CSV/Excel/JSON/Parquet export)
- `argparse` library (for parsing command-line arguments)
- `faker` library (for generating random names if no input file is provided)
- `pytest` library (for testing)
- `unidecode` library (for reducing Unicode to an ASCII representation)
- `aiofiles` library (for asynchronous file operations)

You can install these libraries manually via `pip`:

```bash
pip install pandas argparse unidecode faker aiofiles
```

Or by using `requirements.txt` file:

```bash
pip install --prefix=/install -r ./requirements.txt
```

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

- number_of_identities: The number of identities to generate (required).
- --names-file: Optional file containing the list of names and surnames (if not provided, random names will be generated using the faker library).
- --surnames-file: Optional file containing the list of names and surnames (if not provided, random names will be generated using the faker library).
- --output-file: Path to save the output file without extension (default is output/identities). The appropriate extension (.csv or .xlsx) will be added based on the --output-format.
- --output-format: Output format, either csv, excel, or both (default is both).
- --workers: Allows users to specify the number of parallel workers (CPU cores) to use. Defaults to 4.

### Input File Format

The input file (surnames.txt) should contain surnames, one per line, like this:

```bash
John
Jane
```

The input file (names.txt) should contain names, one per line, like this:

```bash
Doe
Smith
```

The program will randomly combine these names and surnames to create identities.

## Output

The generated output will include the following columns:

```bash
username
password
email
isEmailVerified
name
surname
middlename
honorific
language
isActive
gender
communicationChannel
addressType
streetNumber
complementStreetNumber
streetType
streetName
complementLocation
complementIdentification
complementAddress
postalCode
locality
region
country
```

Each generated identity includes detailed address information, broken down into multiple columns:

- **Type**: Either "work" or "home".
- **StreetNumber**: The building or street number.
- **ComplementStreetNumber**: Additional street number information like "bis" or "ter" (optional).
- **StreetType**: Type of street (e.g., avenue, boulevard).
- **StreetName**: The name of the street.
- **Locality**: The city or town.
- **ComplementLocation**: Additional location information (optional).
- **ComplementIdentification**: Identification complements (optional).
- **ComplementAddress**: Additional address details such as apartment or suite number.
- **Region**: The region in France (e.g., Île-de-France).
- **Country**: Always "France".
- **PostalCode**: The postal code of the address.

## License

This project is licensed under the Apache License, Version 2.0.
