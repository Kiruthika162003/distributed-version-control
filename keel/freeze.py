"""Freeze windows: the branch is closed, the sign says why, and by whom.

A freeze that is just a lock teaches people to route around
it, so every freeze here carries a reason and a name, and
every refusal repeats both, because "closed for the release
cut, ask Priya" gets respected while "permission denied"
gets worked around. The override exists on purpose: real
emergencies land during freezes, and a freeze tool without a
sanctioned exception trains people to build unsanctioned
ones. The exception's price is loudness, an approver who is
not the person landing, a ticket to point at, and a journal
entry in capitals, since a quiet override is
indistinguishable from the freeze not working. The journal
records refusals too, not to shame anyone but because the
question "how many landings did the freeze actually stop"
deserves a number, and a policy that cannot report its own
cost gets renewed forever on vibes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid, Missing


@dataclass(frozen=True)
class Freeze:
    branch: str
    reason: str
    frozen_by: str


@dataclass
class FreezeBoard:
    freezes: dict[str, Freeze] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)

    def freeze(
        self, branch: str, reason: str, by: str
    ) -> str:
        if not reason.strip():
            raise Invalid(
                "a freeze without a reason is a lockout, "
                "not a policy"
            )
        if not by.strip():
            raise Invalid(
                "an anonymous freeze cannot be asked about, "
                "so it cannot be respected"
            )
        if branch in self.freezes:
            standing = self.freezes[branch]
            raise Invalid(
                f"{branch} is already frozen by "
                f"{standing.frozen_by} ({standing.reason}); "
                "stack reasons in one freeze, not freezes "
                "in a stack"
            )
        self.freezes[branch] = Freeze(
            branch=branch, reason=reason, frozen_by=by
        )
        self.journal.append(
            f"frozen: {branch} by {by} ({reason})"
        )
        return f"{branch} frozen: {reason} (ask {by})"

    def lift(self, branch: str, by: str) -> str:
        standing = self.freezes.pop(branch, None)
        if standing is None:
            raise Missing(
                f"{branch} is not frozen; lifting warm "
                "air moves nothing"
            )
        self.journal.append(f"lifted: {branch} by {by}")
        return (
            f"{branch} lifted by {by}; the sign comes down"
        )

    def check_landing(self, branch: str, who: str) -> str:
        standing = self.freezes.get(branch)
        if standing is None:
            return f"{branch} is open; land away"
        self.journal.append(
            f"refused: {who} on {branch} "
            f"({standing.reason})"
        )
        raise Conflict(
            f"{branch} is closed for {standing.reason}; "
            f"ask {standing.frozen_by} or land with an "
            "override that names an approver and a ticket"
        )

    def override(
        self,
        branch: str,
        who: str,
        approver: str,
        ticket: str,
    ) -> str:
        standing = self.freezes.get(branch)
        if standing is None:
            raise Invalid(
                f"{branch} is not frozen; an override "
                "with nothing to override is a story for "
                "the postmortem"
            )
        if approver.strip() == who.strip():
            raise Invalid(
                "a self-approved override is a freeze "
                "with extra steps removed"
            )
        if not ticket.strip():
            raise Invalid(
                "an override without a ticket cannot be "
                "audited, and unauditable exceptions "
                "become the norm"
            )
        entry = (
            f"OVERRIDE: {who} landed on {branch} during "
            f"{standing.reason!r}, approved by {approver}, "
            f"ticket {ticket}"
        )
        self.journal.append(entry)
        return entry

    def report(self) -> str:
        frozen = sorted(self.freezes)
        refusals = sum(
            1
            for entry in self.journal
            if entry.startswith("refused:")
        )
        overrides = sum(
            1
            for entry in self.journal
            if entry.startswith("OVERRIDE:")
        )
        lines = [
            f"{len(frozen)} branch(es) frozen, "
            f"{refusals} landing(s) stopped, "
            f"{overrides} override(s)"
        ]
        for branch in frozen:
            standing = self.freezes[branch]
            lines.append(
                f"  {branch}: {standing.reason} "
                f"(ask {standing.frozen_by})"
            )
        lines.extend(
            f"  {entry}"
            for entry in self.journal
            if entry.startswith("OVERRIDE:")
        )
        return "\n".join(lines)
