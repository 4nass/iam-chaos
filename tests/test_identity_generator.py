import asyncio
import csv

import pytest

from core.address_factory import AddressFactory
from core.identity_generator import generate_identities_parallel, generate_identity


def test_generate_identity():
    unique_usernames = {}

    identity = generate_identity(unique_usernames=unique_usernames)

    assert identity["username"]
    assert identity["email"]
    assert identity["name"]
    assert identity["username"] in unique_usernames


def test_generate_unique_usernames():
    unique_usernames = {}

    first = generate_identity(unique_usernames=unique_usernames)
    second = generate_identity(unique_usernames=unique_usernames)

    assert first["username"] != second["username"]
    assert set(unique_usernames) == {first["username"], second["username"]}


def test_generate_french_address():
    address = AddressFactory.create_address("fr_FR").generate()

    assert address["streetName"]
    assert address["postalCode"]
    assert address["locality"]
    assert address["country"] == "France"


def test_zero_identities_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        asyncio.run(
            generate_identities_parallel(
                0, output_file=tmp_path / "identities", output_format="all"
            )
        )

    assert not list(tmp_path.iterdir())


def test_export_large_batch_to_csv(tmp_path):
    output_file = tmp_path / "identities"
    asyncio.run(
        generate_identities_parallel(
            10_000, output_file=output_file, output_format="csv", workers=4
        )
    )

    with output_file.with_suffix(".csv").open(encoding="utf-8", newline="") as handle:
        assert sum(1 for _ in csv.DictReader(handle)) == 10_000


def test_column_mapping(tmp_path):
    output_file = tmp_path / "identities"
    column_mapping = {"username": "User Name", "email": "Email Address"}
    asyncio.run(
        generate_identities_parallel(
            10,
            output_file=output_file,
            output_format="csv",
            column_mapping=column_mapping,
            workers=1,
        )
    )

    with output_file.with_suffix(".csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 10
    assert {"User Name", "Email Address"} <= rows[0].keys()
    assert {"username", "email"}.isdisjoint(rows[0])
    assert all(row["User Name"] and row["Email Address"] for row in rows)
