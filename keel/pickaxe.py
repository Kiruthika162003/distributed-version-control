"""Pickaxe: when did this string enter the codebase, and when did it leave.

Some questions are about lines and belong to blame; others
are about survival, when did this function name first appear,
when did the last caller of this API vanish, and those belong
to the pickaxe. It walks a first-parent line counting
occurrences of the needle in every snapshot, and flags the
commits where the count changed, split by direction, because
introductions and removals answer different questions: the
introduction is where the archaeology starts, the removal is
where the cleanup finished, and a commit that moved text
without changing the count is invisible to the pickaxe on
purpose, since moves are the noise this tool exists to
filter. The count rides along in every finding, so "removed
the last two callers" reads differently from "removed two of
forty", which is the difference between a cleanup and a dent.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class PickaxeHit:
    address: str
    message: str
    direction: str
    count_before: int
    count_after: int

    def line(self) -> str:
        return (
            f"{self.address[:8]} {self.message}: "
            f"{self.direction} ({self.count_before} -> "
            f"{self.count_after})"
        )


def _count_needle(
    repo: Repo, address: str, needle: bytes
) -> int:
    total = 0
    for content in repo.files_at(address).values():
        total += content.count(needle)
    return total


def pickaxe(
    repo: Repo, start: str, needle: bytes
) -> list[PickaxeHit]:
    if not needle.strip():
        raise Invalid(
            "an empty needle matches everything and answers "
            "nothing"
        )
    hits: list[PickaxeHit] = []
    cursor: str | None = start
    while cursor is not None:
        commit = repo.graph.get(cursor)
        own_count = _count_needle(repo, cursor, needle)
        if commit.parents:
            parent_count = _count_needle(
                repo, commit.parents[0], needle
            )
        else:
            parent_count = 0
        if own_count != parent_count:
            direction = (
                "introduced"
                if own_count > parent_count
                else "removed"
            )
            hits.append(
                PickaxeHit(
                    address=cursor,
                    message=commit.message,
                    direction=direction,
                    count_before=parent_count,
                    count_after=own_count,
                )
            )
        cursor = (
            commit.parents[0] if commit.parents else None
        )
    return hits


def survival_story(
    repo: Repo, start: str, needle: bytes
) -> str:
    hits = pickaxe(repo, start, needle)
    if not hits:
        return (
            f"{needle.decode(errors='replace')!r} never "
            "changed count on this line of history; either "
            "it was always here or it never was"
        )
    current = _count_needle(repo, start, needle)
    lines = [
        f"{needle.decode(errors='replace')!r}: "
        f"{len(hits)} count change(s), "
        f"{current} occurrence(s) today"
    ]
    lines.extend(hit.line() for hit in hits)
    if current == 0:
        lines.append(
            "the needle is gone; the newest removal above "
            "is where the cleanup finished"
        )
    return "\n".join(lines)
