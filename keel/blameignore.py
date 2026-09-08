"""Blame with ignored revisions: the reformat commit does not get the credit.

The day the formatter runs over the whole tree, every line's
blame changes to the person who pressed the button, and from
then on the tool answers the wrong question forever: who
reformatted, not who wrote. The ignore list names the
revisions blame should see through, and for any line those
commits would claim, the walk continues past them to the
author underneath, with the seen-through commit recorded in
the answer, because transparency about the detour is what
separates seeing through from covering up. The list is
policy, not heuristics: nothing lands on it automatically,
since a tool that guesses which commits are cosmetic will
eventually see through a real change, and a blame that skips
a real change is corruption with a good excuse.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.blame import blame
from keel.errors import Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class SeenThroughLine:
    line_number: int
    text: str
    credited: str
    seen_through: tuple[str, ...]

    def render(self, repo: Repo) -> str:
        credit = repo.graph.get(self.credited)
        base = (
            f"{self.line_number:>3} {self.credited[:8]} "
            f"{credit.message[:30]}: {self.text}"
        )
        if self.seen_through:
            detours = ", ".join(
                address[:8]
                for address in self.seen_through
            )
            base += f" (seen through {detours})"
        return base


def blame_with_ignores(
    repo: Repo,
    start: str,
    path: str,
    ignored: set[str],
) -> list[SeenThroughLine]:
    for address in ignored:
        repo.graph.get(address)
    lines = blame(repo, start, path)
    results: list[SeenThroughLine] = []
    for entry in lines:
        credited = entry.commit
        detours: list[str] = []
        while credited in ignored:
            detours.append(credited)
            commit = repo.graph.get(credited)
            if not commit.parents:
                break
            parent = commit.parents[0]
            parent_lines = {
                line.text.strip(): line.commit
                for line in blame(repo, parent, path)
            }
            underneath = parent_lines.get(entry.text.strip())
            if underneath is None or underneath == credited:
                break
            credited = underneath
        results.append(
            SeenThroughLine(
                line_number=entry.line_number,
                text=entry.text,
                credited=credited,
                seen_through=tuple(detours),
            )
        )
    return results


def ignore_list_policy(candidates: list[str]) -> str:
    if not candidates:
        raise Invalid(
            "an empty ignore list needs no policy statement"
        )
    return (
        f"{len(candidates)} revision(s) listed by hand; "
        "nothing lands here automatically, because a tool "
        "that guesses which commits are cosmetic will "
        "eventually see through a real change, and a blame "
        "that skips a real change is corruption with a good "
        "excuse"
    )
