"""Deterministic canonical identity generation."""

import hashlib
import unicodedata
import uuid
from typing import List

from .model import (
    CanonicalIdentity,
    CredentialProfile,
    EmailAttribute,
    IdentityMetadata,
    LifecycleState,
    NameAttribute,
    normalize_username,
)


_GIVEN_NAMES = ("Elodie", "Zoe", "Inigo", "Amina", "Noah", "Marius")
_FAMILY_NAMES = ("Renard", "Muller", "Nunez", "Bernard", "Kovac", "Martin")


def seed_hash(seed: object) -> str:
    return hashlib.sha256(str(seed).encode("utf-8")).hexdigest()


def _digest(seed: object, index: int) -> bytes:
    value = "{}:{}".format(seed, index).encode("utf-8")
    return hashlib.sha256(value).digest()


def _username_part(value: str) -> str:
    value = unicodedata.normalize("NFC", value).strip().casefold()
    return "-".join(value.split())


def _email_part(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return value.encode("ascii", "ignore").decode("ascii").casefold()


def generate_identity(
    seed: object,
    index: int,
    tenant_id: str = "default",
    groups: List[str] = None,
    roles: List[str] = None,
    credential_profile: CredentialProfile = CredentialProfile.KNOWN_PASSWORD,
    scenario_origin: str = "offline",
) -> CanonicalIdentity:
    """Generate one identity from seed and index without shared state."""
    if index < 0:
        raise ValueError("identity index must be non-negative")

    digest = _digest(seed, index)
    given_name = _GIVEN_NAMES[digest[0] % len(_GIVEN_NAMES)]
    family_name = _FAMILY_NAMES[digest[1] % len(_FAMILY_NAMES)]

    # Keep the canonical name human-readable and accented for Unicode tests.
    if given_name == "Elodie":
        given_name = chr(0x00C9) + "lodie"
    if family_name == "Muller":
        family_name = "M" + chr(0x00FC) + "ller"
    if family_name == "Nunez":
        family_name = "N" + chr(0x00FA) + chr(0x00F1) + "ez"

    username = "{}.{}{:04d}".format(
        _username_part(given_name),
        _username_part(family_name),
        index,
    )
    email = "{}@example.test".format(
        "{}.{}".format(_email_part(given_name), _email_part(family_name))
    )
    identity_id = "usr_{}".format(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            "iam-chaos:{}:identity:{}".format(seed, index),
        )
    )
    external_id = "EMP-{}".format(digest[:5].hex().upper())

    return CanonicalIdentity(
        id=identity_id,
        external_id=external_id,
        username=username,
        raw_username=username,
        normalized_username=normalize_username(username),
        emails=[EmailAttribute(email, primary=True, verified=True)],
        name=NameAttribute(given_name, family_name),
        active=True,
        lifecycle_state=LifecycleState.ACTIVE,
        credential_profile=credential_profile,
        tenant_id=tenant_id,
        groups=list(groups or []),
        roles=list(roles or []),
        metadata=IdentityMetadata(
            seed_hash=seed_hash(seed),
            index=index,
            scenario_origin=scenario_origin,
        ),
    )


def generate_identities(
    seed: object,
    count: int,
    tenant_id: str = "default",
    groups: List[str] = None,
    roles: List[str] = None,
    credential_profile: CredentialProfile = CredentialProfile.KNOWN_PASSWORD,
    scenario_origin: str = "offline",
) -> List[CanonicalIdentity]:
    if count < 1:
        raise ValueError("identity count must be greater than zero")
    return [
        generate_identity(
            seed=seed,
            index=index,
            tenant_id=tenant_id,
            groups=groups,
            roles=roles,
            credential_profile=credential_profile,
            scenario_origin=scenario_origin,
        )
        for index in range(count)
    ]
