import asyncio
import csv
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook, load_workbook

from utils.file_converter import AsyncFileConverter


IDENTITIES = [
    {"name": "Élodie Renard", "email": "elodie@example.com"},
    {"name": "Jane Doe", "email": "jane@example.com"},
]
EXTENSIONS = {"csv": ".csv", "excel": ".xlsx", "json": ".json", "parquet": ".parquet"}


def write_identities(path, rows):
    columns = list(rows[0])

    if path.suffix == ".csv":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
    elif path.suffix == ".xlsx":
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Users"
        sheet.append(columns)
        for row in rows:
            sheet.append([row[column] for column in columns])
        workbook.save(path)
    elif path.suffix == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    elif path.suffix == ".parquet":
        pq.write_table(pa.Table.from_pylist(rows), path)
    else:
        raise ValueError(f"Unsupported fixture format: {path.suffix}")


def read_identities(path):
    if path.suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    if path.suffix == ".xlsx":
        workbook = load_workbook(path, read_only=True)
        try:
            columns, *rows = workbook["Users"].values
            return [dict(zip(columns, row)) for row in rows]
        finally:
            workbook.close()

    if path.suffix == ".json":
        columns = json.loads(path.read_text(encoding="utf-8"))
        return [
            {name: values[index] for name, values in columns.items()}
            for index in next(iter(columns.values()), {})
        ]

    if path.suffix == ".parquet":
        return pq.read_table(path).to_pylist()

    raise ValueError(f"Unsupported fixture format: {path.suffix}")


@pytest.mark.parametrize(
    ("source_format", "target_format"),
    [
        ("csv", "excel"),
        ("csv", "json"),
        ("csv", "parquet"),
        ("json", "excel"),
        ("json", "csv"),
        ("json", "parquet"),
        ("parquet", "excel"),
        ("parquet", "csv"),
        ("parquet", "json"),
        ("excel", "csv"),
        ("excel", "json"),
    ],
)
def test_conversion_preserves_identity_records(tmp_path, source_format, target_format):
    source_file = tmp_path / ("input" + EXTENSIONS[source_format])
    target_file = tmp_path / ("output" + EXTENSIONS[target_format])
    write_identities(source_file, IDENTITIES)

    converter = AsyncFileConverter(source_file)
    convert = getattr(converter, f"convert_{source_format}_to_{target_format}")
    asyncio.run(convert(target_file))

    assert read_identities(target_file) == IDENTITIES


def test_csv_to_excel_applies_column_mapping(tmp_path):
    source_file = tmp_path / "input.csv"
    target_file = tmp_path / "output.xlsx"
    write_identities(source_file, IDENTITIES)
    mapping = {"name": "Full Name", "email": "Email Address"}

    asyncio.run(
        AsyncFileConverter(source_file).convert_csv_to_excel(
            target_file, column_mapping=mapping
        )
    )

    assert read_identities(target_file) == [
        {mapping[column]: value for column, value in row.items()} for row in IDENTITIES
    ]


def test_excel_to_csv_keeps_only_requested_columns(tmp_path):
    source_file = tmp_path / "input.xlsx"
    target_file = tmp_path / "output.csv"
    write_identities(source_file, [{**row, "age": 30} for row in IDENTITIES])

    asyncio.run(
        AsyncFileConverter(source_file).convert_excel_to_csv(
            target_file, columns_to_keep=["name", "email"]
        )
    )

    assert read_identities(target_file) == IDENTITIES
