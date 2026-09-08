"""The compass: one commit oriented against every name in the harbor.

Handed a bare address, the first question is where am I,
and the compass answers it against everything that has a
name: which branches carry this commit, each with the
distance from its tip, because carried by main at distance
zero and carried by main at distance forty are different
situations wearing the same preposition; which tags seal
history that includes it, the eras it is part of; and,
when nothing carries it, the wandering verdict, reachable
from no name, with the pointer to the lost and found where
such commits are shelved. Distances are counted in
commits, not sequence arithmetic, since a busy graph can
put many sequences between two adjacent commits, and the
compass never guesses about names it cannot see, remotes
being other harbors with compasses of their own.
"""

from __future__ import annotations

from keel.errors import Missing
from keel.repo import Repo
from keel.tags import TagStore


def orient(
    repo: Repo,
    address: str,
    tags: TagStore | None = None,
) -> str:
    if address not in repo.graph.commits:
        raise Missing(
            f"{address[:8]} is not a commit here"
        )
    commit = repo.graph.get(address)
    subject = commit.message.splitlines()[0]
    lines = [
        f"orienting {address[:8]} ({subject!r}):"
    ]
    carriers = []
    for branch, tip in sorted(
        repo.refs.branches.items()
    ):
        line = repo.graph.ancestors(tip)
        if address not in line:
            continue
        distance = len(line) - len(
            repo.graph.ancestors(address)
        )
        carriers.append((distance, branch))
    carriers.sort()
    for distance, branch in carriers:
        note = (
            "at the tip"
            if distance == 0
            else f"{distance} commit(s) below the tip"
        )
        lines.append(f"  carried by {branch}, {note}")
    if tags is not None:
        sealing = sorted(
            name
            for name, tag in tags.tags.items()
            if address
            in repo.graph.ancestors(tag.target)
        )
        if sealing:
            lines.append(
                "  part of the era(s) sealed by "
                + ", ".join(sealing)
            )
    if not carriers:
        lines.append(
            "  reachable from no name; wandering, "
            "and the lost and found is where such "
            "commits are shelved"
        )
    return "\n".join(lines)
