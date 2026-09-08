"""Lifespans: every path gets a biography, and the graveyard keeps names.

Blame answers who touched a line; nobody answers when a
file was born, when it died, and whether it came back, yet
that is the first question in every deletion argument. The
chronicle walks the first-parent line once and files three
kinds of event: born when a path first appears, died when
it vanishes from the snapshot, reborn when it returns, each
stamped with the commit and its message, because a death
certificate without a cause is a rumor with a date. The
graveyard is the census's useful half: paths currently
dead, each with the commit that buried it, so the argument
about whether deleting utils.py was discussed can be
settled by reading what the burying commit actually said.
Asking about a path that never lived is answered plainly
rather than with an empty list, since an empty list reads
as a file with no history and those are different claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Missing
from keel.repo import Repo


@dataclass(frozen=True)
class LifeEvent:
    kind: str
    address: str
    message: str

    def line(self) -> str:
        subject = self.message.splitlines()[0]
        return (
            f"{self.kind} in {self.address[:8]} "
            f"({subject})"
        )


def chronicle(
    repo: Repo, tip: str
) -> dict[str, list[LifeEvent]]:
    chain = []
    cursor = tip
    while True:
        commit = repo.graph.get(cursor)
        chain.append(commit)
        if not commit.parents:
            break
        cursor = commit.parents[0]
    chain.reverse()
    events: dict[str, list[LifeEvent]] = {}
    previous: set[str] = set()
    for commit in chain:
        current = set(repo.files_at(commit.address))
        for path in sorted(current - previous):
            kind = (
                "reborn" if path in events else "born"
            )
            events.setdefault(path, []).append(
                LifeEvent(
                    kind=kind,
                    address=commit.address,
                    message=commit.message,
                )
            )
        for path in sorted(previous - current):
            events[path].append(
                LifeEvent(
                    kind="died",
                    address=commit.address,
                    message=commit.message,
                )
            )
        previous = current
    return events


def biography(repo: Repo, tip: str, path: str) -> str:
    events = chronicle(repo, tip).get(path)
    if events is None:
        raise Missing(
            f"{path} never lived on this line; no "
            "history is a different claim than an "
            "empty one"
        )
    state = (
        "living"
        if events[-1].kind != "died"
        else "dead"
    )
    parts = ", ".join(event.line() for event in events)
    return f"{path}: {parts}; currently {state}"


def graveyard(repo: Repo, tip: str) -> str:
    dead = {
        path: events[-1]
        for path, events in chronicle(repo, tip).items()
        if events[-1].kind == "died"
    }
    if not dead:
        return "the graveyard is empty; everything lives"
    lines = [f"{len(dead)} path(s) at rest:"]
    for path in sorted(dead):
        burial = dead[path]
        lines.append(
            f"  {path}, buried by {burial.address[:8]} "
            f"({burial.message.splitlines()[0]})"
        )
    return "\n".join(lines)


def census(repo: Repo, tip: str) -> str:
    events = chronicle(repo, tip)
    living = sum(
        1
        for held in events.values()
        if held[-1].kind != "died"
    )
    dead = len(events) - living
    resurrected = sum(
        1
        for held in events.values()
        if any(event.kind == "reborn" for event in held)
    )
    return (
        f"{len(events)} path(s) ever lived: {living} "
        f"living, {dead} dead, {resurrected} came back "
        "at least once"
    )
