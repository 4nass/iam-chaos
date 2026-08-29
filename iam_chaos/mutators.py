"""Deterministic data and delivery mutators."""

import copy
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from .model import normalize_username


@dataclass
class MutationContext:
    current_index: int
    identities: Mapping[int, Dict[str, Any]]


def _mark(payload: Dict[str, Any], name: str) -> None:
    metadata = payload.setdefault("metadata", {})
    applied = metadata.setdefault("applied_mutations", [])
    if name not in applied:
        applied.append(name)


class UnicodeMutator:
    """Apply NFC or NFD to identity text fields."""

    name = "unicode_nfc_nfd"

    def apply(
        self,
        payload: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        context: Optional[MutationContext] = None,
    ) -> Dict[str, Any]:
        params = params or {}
        form = str(params.get("form", "nfd")).upper()
        if form not in ("NFC", "NFD"):
            raise ValueError("unicode form must be NFC or NFD")
        for field_name in ("username", "raw_username"):
            if isinstance(payload.get(field_name), str):
                payload[field_name] = unicodedata.normalize(
                    form, payload[field_name]
                )
        if isinstance(payload.get("name"), dict):
            for field_name in ("given_name", "family_name", "formatted"):
                value = payload["name"].get(field_name)
                if isinstance(value, str):
                    payload["name"][field_name] = unicodedata.normalize(form, value)
        payload["normalized_username"] = normalize_username(payload["username"])
        _mark(payload, self.name + "_" + form.lower())
        return payload


class UsernameCollisionMutator:
    name = "username_collision"

    def apply(
        self,
        payload: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        context: Optional[MutationContext] = None,
    ) -> Dict[str, Any]:
        if context is None:
            raise ValueError("username collision requires a mutation context")
        params = params or {}
        target_index = params.get("target_index")
        if target_index is None:
            target_index = max(0, context.current_index - 1)
        try:
            target = context.identities[int(target_index)]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("username collision target does not exist") from exc
        payload["username"] = target["username"]
        payload["raw_username"] = target.get("raw_username", target["username"])
        payload["normalized_username"] = normalize_username(payload["username"])
        _mark(payload, self.name)
        return payload


class InvalidEmailMutator:
    name = "invalid_email"

    def apply(
        self,
        payload: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        context: Optional[MutationContext] = None,
    ) -> Dict[str, Any]:
        params = params or {}
        value = str(params.get("value", "invalid-email"))
        email_index = int(params.get("index", 0))
        emails = payload.setdefault("emails", [])
        while len(emails) <= email_index:
            emails.append(
                {"value": value, "primary": False, "verified": False}
            )
        emails[email_index]["value"] = value
        _mark(payload, self.name)
        return payload


class MissingRequiredFieldMutator:
    name = "missing_required_field"

    def apply(
        self,
        payload: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        context: Optional[MutationContext] = None,
    ) -> Dict[str, Any]:
        params = params or {}
        field_name = str(params.get("field", "username"))
        target: Dict[str, Any] = payload
        parts = field_name.split(".")
        for part in parts[:-1]:
            value = target.get(part)
            if not isinstance(value, dict):
                return payload
            target = value
        target.pop(parts[-1], None)
        _mark(payload, self.name + ":" + field_name)
        return payload


class EventReplayMutator:
    name = "event_replay"


class OutOfOrderMutator:
    name = "out_of_order"


PAYLOAD_MUTATORS = {
    "unicode": UnicodeMutator(),
    "unicode_nfc_nfd": UnicodeMutator(),
    "username_collision": UsernameCollisionMutator(),
    "invalid_email": InvalidEmailMutator(),
    "missing_required_field": MissingRequiredFieldMutator(),
}

DELIVERY_MUTATIONS = {"event_replay", "out_of_order"}


def apply_payload_mutation(
    payload: Dict[str, Any],
    mutation_type: str,
    params: Optional[Dict[str, Any]],
    context: MutationContext,
) -> Dict[str, Any]:
    mutator = PAYLOAD_MUTATORS.get(mutation_type)
    if mutator is None:
        if mutation_type in DELIVERY_MUTATIONS:
            return payload
        raise ValueError("unsupported mutation: {}".format(mutation_type))
    return mutator.apply(copy.deepcopy(payload), params, context)
