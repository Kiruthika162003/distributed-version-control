"""Catch-up: everything since you last looked, sized for one coffee.

Coming back from two weeks away, the question is not what
happened, it is what do I need to know, and the catch-up
answers it from a single anchor: the address you last stood
on. Everything since is summarized in the order a returning
person triages, the headline count first, then where the
motion landed by directory, then the subjects of the newest
few commits because recency is relevance after an absence,
then the branches and tags that appeared while you were
gone, each a conversation that started without you. An
anchor the repository does not recognize is refused rather
than guessed around, since a catch-up from the wrong
anchor is confidently wrong about everything, and the
anchor that IS the tip gets the shortest page of all:
nothing happened, you were never really gone.
"""

from __future__ import annotations

from keel.dirstat import render as dirstat_render
from keel.errors import Missing
from keel.repo import Repo
from keel.tags import TagStore

RECENT = 5


def catch_up(
    repo: Repo,
    last_seen: str,
    known_branches: set[str] | None = None,
    tags: TagStore | None = None,
) -> str:
    if last_seen not in repo.graph.commits:
        raise Missing(
            f"{last_seen[:8]} is not a commit here; a "
            "catch-up from the wrong anchor is "
            "confidently wrong about everything"
        )
    tip = repo.refs.current()
    if last_seen == tip:
        return (
            "nothing happened; you were never really "
            "gone"
        )
    fresh = [
        commit
        for commit in repo.graph.log(tip)
        if commit.sequence
        > repo.graph.get(last_seen).sequence
    ]
    lines = [
        f"since {last_seen[:8]}: {len(fresh)} "
        "commit(s), sized for one coffee"
    ]
    lines.append(dirstat_render(repo, last_seen, tip))
    recent = fresh[:RECENT]
    lines.append(
        f"the newest {len(recent)} subject(s), "
        "recency being relevance after an absence:"
    )
    lines.extend(
        f"  {commit.address[:8]} "
        f"{commit.message.splitlines()[0]}"
        for commit in recent
    )
    if known_branches is not None:
        arrived = sorted(
            set(repo.refs.branches) - known_branches
        )
        if arrived:
            lines.append(
                "branches that appeared while you "
                "were gone: "
                + ", ".join(arrived)
                + "; each a conversation that started "
                "without you"
            )
        else:
            lines.append(
                "no new branches; the conversations "
                "are the ones you left"
            )
    if tags is not None:
        placed = sorted(
            name
            for name, tag in tags.tags.items()
            if repo.graph.get(tag.target).sequence
            > repo.graph.get(last_seen).sequence
        )
        if placed:
            lines.append(
                "sealed while you were gone: "
                + ", ".join(placed)
            )
    return "\n".join(lines)
