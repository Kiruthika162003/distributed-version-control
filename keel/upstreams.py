"""Upstreams: every branch knows whom it follows, and nobody follows a circle.

Ahead and behind are meaningless numbers until the other
side has a name, and the tracking table is where the name
lives: each branch may follow one upstream, comparisons
read the table instead of making the caller retype the
pairing, and a branch that follows nobody says so rather
than defaulting to whatever the tool author's workflow
was. The table refuses the two degenerate shapes at write
time: following yourself, which makes every status report
a mirror admiring itself, and following in a circle, which
turns the innocent question who is upstream of whom into a
walk that never comes home. The status verbs are borrowed
from the remote divergence report on purpose, current,
ahead, behind, diverged, because a developer should not
need two vocabularies for the same four situations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass
class Tracking:
    repo: Repo
    follows: dict[str, str] = field(default_factory=dict)

    def _known(self, branch: str) -> None:
        if branch not in self.repo.refs.branches:
            raise Missing(
                f"{branch} is not a branch here"
            )

    def follow(self, branch: str, upstream: str) -> str:
        self._known(branch)
        self._known(upstream)
        if branch == upstream:
            raise Invalid(
                f"{branch} cannot follow itself; that "
                "status report is a mirror admiring "
                "itself"
            )
        cursor = upstream
        walked = [branch]
        while cursor in self.follows:
            walked.append(cursor)
            cursor = self.follows[cursor]
            if cursor == branch:
                chain = " -> ".join(
                    [*walked, cursor]
                )
                raise Invalid(
                    f"circle refused: {chain}; who is "
                    "upstream of whom becomes a walk "
                    "that never comes home"
                )
        self.follows[branch] = upstream
        return f"{branch} now follows {upstream}"

    def unfollow(self, branch: str) -> str:
        if branch not in self.follows:
            raise Missing(
                f"{branch} follows nobody already"
            )
        former = self.follows.pop(branch)
        return f"{branch} no longer follows {former}"

    def status(self, branch: str) -> str:
        self._known(branch)
        upstream = self.follows.get(branch)
        if upstream is None:
            return (
                f"{branch} follows nobody; ahead and "
                "behind need a named other"
            )
        ours = self.repo.graph.ancestors(
            self.repo.refs.branches[branch]
        )
        theirs = self.repo.graph.ancestors(
            self.repo.refs.branches[upstream]
        )
        ahead = len(ours - theirs)
        behind = len(theirs - ours)
        if ahead == 0 and behind == 0:
            return f"{branch}: current with {upstream}"
        if behind == 0:
            return (
                f"{branch}: ahead of {upstream} by "
                f"{ahead}"
            )
        if ahead == 0:
            return (
                f"{branch}: behind {upstream} by "
                f"{behind}"
            )
        return (
            f"{branch}: diverged from {upstream}, "
            f"ahead {ahead} behind {behind}"
        )

    def report(self) -> str:
        lines = []
        for branch in sorted(self.repo.refs.branches):
            lines.append(f"  {self.status(branch)}")
        return "\n".join(
            [f"{len(lines)} branch(es):", *lines]
        )
