"""Code age: how old the tip's lines are, counted in the repo's own clock.

A file's age is not when it was created but when its lines
last changed, and the census reads that truth from blame:
every surviving line is dated by the sequence number of the
commit that wrote it, ages measured against the tip in the
only clock this history trusts. The verdicts are relative
to the repository's own span rather than absolute numbers,
old growth for files whose average line predates most of
the history, fresh paint for files mostly written in the
newest stretch, because a six-month-old line is ancient in
a year-old repository and newborn in a decade-old one, and
a census that ignores the denominator flatters every young
repo as stable. Old growth is read as a compliment with a
caveat attached: unchanged can mean finished or it can
mean feared, and blame cannot tell those apart, only the
next person to edit it can.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.blame import blame
from keel.repo import Repo

OLD_GROWTH_SHARE = 0.66
FRESH_PAINT_SHARE = 0.2


@dataclass(frozen=True)
class FileAge:
    path: str
    lines: int
    average_age: float
    oldest: int
    newest: int

    def verdict(self, span: int) -> str:
        if span == 0:
            return "newborn repository; everything ages together"
        share = self.average_age / span
        if share >= OLD_GROWTH_SHARE:
            return (
                "old growth; finished or feared, and "
                "only the next editor can tell"
            )
        if share <= FRESH_PAINT_SHARE:
            return "fresh paint"
        return "settled"

    def line(self, span: int) -> str:
        return (
            f"  {self.path}: {self.lines} line(s), "
            f"average age {self.average_age:.1f} of "
            f"{span}, oldest {self.oldest}, newest "
            f"{self.newest}; {self.verdict(span)}"
        )


def age_census(
    repo: Repo, tip: str
) -> list[FileAge]:
    now = repo.graph.get(tip).sequence
    found: list[FileAge] = []
    for path in sorted(repo.files_at(tip)):
        rows = blame(repo, tip, path)
        if not rows:
            continue
        ages = [
            now - repo.graph.get(row.commit).sequence
            for row in rows
        ]
        found.append(
            FileAge(
                path=path,
                lines=len(ages),
                average_age=sum(ages) / len(ages),
                oldest=max(ages),
                newest=min(ages),
            )
        )
    found.sort(
        key=lambda held: (-held.average_age, held.path)
    )
    return found


def report(repo: Repo, tip: str) -> str:
    census = age_census(repo, tip)
    span = repo.graph.get(tip).sequence
    lines = [
        f"line ages against a span of {span}:"
    ]
    lines.extend(held.line(span) for held in census)
    total_lines = sum(held.lines for held in census)
    if total_lines and span:
        fresh = sum(
            held.lines
            for held in census
            if held.average_age / span
            <= FRESH_PAINT_SHARE
        )
        lines.append(
            f"{fresh} of {total_lines} line(s) live in "
            "fresh paint; the denominator is the "
            "repo's own life, not the calendar"
        )
    return "\n".join(lines)
