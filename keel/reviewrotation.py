"""Review rotation: the wheel turns fairly, and absences are declared.

Ownership names a team; somebody still has to pick the
person, and unpicked queues resolve by whoever answers
fastest, which is how the same two people review everything
until they leave. The wheel assigns within a team in strict
rotation, skipping the declared-away rather than the merely
slow, and every skip is said in the receipt, because a
rotation that silently passes someone over is
indistinguishable from one that forgot them. Load counts
ride on the roster so the fairness is auditable, assigned
totals visible to everyone, and the away list requires a
return marker in the reason, not a date the system would
have to understand, just a word a human left, since the
absence nobody explains becomes the permanent exemption
everybody resents. An empty bench, everyone away, is
refused loudly rather than assigned around, because
work routed to a ghost team fails slower than work
refused now.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing


@dataclass
class Wheel:
    rosters: dict[str, list[str]] = field(
        default_factory=dict
    )
    cursor: dict[str, int] = field(default_factory=dict)
    load: dict[str, int] = field(default_factory=dict)
    away: dict[str, str] = field(default_factory=dict)

    def enroll(self, team: str, member: str) -> str:
        roster = self.rosters.setdefault(team, [])
        if member in roster:
            raise Invalid(
                f"{member} already rides the {team} "
                "wheel"
            )
        roster.append(member)
        self.load.setdefault(member, 0)
        return f"{member} joins the {team} wheel"

    def declare_away(
        self, member: str, reason: str
    ) -> str:
        if not reason.strip():
            raise Invalid(
                "an absence nobody explains becomes "
                "the permanent exemption everybody "
                "resents"
            )
        self.away[member] = reason
        return f"{member} away: {reason}"

    def declare_back(self, member: str) -> str:
        if member not in self.away:
            raise Missing(
                f"{member} was never declared away"
            )
        del self.away[member]
        return f"{member} rides again"

    def assign(self, team: str) -> str:
        roster = self.rosters.get(team)
        if not roster:
            raise Missing(
                f"{team} has no wheel; enroll riders "
                "first"
            )
        start = self.cursor.get(team, 0)
        skipped: list[str] = []
        for offset in range(len(roster)):
            index = (start + offset) % len(roster)
            candidate = roster[index]
            if candidate in self.away:
                skipped.append(
                    f"{candidate} "
                    f"({self.away[candidate]})"
                )
                continue
            self.cursor[team] = index + 1
            self.load[candidate] += 1
            receipt = (
                f"{team} assigns {candidate} "
                f"(load now {self.load[candidate]})"
            )
            if skipped:
                receipt += (
                    "; skipped " + ", ".join(skipped)
                    + ", said aloud because a silent "
                    "pass-over is a forgetting"
                )
            return receipt
        raise Invalid(
            f"the whole {team} bench is away: "
            + ", ".join(skipped)
            + "; work routed to a ghost team fails "
            "slower than work refused now"
        )

    def fairness(self, team: str) -> str:
        roster = self.rosters.get(team)
        if not roster:
            raise Missing(f"{team} has no wheel")
        lines = [f"the {team} wheel:"]
        for member in roster:
            marker = (
                f" [away: {self.away[member]}]"
                if member in self.away
                else ""
            )
            lines.append(
                f"  {member}: {self.load[member]} "
                f"assignment(s){marker}"
            )
        counts = [
            self.load[member] for member in roster
        ]
        spread = max(counts) - min(counts)
        lines.append(
            f"spread {spread}; fairness is auditable "
            "or it is folklore"
        )
        return "\n".join(lines)
