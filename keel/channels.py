"""Release channels: a ladder where promotions climb and never sidle.

Dev, beta, stable is a promise about order: nothing reaches
a rung without standing on the one below, so stable never
skips beta no matter how urgent the quarter feels, because
the skipped rung is exactly where the bug would have been
caught. Promotions are fast-forward by law, a channel never
rewinds by promotion, since users on a channel experience a
rewind as the product forgetting things it knew. The
rollback exists for the bad release and pays for itself in
loudness: it demands a written why, lands in the journal in
capitals, and is the only way a channel moves backward, so
every rewind in the record has a sentence attached that
someone chose to sign. The lag report counts how far each
rung trails the one below in commits, because "beta is
eleven commits behind dev" is a planning fact and a
comfort, in that order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass
class Channels:
    repo: Repo
    ladder: tuple[str, ...] = ("dev", "beta", "stable")
    held: dict[str, str] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)

    def _rung(self, channel: str) -> int:
        if channel not in self.ladder:
            raise Missing(
                f"{channel} is not a rung; the ladder "
                f"is {' -> '.join(self.ladder)}"
            )
        return self.ladder.index(channel)

    def advance(self, address: str) -> str:
        bottom = self.ladder[0]
        self.repo.graph.get(address)
        current = self.held.get(bottom)
        if current is not None and not (
            self.repo.graph.is_ancestor(current, address)
        ):
            raise Invalid(
                f"{bottom} would rewind from "
                f"{current[:8]} to {address[:8]}; even "
                "the bottom rung moves forward, and "
                "rewinds go through rollback with a "
                "signed why"
            )
        self.held[bottom] = address
        self.journal.append(
            f"{bottom} advanced to {address[:8]}"
        )
        return f"{bottom} now at {address[:8]}"

    def promote(self, channel: str) -> str:
        rung = self._rung(channel)
        if rung == 0:
            raise Invalid(
                f"{channel} is the bottom rung; it "
                "advances, it is not promoted"
            )
        below = self.ladder[rung - 1]
        source = self.held.get(below)
        if source is None:
            raise Invalid(
                f"{below} holds nothing; a promotion "
                "from an empty rung is a leap of faith, "
                "and ladders exist to end those"
            )
        current = self.held.get(channel)
        if current == source:
            return (
                f"{channel} already holds {source[:8]}; "
                "nothing to climb"
            )
        if current is not None and not (
            self.repo.graph.is_ancestor(current, source)
        ):
            raise Invalid(
                f"promoting {below} to {channel} would "
                f"rewind {channel} from {current[:8]} "
                f"to {source[:8]}; users experience a "
                "rewind as the product forgetting "
                "things it knew"
            )
        self.held[channel] = source
        self.journal.append(
            f"{channel} promoted to {source[:8]} "
            f"from {below}"
        )
        return (
            f"{channel} now at {source[:8]}, standing "
            f"on {below}"
        )

    def rollback(
        self, channel: str, address: str, why: str
    ) -> str:
        self._rung(channel)
        if not why.strip():
            raise Invalid(
                "a rollback without a why is a rewind "
                "nobody signed"
            )
        current = self.held.get(channel)
        if current is None:
            raise Invalid(
                f"{channel} holds nothing to roll back"
            )
        self.repo.graph.get(address)
        entry = (
            f"ROLLBACK {channel}: {current[:8]} -> "
            f"{address[:8]} because {why}"
        )
        self.held[channel] = address
        self.journal.append(entry)
        return entry

    def lag_report(self) -> str:
        lines = []
        for rung, channel in enumerate(self.ladder):
            address = self.held.get(channel)
            if address is None:
                lines.append(f"  {channel}: empty rung")
                continue
            if rung == 0:
                lines.append(
                    f"  {channel}: {address[:8]}, the "
                    "leading edge"
                )
                continue
            below_address = self.held.get(
                self.ladder[rung - 1]
            )
            if below_address is None:
                lines.append(
                    f"  {channel}: {address[:8]}, "
                    "nothing below to trail"
                )
                continue
            lag = len(
                self.repo.graph.ancestors(below_address)
                - self.repo.graph.ancestors(address)
            )
            lines.append(
                f"  {channel}: {address[:8]}, "
                f"{lag} commit(s) behind "
                f"{self.ladder[rung - 1]}"
            )
        return "\n".join(["the ladder:", *lines])
