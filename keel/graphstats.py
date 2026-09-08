"""Graph statistics: the shape of a history, measured and then named.

Two repositories with a thousand commits each can hold
completely different stories, one a railway of rebased
work, one a braided river of merges, and the difference is
readable from four numbers no log ever prints. The census
walks everything reachable from a tip and counts commits,
merges, roots, and branch points, then measures the longest
linear run, the stretch of single-parent commits nobody
merged into, because that run is where bisect will be fast
and blame will be boring, and both of those are compliments.
The verdicts at the end are earned by thresholds stated in
the code rather than vibes: merge density above a fifth
reads as braided, a linear run covering most of the history
reads as a railway, and a history with several roots gets
called what it is, a federation, since pretending unrelated
lines are one story is how archaeology digs into the wrong
city.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Missing
from keel.repo import Repo

BRAIDED_DENSITY = 0.2
RAILWAY_SHARE = 0.6


@dataclass(frozen=True)
class GraphShape:
    commits: int
    merges: int
    roots: int
    branch_points: int
    longest_linear_run: int

    def merge_density(self) -> float:
        if not self.commits:
            return 0.0
        return self.merges / self.commits

    def verdicts(self) -> list[str]:
        found = []
        if self.merge_density() > BRAIDED_DENSITY:
            found.append(
                "a braided river; merges carry a fifth or "
                "more of the story"
            )
        if (
            self.commits
            and self.longest_linear_run / self.commits
            >= RAILWAY_SHARE
        ):
            found.append(
                "a railway; most of the history is one "
                "straight run, where bisect is fast and "
                "blame is boring, both compliments"
            )
        if self.roots > 1:
            found.append(
                f"a federation of {self.roots} unrelated "
                "beginnings; dig each city separately"
            )
        if not found:
            found.append(
                "an unremarkable shape, which no working "
                "repository should be ashamed of"
            )
        return found


def measure(repo: Repo, tip: str) -> GraphShape:
    reachable = repo.graph.ancestors(tip)
    if not reachable:
        raise Missing("nothing reachable; no shape to name")
    children: dict[str, int] = {}
    merges = 0
    roots = 0
    for address in reachable:
        commit = repo.graph.get(address)
        if len(commit.parents) > 1:
            merges += 1
        if not commit.parents:
            roots += 1
        for parent in commit.parents:
            if parent in reachable:
                children[parent] = (
                    children.get(parent, 0) + 1
                )
    branch_points = sum(
        1 for count in children.values() if count > 1
    )
    longest = 0
    for address in reachable:
        commit = repo.graph.get(address)
        if len(commit.parents) == 1 and (
            children.get(commit.parents[0], 0) == 1
        ):
            continue
        run = 1
        cursor = address
        while (
            children.get(cursor, 0) == 1
        ):
            child = next(
                candidate
                for candidate in reachable
                if cursor
                in repo.graph.get(candidate).parents
            )
            if len(repo.graph.get(child).parents) != 1:
                break
            run += 1
            cursor = child
        longest = max(longest, run)
    return GraphShape(
        commits=len(reachable),
        merges=merges,
        roots=roots,
        branch_points=branch_points,
        longest_linear_run=longest,
    )


def narrate(repo: Repo, tip: str) -> str:
    shape = measure(repo, tip)
    lines = [
        f"{shape.commits} commit(s), {shape.merges} "
        f"merge(s), {shape.roots} root(s), "
        f"{shape.branch_points} branch point(s), "
        f"longest linear run {shape.longest_linear_run}"
    ]
    lines.extend(
        f"  {verdict}" for verdict in shape.verdicts()
    )
    return "\n".join(lines)
