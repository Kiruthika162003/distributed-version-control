"""Eras: the history cut at its tags and each stretch given its character.

Tags are the repository's own punctuation, and reading the
history as the stretches between them answers the question
raw logs cannot: what was each era about. For every
interval from one seal to the next, the census counts the
commits, the merges, and the paths that moved, then names
the era's protagonist, the path touched most in that
stretch, because eras are remembered by their protagonists
and the file everyone edited is what the era was about
whether the release notes admit it or not. The unfinished
era, tip beyond the last seal, is reported with its count
and called what it is, still being written, and a history
with no tags at all is returned as one nameless era with
the suggestion that punctuation would help, offered once
and not pressed, in the mirror-not-manual tradition.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.tags import TagStore


def _interval_paths(
    repo: Repo, commits: list
) -> dict[str, int]:
    touched: dict[str, int] = {}
    for commit in commits:
        if len(commit.parents) > 1:
            continue
        current = repo.files_at(commit.address)
        parent = (
            repo.files_at(commit.parents[0])
            if commit.parents
            else {}
        )
        for path in set(current) | set(parent):
            if current.get(path) != parent.get(path):
                touched[path] = (
                    touched.get(path, 0) + 1
                )
    return touched


def _describe(
    repo: Repo, name: str, commits: list
) -> str:
    merges = sum(
        1
        for commit in commits
        if len(commit.parents) > 1
    )
    touched = _interval_paths(repo, commits)
    if touched:
        protagonist = min(
            touched,
            key=lambda path: (-touched[path], path),
        )
        hero = (
            f", protagonist {protagonist} "
            f"({touched[protagonist]} touch(es))"
        )
    else:
        hero = ", no paths moved"
    return (
        f"  {name}: {len(commits)} commit(s), "
        f"{merges} merge(s){hero}"
    )


def chronicle(
    repo: Repo, tags: TagStore
) -> str:
    tip = repo.refs.current()
    line = sorted(
        repo.graph.log(tip),
        key=lambda commit: commit.sequence,
    )
    if not tags.tags:
        return "\n".join(
            [
                "one nameless era of "
                f"{len(line)} commit(s); punctuation "
                "would help, offered once and not "
                "pressed",
            ]
        )
    seals = sorted(
        (
            (
                repo.graph.get(tag.target).sequence,
                name,
            )
            for name, tag in tags.tags.items()
        ),
    )
    lines = ["the eras, cut at the seals:"]
    start = 0
    previous_name = "the founding"
    for sequence, name in seals:
        interval = [
            commit
            for commit in line
            if start <= commit.sequence <= sequence
        ]
        lines.append(
            _describe(
                repo,
                f"{previous_name} -> {name}",
                interval,
            )
        )
        start = sequence + 1
        previous_name = name
    unfinished = [
        commit
        for commit in line
        if commit.sequence >= start
    ]
    if unfinished:
        lines.append(
            _describe(
                repo,
                f"{previous_name} -> now",
                unfinished,
            )
            + "; still being written"
        )
    return "\n".join(lines)
