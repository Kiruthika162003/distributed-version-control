"""The wake: everything downstream of a commit, counted before rewriting.

Ancestry is the question tools answer by habit; the wake is
the other direction, every commit that builds on this one,
and it is the number that prices a rewrite, because
re-addressing one commit re-addresses its entire wake and
the wake is what every fork, clone, and colleague is
standing on. The census walks the graph once and inverts
the parent arrows, then answers per commit: the wake's
size, the branch tips riding in it, and the verdict in
plain terms, safe to rewrite when the wake is empty and
priced in re-addressed commits when it is not, with the
riding branches named because a wake with three branch
tips in it is three conversations to have before any
history moves. The root's wake is the whole repository,
which the report states as the reason roots are rewritten
only by people who enjoy migrations.
"""

from __future__ import annotations

from keel.errors import Missing
from keel.repo import Repo


def _children_map(
    repo: Repo,
) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    for address, commit in repo.graph.commits.items():
        for parent in commit.parents:
            children.setdefault(parent, []).append(
                address
            )
    return children


def wake_of(repo: Repo, address: str) -> set[str]:
    if address not in repo.graph.commits:
        raise Missing(
            f"{address[:8]} is not a commit here"
        )
    children = _children_map(repo)
    found: set[str] = set()
    frontier = [address]
    while frontier:
        current = frontier.pop()
        for child in children.get(current, []):
            if child not in found:
                found.add(child)
                frontier.append(child)
    return found


def report(repo: Repo, address: str) -> str:
    wake = wake_of(repo, address)
    commit = repo.graph.get(address)
    subject = commit.message.splitlines()[0]
    riding = sorted(
        branch
        for branch, tip in repo.refs.branches.items()
        if tip in wake or tip == address
    )
    lines = [
        f"the wake of {address[:8]} ({subject!r}): "
        f"{len(wake)} commit(s)"
    ]
    if not wake:
        lines.append(
            "empty; safe to rewrite, nobody is "
            "standing downstream"
        )
    else:
        lines.append(
            f"a rewrite re-addresses all "
            f"{len(wake)}; the wake is what every "
            "fork, clone, and colleague stands on"
        )
    if riding:
        lines.append(
            "branch tips riding in it: "
            + ", ".join(riding)
            + "; each one a conversation before any "
            "history moves"
        )
    if not commit.parents and wake:
        lines.append(
            "this is a root; its wake is the whole "
            "repository, which is why roots are "
            "rewritten only by people who enjoy "
            "migrations"
        )
    return "\n".join(lines)
