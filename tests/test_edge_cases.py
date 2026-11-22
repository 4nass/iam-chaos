import asyncio
import csv

import pytest

from cli.generate_identities import main
from core.identity_generator import generate_identities_parallel


def test_zero_workers_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        asyncio.run(
            generate_identities_parallel(
                10, output_file=tmp_path / "identities", output_format="csv", workers=0
            )
        )

    assert not list(tmp_path.iterdir())


def test_cli_rejects_invalid_json_column_mapping(tmp_path, caplog):
    with pytest.raises(SystemExit) as exc:
        main([
            "10",
            "--output-file", str(tmp_path / "identities"),
            "--column-mapping", "{'username': 'User Name'}",
        ])

    assert exc.value.code == 1
    assert "Invalid JSON format for column mapping" in caplog.text
    assert not list(tmp_path.iterdir())


def test_generator_exports_names_from_default_provider(tmp_path):
    output_file = tmp_path / "identities"
    asyncio.run(
        generate_identities_parallel(
            3, output_file=output_file, output_format="all", workers=1
        )
    )

    with output_file.with_suffix(".csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 3
    assert all(row["name"] and row["surname"] for row in rows)
    assert {path.suffix for path in tmp_path.iterdir()} == {
        ".csv", ".xlsx", ".json", ".parquet"
    }
