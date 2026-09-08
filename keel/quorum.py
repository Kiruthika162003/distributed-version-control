"""Quorum: approvals counted toward a threshold, with every vote on record.

Some changes need more than a reviewer; they need a
quorum, the schema migration and the license swap and the
history rewrite, and the ledger runs the arithmetic in the
open. A proposal names what it is for and how many
approvals it needs, votes are recorded by name with
duplicates refused because one person twice is one person,
and the threshold crossing is announced in the receipt of
the vote that crossed it, so the deciding voter knows they
decided, which is information people deserve at the moment
of the click and not in the minutes later. The veto is one
name stopping the count with a reason, standing until that
same name lifts it, because a veto anyone else can lift is
a strongly worded comment, and proposals expire only by
withdrawal, never quietly, since the proposal that
evaporates unannounced returns as the change nobody
remembers approving.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid, Missing


@dataclass
class Proposal:
    subject: str
    needed: int
    approvals: list[str] = field(default_factory=list)
    veto_by: str = ""
    veto_reason: str = ""


@dataclass
class QuorumLedger:
    proposals: dict[str, Proposal] = field(
        default_factory=dict
    )

    def propose(
        self, key: str, subject: str, needed: int
    ) -> str:
        if needed < 2:
            raise Invalid(
                "a quorum of one is a reviewer with "
                "paperwork"
            )
        if key in self.proposals:
            raise Invalid(
                f"{key} is already proposed; second "
                "thoughts go in the first proposal"
            )
        self.proposals[key] = Proposal(
            subject=subject, needed=needed
        )
        return (
            f"{key} proposed: {subject}, needs "
            f"{needed}"
        )

    def _get(self, key: str) -> Proposal:
        proposal = self.proposals.get(key)
        if proposal is None:
            raise Missing(f"{key} is not proposed")
        return proposal

    def approve(self, key: str, voter: str) -> str:
        proposal = self._get(key)
        if proposal.veto_by:
            raise Conflict(
                f"{key} stands vetoed by "
                f"{proposal.veto_by} "
                f"({proposal.veto_reason}); votes "
                "wait until that same name lifts it"
            )
        if voter in proposal.approvals:
            raise Invalid(
                f"{voter} already approved {key}; "
                "one person twice is one person"
            )
        proposal.approvals.append(voter)
        held = len(proposal.approvals)
        if held == proposal.needed:
            return (
                f"{key} reaches quorum at "
                f"{held} of {proposal.needed}; "
                f"{voter}, your vote decided it, "
                "which you deserve to know now and "
                "not in the minutes"
            )
        return (
            f"{key}: {held} of {proposal.needed}, "
            f"{voter} on record"
        )

    def veto(
        self, key: str, voter: str, reason: str
    ) -> str:
        proposal = self._get(key)
        if not reason.strip():
            raise Invalid(
                "a veto without a reason is a mood "
                "with authority"
            )
        if proposal.veto_by:
            raise Conflict(
                f"{key} is already vetoed by "
                f"{proposal.veto_by}"
            )
        proposal.veto_by = voter
        proposal.veto_reason = reason
        return (
            f"{key} vetoed by {voter}: {reason}; "
            "standing until the same name lifts it"
        )

    def lift_veto(self, key: str, voter: str) -> str:
        proposal = self._get(key)
        if not proposal.veto_by:
            raise Missing(f"{key} is not vetoed")
        if proposal.veto_by != voter:
            raise Invalid(
                f"the veto belongs to "
                f"{proposal.veto_by}; a veto anyone "
                "else can lift is a strongly worded "
                "comment"
            )
        proposal.veto_by = ""
        proposal.veto_reason = ""
        return f"{key}: the veto is lifted by {voter}"

    def withdraw(self, key: str) -> str:
        proposal = self.proposals.pop(key, None)
        if proposal is None:
            raise Missing(f"{key} is not proposed")
        return (
            f"{key} withdrawn with "
            f"{len(proposal.approvals)} approval(s) "
            "on record; announced, never evaporated"
        )

    def standing(self) -> str:
        if not self.proposals:
            return "no proposals stand"
        lines = [
            f"{len(self.proposals)} proposal(s) "
            "standing:"
        ]
        for key in sorted(self.proposals):
            proposal = self.proposals[key]
            state = (
                f"VETOED by {proposal.veto_by}"
                if proposal.veto_by
                else (
                    f"{len(proposal.approvals)} of "
                    f"{proposal.needed}"
                )
            )
            lines.append(
                f"  {key}: {proposal.subject} "
                f"({state})"
            )
        return "\n".join(lines)
