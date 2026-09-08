"""A witness testifies to numbers it measured, and holds or it does not."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Testimony:
    witness: str
    claim: str
    numbers: dict[str, object]
    holds: bool

    def line(self) -> str:
        state = "holds" if self.holds else "BROKEN"
        return f"{self.witness}: {state}: {self.claim}"
