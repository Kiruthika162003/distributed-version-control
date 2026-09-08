"""The worklog: history bucketed into windows, each window one sentence.

A log answers what happened; a worklog answers how it has
been going, which is a different question with a different
reader. Commits are bucketed by sequence number into fixed
windows, and each window compresses to the numbers a
standup actually wants: how many commits, how many were
merges, how many distinct paths moved, and which path was
busiest, because the busiest path in a window is usually
the sentence someone would have said aloud. The trend line
at the end compares the last window to the first in plain
multiples and only claims rising or falling past a margin,
since a worklog that calls every wobble a trend teaches
people to stop reading the trend, and steady is a
respectable thing to say about work.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid
from keel.repo import Repo

TREND_MARGIN = 1.5


@dataclass(frozen=True)
class WorkWindow:
    start: int
    end: int
    commits: int
    merges: int
    paths: int
    busiest: str
    busiest_touches: int

    def line(self) -> str:
        detail = (
            f"busiest {self.busiest} "
            f"({self.busiest_touches} touch(es))"
            if self.busiest
            else "no paths moved"
        )
        return (
            f"  window {self.start}-{self.end}: "
            f"{self.commits} commit(s), {self.merges} "
            f"merge(s), {self.paths} path(s), {detail}"
        )


def _touched_paths(repo: Repo, commit) -> list[str]:
    current = repo.files_at(commit.address)
    if not commit.parents:
        return sorted(current)
    parent = repo.files_at(commit.parents[0])
    return sorted(
        path
        for path in set(current) | set(parent)
        if current.get(path) != parent.get(path)
    )


def digest(
    repo: Repo, tip: str, window: int = 5
) -> list[WorkWindow]:
    if window < 1:
        raise Invalid(
            "a window below one buckets nothing; the "
            "worklog needs room to hold a day"
        )
    commits = sorted(
        repo.graph.log(tip),
        key=lambda held: held.sequence,
    )
    buckets: dict[int, list] = {}
    for commit in commits:
        buckets.setdefault(
            commit.sequence // window, []
        ).append(commit)
    windows: list[WorkWindow] = []
    for index in sorted(buckets):
        members = buckets[index]
        touches: dict[str, int] = {}
        for commit in members:
            for path in _touched_paths(repo, commit):
                touches[path] = touches.get(path, 0) + 1
        busiest = ""
        busiest_touches = 0
        if touches:
            busiest = min(
                touches,
                key=lambda path: (-touches[path], path),
            )
            busiest_touches = touches[busiest]
        windows.append(
            WorkWindow(
                start=index * window,
                end=index * window + window - 1,
                commits=len(members),
                merges=sum(
                    1
                    for commit in members
                    if len(commit.parents) > 1
                ),
                paths=len(touches),
                busiest=busiest,
                busiest_touches=busiest_touches,
            )
        )
    return windows


def _trend(windows: list[WorkWindow]) -> str:
    if len(windows) < 2:
        return (
            "one window is a snapshot, not a trend"
        )
    first = windows[0].commits
    last = windows[-1].commits
    if last >= first * TREND_MARGIN:
        return (
            f"the pace is rising: {last} against "
            f"{first} in the first window"
        )
    if first >= last * TREND_MARGIN:
        return (
            f"the pace is falling: {last} against "
            f"{first} in the first window"
        )
    return (
        "steady, which is a respectable thing to say "
        "about work"
    )


def render(
    repo: Repo, tip: str, window: int = 5
) -> str:
    windows = digest(repo, tip, window)
    lines = [
        f"{len(windows)} window(s) of {window}:"
    ]
    lines.extend(held.line() for held in windows)
    lines.append(_trend(windows))
    return "\n".join(lines)
