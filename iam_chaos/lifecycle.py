"""Offline identity lifecycle state machine."""

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .model import LifecycleState, normalize_username


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class IdentityRecord:
    state: LifecycleState
    version: int
    username: str
    last_event_id: str = ""
    last_time: float = 0.0


@dataclass
class TransitionResult:
    accepted: bool
    outcome: str
    state_before: Optional[str]
    state_after: Optional[str]
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "outcome": self.outcome,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "reason": self.reason,
        }


class IdentityStateMachine:
    """Apply lifecycle events with provider-neutral offline semantics."""

    def __init__(self) -> None:
        self.records: Dict[str, IdentityRecord] = {}
        self.username_index: Dict[str, str] = {}
        self.seen_event_ids = set()
        self.accepted_event_ids = set()

    @staticmethod
    def _state_value(state: Optional[LifecycleState]) -> Optional[str]:
        return state.value if state else None

    def _result(
        self,
        accepted: bool,
        outcome: str,
        before: Optional[LifecycleState],
        after: Optional[LifecycleState],
        reason: str = "",
    ) -> TransitionResult:
        return TransitionResult(
            accepted=accepted,
            outcome=outcome,
            state_before=self._state_value(before),
            state_after=self._state_value(after),
            reason=reason,
        )

    def _validate_payload(
        self, payload: Dict[str, Any], identity_id: str
    ) -> Optional[TransitionResult]:
        required = ("id", "external_id", "username", "emails", "name")
        for field_name in required:
            if field_name not in payload:
                return self._result(
                    False,
                    "invalid_payload",
                    None,
                    None,
                    "missing_required_field:{}".format(field_name),
                )
        if payload.get("id") != identity_id:
            return self._result(False, "invalid_payload", None, None, "id_mismatch")

        username = payload.get("username")
        if not isinstance(username, str) or not username.strip():
            return self._result(False, "invalid_payload", None, None, "invalid_username")
        if any(ord(char) < 32 for char in username):
            return self._result(
                False, "invalid_payload", None, None, "control_character"
            )

        emails = payload.get("emails")
        if not isinstance(emails, list) or not emails:
            return self._result(False, "invalid_payload", None, None, "invalid_emails")
        for email in emails:
            if not isinstance(email, dict) or not _EMAIL_RE.match(
                str(email.get("value", ""))
            ):
                return self._result(False, "invalid_payload", None, None, "invalid_email")

        if not isinstance(payload.get("name"), dict):
            return self._result(False, "invalid_payload", None, None, "invalid_name")

        owner = self.username_index.get(normalize_username(username))
        if owner and owner != identity_id:
            record = self.records.get(owner)
            if record and record.state != LifecycleState.DELETED:
                return self._result(
                    False,
                    "username_conflict",
                    None,
                    None,
                    "username_already_in_use:{}".format(owner),
                )
        return None

    def apply(self, event: Dict[str, Any]) -> TransitionResult:
        event_id = str(event.get("event_id", ""))
        identity_id = str(event.get("identity_id", ""))
        action = str(event.get("action", "")).lower()
        payload = event.get("payload") or {}
        record = self.records.get(identity_id)

        replayed_from = event.get("replayed_from")
        if replayed_from and replayed_from in self.accepted_event_ids:
            self.seen_event_ids.add(event_id)
            state = record.state if record else None
            return self._result(True, "idempotent", state, state, "event_replay")

        if event_id:
            self.seen_event_ids.add(event_id)

        if action in ("create", "update"):
            invalid = self._validate_payload(payload, identity_id)
            if invalid:
                return invalid

        if action == "create":
            if record and record.state != LifecycleState.DELETED:
                if normalize_username(record.username) == normalize_username(
                    payload["username"]
                ):
                    self.accepted_event_ids.add(event_id)
                    return self._result(
                        True,
                        "idempotent",
                        record.state,
                        record.state,
                        "duplicate_create",
                    )
                return self._result(
                    False,
                    "username_conflict",
                    record.state,
                    record.state,
                    "identity_already_exists",
                )

            state_before = record.state if record else None
            if record and record.username:
                self.username_index.pop(normalize_username(record.username), None)
            username = str(payload["username"])
            self.records[identity_id] = IdentityRecord(
                state=LifecycleState.ACTIVE,
                version=(record.version + 1 if record else 1),
                username=username,
                last_event_id=event_id,
                last_time=float(event.get("time_seconds", 0)),
            )
            self.username_index[normalize_username(username)] = identity_id
            self.accepted_event_ids.add(event_id)
            return self._result(
                True, "accepted", state_before, LifecycleState.ACTIVE
            )

        if action == "update":
            if not record:
                return self._result(
                    False, "identity_not_found", None, None, "create_required"
                )
            if record.state == LifecycleState.DELETED:
                return self._result(
                    False,
                    "deleted_identity",
                    record.state,
                    record.state,
                    "update_after_delete",
                )
            old_username = record.username
            new_username = str(payload["username"])
            if old_username != new_username:
                self.username_index.pop(normalize_username(old_username), None)
                self.username_index[normalize_username(new_username)] = identity_id
            record.username = new_username
            record.version += 1
            record.last_event_id = event_id
            record.last_time = float(event.get("time_seconds", 0))
            self.accepted_event_ids.add(event_id)
            return self._result(True, "accepted", record.state, record.state)

        if action in ("enable", "disable"):
            if not record:
                return self._result(
                    False, "identity_not_found", None, None, "create_required"
                )
            if record.state == LifecycleState.DELETED:
                return self._result(
                    False,
                    "deleted_identity",
                    record.state,
                    record.state,
                    "lifecycle_after_delete",
                )
            target = LifecycleState.ACTIVE if action == "enable" else LifecycleState.DISABLED
            if record.state == target:
                self.accepted_event_ids.add(event_id)
                return self._result(
                    True, "idempotent", record.state, record.state, "state_replay"
                )
            before = record.state
            record.state = target
            record.version += 1
            record.last_event_id = event_id
            record.last_time = float(event.get("time_seconds", 0))
            self.accepted_event_ids.add(event_id)
            return self._result(True, "accepted", before, target)

        if action == "delete":
            if not record:
                return self._result(
                    False, "identity_not_found", None, None, "create_required"
                )
            if record.state == LifecycleState.DELETED:
                self.accepted_event_ids.add(event_id)
                return self._result(
                    True, "idempotent", record.state, record.state, "state_replay"
                )
            before = record.state
            self.username_index.pop(normalize_username(record.username), None)
            record.state = LifecycleState.DELETED
            record.version += 1
            record.last_event_id = event_id
            record.last_time = float(event.get("time_seconds", 0))
            self.accepted_event_ids.add(event_id)
            return self._result(True, "accepted", before, LifecycleState.DELETED)

        return self._result(False, "invalid_action", None, None, action)
