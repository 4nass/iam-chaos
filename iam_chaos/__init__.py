"""Public IAMChaos library API."""

from .engine import ScenarioEngine
from .model import (
    CanonicalIdentity,
    CredentialProfile,
    EmailAttribute,
    IdentityMetadata,
    LifecycleState,
    NameAttribute,
)

__all__ = [
    "CanonicalIdentity",
    "CredentialProfile",
    "EmailAttribute",
    "IdentityMetadata",
    "LifecycleState",
    "NameAttribute",
    "ScenarioEngine",
]

__version__ = "0.1.0"
