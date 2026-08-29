"""Versioned YAML scenario specification."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

from .clock import parse_duration
from .model import CredentialProfile


SUPPORTED_VERSION = 1


class ScenarioSpecError(ValueError):
    """Raised when a scenario is invalid or unsupported."""


@dataclass(frozen=True)
class MutationSpec:
    type: str
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Any) -> "MutationSpec":
        if isinstance(raw, str):
            return cls(type=raw.strip().lower())
        if not isinstance(raw, Mapping) or "type" not in raw:
            raise ScenarioSpecError("mutation must contain a type")
        params = dict(raw.get("params") or {})
        params.update(
            {
                key: value
                for key, value in raw.items()
                if key not in ("type", "params")
            }
        )
        return cls(type=str(raw["type"]).strip().lower(), params=params)


@dataclass(frozen=True)
class ScenarioStep:
    id: str
    at_seconds: float
    action: str
    identities: Optional[List[int]]
    mutations: List[MutationSpec]

    def target_indices(self, count: int) -> List[int]:
        if self.identities is None:
            return list(range(count))
        return list(self.identities)


@dataclass(frozen=True)
class IdentitySetSpec:
    count: int
    tenant_id: str = "default"
    groups: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    credential_profile: CredentialProfile = CredentialProfile.KNOWN_PASSWORD


@dataclass(frozen=True)
class ScenarioSpec:
    version: int
    name: str
    seed: Union[int, str]
    identities: IdentitySetSpec
    steps: List[ScenarioStep]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ScenarioSpec":
        if not isinstance(raw, Mapping):
            raise ScenarioSpecError("scenario root must be a mapping")
        if not isinstance(raw.get("version"), int) or isinstance(raw.get("version"), bool) or raw.get("version") != SUPPORTED_VERSION:
            raise ScenarioSpecError(
                "unsupported scenario version: {} (expected {})".format(
                    raw.get("version"), SUPPORTED_VERSION
                )
            )
        if "seed" not in raw:
            raise ScenarioSpecError("scenario seed is required")

        identity_raw = raw.get("identities") or {}
        if not isinstance(identity_raw, Mapping):
            raise ScenarioSpecError("identities must be a mapping")
        count = identity_raw.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ScenarioSpecError("identities.count must be a positive integer")

        try:
            credential_profile = CredentialProfile(
                identity_raw.get(
                    "credential_profile", CredentialProfile.KNOWN_PASSWORD
                )
            )
        except ValueError as exc:
            raise ScenarioSpecError(str(exc)) from exc

        steps_raw = raw.get("steps")
        if not isinstance(steps_raw, list) or not steps_raw:
            raise ScenarioSpecError("scenario must contain at least one step")

        steps = []
        allowed_actions = {"create", "update", "enable", "disable", "delete"}
        for position, step_raw in enumerate(steps_raw):
            if not isinstance(step_raw, Mapping):
                raise ScenarioSpecError("step {} must be a mapping".format(position))
            action = str(step_raw.get("action", "")).strip().lower()
            if action not in allowed_actions:
                raise ScenarioSpecError("unsupported action: {}".format(action))

            identities = step_raw.get("identities")
            if identities is not None:
                if identities == "all":
                    identities = None
                elif not isinstance(identities, list) or not all(
                    isinstance(item, int) and not isinstance(item, bool)
                    for item in identities
                ):
                    raise ScenarioSpecError(
                        "step identities must be a list of integer indexes or all"
                    )
                elif any(item < 0 or item >= count for item in identities):
                    raise ScenarioSpecError(
                        "step identity index is outside the configured count"
                    )

            mutations_raw = step_raw.get("mutations") or []
            if not isinstance(mutations_raw, list):
                raise ScenarioSpecError("step mutations must be a list")

            try:
                at_seconds = parse_duration(step_raw.get("at", 0))
            except ValueError as exc:
                raise ScenarioSpecError(
                    "invalid time in step {}".format(position)
                ) from exc

            steps.append(
                ScenarioStep(
                    id=str(step_raw.get("id", "step-{}".format(position))),
                    at_seconds=at_seconds,
                    action=action,
                    identities=identities,
                    mutations=[MutationSpec.from_raw(item) for item in mutations_raw],
                )
            )

        previous = -1.0
        for step in steps:
            if step.at_seconds < previous:
                raise ScenarioSpecError("step times must be monotonic")
            previous = step.at_seconds

        return cls(
            version=SUPPORTED_VERSION,
            name=str(raw.get("name", "unnamed-scenario")),
            seed=raw["seed"],
            identities=IdentitySetSpec(
                count=count,
                tenant_id=str(identity_raw.get("tenant_id", "default")),
                groups=list(identity_raw.get("groups") or []),
                roles=list(identity_raw.get("roles") or []),
                credential_profile=credential_profile,
            ),
            steps=steps,
        )


def load_scenario(source: Union[str, Path, Mapping[str, Any]]) -> ScenarioSpec:
    """Load a scenario from a mapping, YAML text, or YAML file path."""
    if isinstance(source, Mapping):
        return ScenarioSpec.from_dict(source)

    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif isinstance(source, str):
        if os.path.exists(source) and "\\n" not in source:
            text = Path(source).read_text(encoding="utf-8")
        else:
            text = source
    else:
        raise ScenarioSpecError("scenario must be a path, YAML string, or mapping")

    try:
        import yaml
    except ImportError as exc:
        raise ScenarioSpecError("PyYAML is required to load YAML scenarios") from exc

    try:
        parsed = yaml.safe_load(text)
    except Exception as exc:
        raise ScenarioSpecError("invalid YAML: {}".format(exc)) from exc
    return ScenarioSpec.from_dict(parsed)
