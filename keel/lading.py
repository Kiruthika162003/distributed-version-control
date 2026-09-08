"""The bill of lading: what a push will ship, itemized before the wire.

Pushes are quoted after the fact everywhere else, the
objects counted once they have already traveled, and the
bill of lading moves the quote before the decision: run
the same negotiation the push would run, against the same
remote haves, and itemize what would go, commits with
their subjects, the object count by kind, and the total
freight in bytes, because the surprise thousand-object
push is only a surprise to people who were never shown
the bill. The empty bill is its own answer, nothing to
ship, the remote already holds this line, and the bill
never moves anything, quoting being the whole of its
job, so reading it twice costs two reads and zero
regrets.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo
from keel.transfer import negotiate


def bill(
    local: Repo, remote: Repo, branch: str
) -> str:
    tip = local.refs.branches.get(branch)
    if tip is None:
        raise Invalid(
            f"{branch} is not a local branch"
        )
    batch = negotiate(
        local,
        wants=[tip],
        haves=list(remote.graph.commits),
    )
    if not batch.objects:
        return (
            f"nothing to ship on {branch}; the "
            "remote already holds this line"
        )
    by_kind: dict[str, int] = {}
    freight = 0
    commits = []
    for address, (kind, payload) in (
        batch.objects.items()
    ):
        by_kind[kind] = by_kind.get(kind, 0) + 1
        freight += len(payload)
        if kind == "commit":
            commits.append(address)
    commits.sort(
        key=lambda address: -local.graph.get(
            address
        ).sequence
    )
    lines = [
        f"bill of lading for {branch}: "
        f"{len(batch.objects)} object(s), "
        f"{freight} byte(s) of freight"
    ]
    for kind in sorted(by_kind):
        lines.append(
            f"  {kind}: {by_kind[kind]}"
        )
    for address in commits:
        subject = local.graph.get(
            address
        ).message.splitlines()[0]
        lines.append(
            f"  shipping: {address[:8]} {subject}"
        )
    lines.append(
        "quoted before the wire; the thousand-object "
        "surprise only surprises people who were "
        "never shown the bill"
    )
    return "\n".join(lines)
