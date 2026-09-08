"""The frontier: when the fleet last agreed, and how far each ship sailed.

With two branches the merge base answers everything; with
five, the question becomes the fleet's, and the frontier
answers it in two parts. The last accord first: the newest
commit every listed branch still counts as an ancestor,
found by intersecting ancestries and taking the highest
sequence, because the deepest common point is where any
all-hands integration would stand, and a fleet that cannot
name that point is guessing at the size of its own
reunion. Then the distances: each branch's private commit
count beyond the accord, sorted farthest first, since the
ship farthest from the accord is the one whose return
costs the most and the one the schedule should hear about
first. A fleet with no common ancestor at all is reported
as squadrons, not a fleet, each group named, because
pretending strangers share a harbor plans a reunion nobody
can attend.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo


def last_accord(
    repo: Repo, branches: list[str]
) -> str | None:
    common: set[str] | None = None
    for branch in branches:
        tip = repo.refs.branches.get(branch)
        if tip is None:
            raise Invalid(
                f"{branch} is not a branch here"
            )
        line = repo.graph.ancestors(tip)
        common = (
            line if common is None else common & line
        )
    if not common:
        return None
    return max(
        common,
        key=lambda address: repo.graph.get(
            address
        ).sequence,
    )


def report(repo: Repo, branches: list[str]) -> str:
    if len(branches) < 2:
        raise Invalid(
            "a frontier needs at least two ships"
        )
    accord = last_accord(repo, branches)
    if accord is None:
        squadrons: list[set[str]] = []
        for branch in branches:
            line = repo.graph.ancestors(
                repo.refs.branches[branch]
            )
            for squadron in squadrons:
                sample = next(iter(squadron))
                if line & repo.graph.ancestors(
                    repo.refs.branches[sample]
                ):
                    squadron.add(branch)
                    break
            else:
                squadrons.append({branch})
        described = "; ".join(
            ", ".join(sorted(squadron))
            for squadron in squadrons
        )
        return (
            f"not a fleet but {len(squadrons)} "
            f"squadron(s): {described}; pretending "
            "strangers share a harbor plans a "
            "reunion nobody can attend"
        )
    accord_commit = repo.graph.get(accord)
    accord_line = repo.graph.ancestors(accord)
    lines = [
        f"the last accord: {accord[:8]} "
        f"({accord_commit.message.splitlines()[0]!r}, "
        f"seq {accord_commit.sequence})"
    ]
    distances = []
    for branch in branches:
        private = len(
            repo.graph.ancestors(
                repo.refs.branches[branch]
            )
            - accord_line
        )
        distances.append((private, branch))
    distances.sort(key=lambda held: (-held[0], held[1]))
    for private, branch in distances:
        note = (
            "still at the accord"
            if private == 0
            else f"{private} commit(s) out"
        )
        lines.append(f"  {branch}: {note}")
    farthest, name = distances[0]
    if farthest:
        lines.append(
            f"{name} sails farthest; its return "
            "costs the most and the schedule should "
            "hear about it first"
        )
    return "\n".join(lines)
