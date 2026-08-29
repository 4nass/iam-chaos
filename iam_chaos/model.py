"""Provider-neutral canonical identity model."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List
import unicodedata


class LifecycleState(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    DELETED = "DELETED"


class CredentialProfile(str, Enum):
    KNOWN_PASSWORD = "known_password"
    FORCE_RESET = "force_reset"
    EXPIRED = "expired"


def normalize_username(value: str) -> str:
    """Return the comparison form used for username uniqueness."""
    return unicodedata.normalize("NFC", value).strip().casefold()


@dataclass
class EmailAttribute:
    value: str
    primary: bool = True
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "primary": self.primary,
            "verified": self.verified,
        }


@dataclass
class NameAttribute:
    given_name: str
    family_name: str
    formatted: str = ""

    def __post_init__(self) -> None:
        if not self.formatted:
            self.formatted = "{} {}".format(self.given_name, self.family_name)

    def to_dict(self) -> Dict[str, str]:
        return {
            "given_name": self.given_name,
            "family_name": self.family_name,
            "formatted": self.formatted,
        }


@dataclass
class IdentityMetadata:
    seed_hash: str
    index: int
    scenario_origin: str
    scenario_step: str = ""
    applied_mutations: List[str] = field(default_factory=list)
    model_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed_hash": self.seed_hash,
            "index": self.index,
            "scenario_origin": self.scenario_origin,
            "scenario_step": self.scenario_step,
            "applied_mutations": list(self.applied_mutations),
            "model_version": self.model_version,
        }


@dataclass
class CanonicalIdentity:
    id: str
    external_id: str
    username: str
    raw_username: str
    normalized_username: str
    emails: List[EmailAttribute]
    name: NameAttribute
    active: bool = True
    lifecycle_state: LifecycleState = LifecycleState.ACTIVE
    credential_profile: CredentialProfile = CredentialProfile.KNOWN_PASSWORD
    tenant_id: str = "default"
    groups: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    metadata: IdentityMetadata = field(
        default_factory=lambda: IdentityMetadata("", 0, "")
    )

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("identity id is required")
        if not self.external_id:
            raise ValueError("external_id is required")
        if not self.username:
            raise ValueError("username is required")
        if not self.emails:
            raise ValueError("at least one email is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "external_id": self.external_id,
            "username": self.username,
            "raw_username": self.raw_username,
            "normalized_username": self.normalized_username,
            "emails": [email.to_dict() for email in self.emails],
            "name": self.name.to_dict(),
            "active": self.active,
            "lifecycle_state": self.lifecycle_state.value,
            "credential_profile": self.credential_profile.value,
            "tenant_id": self.tenant_id,
            "groups": list(self.groups),
            "roles": list(self.roles),
            "metadata": self.metadata.to_dict(),
        }
