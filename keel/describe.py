"""Describe: name any commit by the nearest tag behind it, plus the distance.

Humans do not navigate by digest; they navigate by release,
and describe turns an arbitrary commit into the sentence
people actually say: two commits past v1.4. The walk follows
first parents backward until it meets a tagged commit, and
the render carries three parts, tag, distance, and short
address, because each answers a different question: the tag
says which era, the distance says how far into it, and the
address makes the whole string resolvable again, so a
describe pasted into a bug report is a coordinate, not a
vibe. A commit with no tagged ancestor is named by its
address alone with the situation stated, since inventing a
distance from nothing would make every young repository
describe itself confidently and wrongly.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.tags import TagStore


def describe(
    repo: Repo, tags: TagStore, address: str
) -> str:
    tagged_at: dict[str, str] = {}
    for name in tags.tags:
        tagged_at[tags.resolve(name)] = name
    distance = 0
    cursor: str | None = address
    while cursor is not None:
        if cursor in tagged_at:
            tag = tagged_at[cursor]
            if distance == 0:
                return f"exactly {tag}"
            return (
                f"{tag}+{distance} ({address[:8]}); the tag "
                "says which era, the distance says how far "
                "into it"
            )
        commit = repo.graph.get(cursor)
        cursor = (
            commit.parents[0] if commit.parents else None
        )
        distance += 1
    return (
        f"{address[:8]} with no tagged ancestor; a distance "
        "invented from nothing would describe confidently "
        "and wrongly"
    )


def describe_head(repo: Repo, tags: TagStore) -> str:
    return describe(repo, tags, repo.refs.current())
