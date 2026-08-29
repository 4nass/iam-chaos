"""Virtual time utilities for deterministic scenario execution."""

from dataclasses import dataclass
from typing import Union


def parse_duration(value: Union[int, float, str]) -> float:
    if isinstance(value, bool):
        raise ValueError("time values cannot be booleans")
    if isinstance(value, (int, float)):
        seconds = float(value)
    elif isinstance(value, str):
        text = value.strip().lower()
        unit = "s"
        for suffix in ("ms", "s", "m", "h"):
            if text.endswith(suffix):
                unit = suffix
                text = text[: -len(suffix)].strip()
                break
        try:
            amount = float(text)
        except ValueError as exc:
            raise ValueError("invalid duration: {}".format(value)) from exc
        seconds = amount / 1000.0 if unit == "ms" else amount
        if unit == "m":
            seconds *= 60
        elif unit == "h":
            seconds *= 3600
    else:
        raise ValueError("unsupported time value: {}".format(type(value).__name__))

    if seconds < 0:
        raise ValueError("time values cannot be negative")
    return seconds


def format_offset(seconds: float) -> str:
    if float(seconds).is_integer():
        return "T+{}s".format(int(seconds))
    return "T+{}s".format(seconds)


@dataclass
class VirtualClock:
    current_seconds: float = 0.0

    def advance_to(self, value: Union[int, float, str]) -> float:
        seconds = parse_duration(value)
        if seconds < self.current_seconds:
            raise ValueError(
                "scenario time must be monotonic: {} < {}".format(
                    seconds, self.current_seconds
                )
            )
        self.current_seconds = seconds
        return seconds

    @property
    def offset(self) -> str:
        return format_offset(self.current_seconds)
