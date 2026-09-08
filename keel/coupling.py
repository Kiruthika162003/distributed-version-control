"""Coupling: files that change together are married, whatever the imports say.

Static analysis reads declarations; history reads behavior,
and the couple report is behavior distilled: for every pair
of files, how often did they change in the same commit,
scored against the quieter partner's total so a chatty file
cannot drown its marriages in noise. The floor and the
minimum are parameters with teeth, a pair below the count
floor is an anecdote and a pair below the rate floor is a
coincidence, and both words appear in the refusals because
they are the exact words reviewers use to dismiss the
report before it earns its first save. The cross-house note
is the finding that pays for the module: two files married
across directory boundaries mean the boundary is drawn
where the work is not, and every architecture diagram that
ignores a standing marriage is a map of a city that
photographs differently from orbit.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from keel.errors import Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class Marriage:
    left: str
    right: str
    together: int
    rate: float

    def line(self) -> str:
        note = ""
        left_house = self.left.split("/")[0]
        right_house = self.right.split("/")[0]
        if left_house != right_house:
            note = (
                "; a marriage across two houses, the "
                "boundary is drawn where the work is not"
            )
        return (
            f"  {self.left} + {self.right}: together "
            f"{self.together} time(s), "
            f"{self.rate:.0%} of the quieter one"
            f"{note}"
        )


def _touched(repo: Repo, commit) -> list[str]:
    if len(commit.parents) > 1:
        return []
    current = repo.files_at(commit.address)
    if commit.parents:
        parent = repo.files_at(commit.parents[0])
    else:
        parent = {}
    return sorted(
        path
        for path in set(current) | set(parent)
        if current.get(path) != parent.get(path)
    )


def measure(
    repo: Repo,
    tip: str,
    rate_floor: float = 0.6,
    count_floor: int = 3,
) -> list[Marriage]:
    if not 0 < rate_floor <= 1:
        raise Invalid(
            "the rate floor is a fraction in (0, 1]; "
            "below it lives coincidence"
        )
    if count_floor < 2:
        raise Invalid(
            "a count floor below two certifies "
            "anecdotes"
        )
    touches: dict[str, int] = {}
    pairs: dict[tuple[str, str], int] = {}
    for commit in repo.graph.log(tip):
        moved = _touched(repo, commit)
        for path in moved:
            touches[path] = touches.get(path, 0) + 1
        for left, right in combinations(moved, 2):
            pairs[(left, right)] = (
                pairs.get((left, right), 0) + 1
            )
    marriages = []
    for (left, right), together in pairs.items():
        if together < count_floor:
            continue
        quieter = min(touches[left], touches[right])
        rate = together / quieter
        if rate >= rate_floor:
            marriages.append(
                Marriage(
                    left=left,
                    right=right,
                    together=together,
                    rate=rate,
                )
            )
    marriages.sort(
        key=lambda held: (-held.rate, -held.together)
    )
    return marriages


def report(
    repo: Repo,
    tip: str,
    rate_floor: float = 0.6,
    count_floor: int = 3,
) -> str:
    marriages = measure(
        repo, tip, rate_floor, count_floor
    )
    if not marriages:
        return (
            "no marriages above the floor; the files "
            "live single lives"
        )
    lines = [
        f"{len(marriages)} marriage(s) above "
        f"{rate_floor:.0%} with at least "
        f"{count_floor} co-change(s):"
    ]
    lines.extend(
        marriage.line() for marriage in marriages
    )
    return "\n".join(lines)
