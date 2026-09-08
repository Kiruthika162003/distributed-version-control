"""The switch guard: changing branches without stepping on the work.

Switching branches with a dirty working copy is the moment
version control eats an afternoon, and the guard makes the
moment boring by sorting the dirt before the move. Dirty
paths that the destination would leave alone travel with
the switch, work in progress riding along the way everyone
expects. Dirty paths the destination would rewrite are the
danger, and the guard shelves exactly those, labeled with
both branch names so the shelf entry explains itself in
three weeks, because a switch that silently overwrites
work is the afternoon, and a switch that refuses outright
teaches people to commit half-thoughts just to move. The
receipt says what traveled and what was shelved by name,
and the clean switch says only that it switched, in the
prompt line's tradition of not narrating the uneventful.
"""

from __future__ import annotations

from keel.errors import Missing
from keel.repo import Repo
from keel.stash import Stash


def switch(
    repo: Repo,
    shelf: Stash,
    working: dict[str, bytes],
    destination: str,
) -> tuple[dict[str, bytes], str]:
    if destination not in repo.refs.branches:
        raise Missing(
            f"{destination} is not a branch here"
        )
    origin = repo.refs.current_branch()
    here = repo.head_files()
    there = repo.files_at(
        repo.refs.branches[destination]
    )
    dirty = sorted(
        path
        for path in set(working) | set(here)
        if working.get(path) != here.get(path)
    )
    endangered = [
        path
        for path in dirty
        if here.get(path) != there.get(path)
    ]
    traveling = [
        path
        for path in dirty
        if path not in endangered
    ]
    shelved_note = ""
    if endangered:
        shelf.push(
            {
                path: working[path]
                for path in endangered
                if path in working
            },
            origin,
            f"switch {origin} -> {destination} "
            "shelved these",
        )
        shelved_note = (
            "; shelved "
            + ", ".join(endangered)
            + " because the destination rewrites "
            "them, and the shelf entry explains "
            "itself in three weeks"
        )
    repo.refs.checkout(destination)
    landed = dict(there)
    for path in traveling:
        if path in working:
            landed[path] = working[path]
        else:
            landed.pop(path, None)
    if not dirty:
        receipt = f"switched to {destination}"
    else:
        receipt = (
            f"switched to {destination}; "
            f"{len(traveling)} dirty path(s) "
            "traveled" + shelved_note
        )
    return landed, receipt
