"""Twins: identical bytes under different names, found and questioned.

The store deduplicates content by address, so two paths
holding the same bytes cost nothing at rest and everything
in maintenance: the fix applied to one twin and not the
other is the bug that comes back with an alibi. The census
walks the tip and groups paths by content address, which
makes detection exact and free, no similarity floors, no
guessing, just the store's own arithmetic read back out.
Every family is reported with a question rather than an
order, deliberate copies exist, the license text, the
fixture that must not drift by design, and the census
cannot tell devotion from neglect, but near-twins found by
a one-line difference are flagged harder, because a
ninety-nine percent copy is never a design decision, it is
a fork that has already started drifting and picked up
speed.
"""

from __future__ import annotations

from keel.renames import line_similarity
from keel.repo import Repo

NEAR_TWIN_FLOOR = 0.9


def twin_families(
    repo: Repo, tip: str
) -> list[list[str]]:
    files = repo.files_at(tip)
    by_content: dict[bytes, list[str]] = {}
    for path in sorted(files):
        by_content.setdefault(files[path], []).append(
            path
        )
    return sorted(
        family
        for family in by_content.values()
        if len(family) > 1
    )


def near_twins(
    repo: Repo, tip: str
) -> list[tuple[str, str, float]]:
    files = repo.files_at(tip)
    paths = sorted(files)
    found = []
    for index, left in enumerate(paths):
        for right in paths[index + 1:]:
            if files[left] == files[right]:
                continue
            score = line_similarity(
                files[left], files[right]
            )
            if score >= NEAR_TWIN_FLOOR:
                found.append(
                    (left, right, round(score, 2))
                )
    return found


def report(repo: Repo, tip: str) -> str:
    families = twin_families(repo, tip)
    nears = near_twins(repo, tip)
    if not families and not nears:
        return (
            "no twins at the tip; every path speaks "
            "for itself"
        )
    lines = [
        f"{len(families)} exact famil(ies), "
        f"{len(nears)} near-twin pair(s):"
    ]
    for family in families:
        lines.append(
            "  identical: "
            + " = ".join(family)
            + "; devotion or neglect, the census "
            "cannot tell, but a fix applied to one "
            "and not the other comes back with an "
            "alibi"
        )
    for left, right, score in nears:
        lines.append(
            f"  drifting: {left} ~ {right} "
            f"({score:.0%}); a ninety-nine percent "
            "copy is a fork that has already picked "
            "up speed"
        )
    return "\n".join(lines)
