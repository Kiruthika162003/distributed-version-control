"""Weigh anchor: the checklist run before history is allowed to move.

Rewrites are legal in this workshop and never casual, and
the anchor check gathers everything that should be read
before one: the wake of the commit about to be rewritten,
because the wake is who pays; the standing orders in
force, because a freeze binds a rewrite exactly as it
binds a landing; and, when a quorum ledger is offered, the
proposal's own count, since the rewrite that needed three
names and sailed on one is the incident report writing
itself. The verdict is advisory in the doctor's tradition,
CLEAR TO WEIGH or HOLD FAST with the reasons listed,
because the machinery for refusing already exists in the
gauntlets and this page is the officer reading the water
before anyone touches the capstan. The clear verdict
still names the wake it is about to disturb, a rewrite
with a clean checklist being permitted, not painless.
"""

from __future__ import annotations

from keel.quorum import QuorumLedger
from keel.repo import Repo
from keel.standingorders import board
from keel.wake import wake_of


def check(
    repo: Repo,
    address: str,
    proposal_key: str = "",
    ledger: QuorumLedger | None = None,
    **organ_state,
) -> str:
    holds: list[str] = []
    wake = wake_of(repo, address)
    riding = sorted(
        branch
        for branch, tip in repo.refs.branches.items()
        if tip in wake or tip == address
    )
    orders = board(**organ_state)
    if not orders.startswith("no standing orders"):
        holds.append(
            "standing orders are in force; a freeze "
            "binds a rewrite exactly as it binds a "
            "landing"
        )
    if ledger is not None and proposal_key:
        proposal = ledger.proposals.get(proposal_key)
        if proposal is None:
            holds.append(
                f"{proposal_key} was never proposed; "
                "the rewrite that needed names and "
                "sailed on none writes its own "
                "incident report"
            )
        elif proposal.veto_by:
            holds.append(
                f"{proposal_key} stands vetoed by "
                f"{proposal.veto_by}"
            )
        elif (
            len(proposal.approvals) < proposal.needed
        ):
            holds.append(
                f"{proposal_key} stands at "
                f"{len(proposal.approvals)} of "
                f"{proposal.needed}; short of quorum"
            )
    lines = [
        f"weighing anchor on {address[:8]}: "
        f"{len(wake)} commit(s) in the wake, "
        f"{len(riding)} branch tip(s) riding"
    ]
    lines.append(orders)
    if holds:
        lines.append("HOLD FAST:")
        lines.extend(f"  {reason}" for reason in holds)
    else:
        lines.append(
            "CLEAR TO WEIGH; permitted, not "
            "painless, and the wake above is who "
            "pays"
        )
    return "\n".join(lines)
