"""The factsheet: what this repository is, in numbers it cannot fake.

Descriptions drift and numbers audited at read time do not,
so the factsheet is computed on request from the objects
themselves: commits and merges from the graph, branches and
the reflog's depth from the ref table, files and bytes from
the tip's tree, tags from the store that seals them. When
the wider workshop is offered, the sheet counts it too, the
organs from the registry that reads docstrings and the
witnesses from the roster that runs measurements, because a
project that ships instruments should count its instruments
with one of them. Every line is a number and a noun, no
adjectives, since the reader who wants adjectives can
derive their own from the numbers, which is the entire
difference between a factsheet and a brochure.
"""

from __future__ import annotations

from keel.organs import roster
from keel.repo import Repo
from keel.tags import TagStore
from keel.witnesses import registry


def facts(
    repo: Repo,
    tags: TagStore | None = None,
    count_workshop: bool = False,
) -> str:
    tip = repo.refs.current()
    commits = repo.graph.log(tip)
    merges = sum(
        1
        for commit in commits
        if len(commit.parents) > 1
    )
    files = repo.files_at(tip)
    lines = [
        "the factsheet, computed on request:",
        f"  {len(commits)} commit(s), {merges} of "
        "them merges",
        f"  {len(repo.refs.branches)} branch(es), "
        f"{len(repo.refs.reflog)} reflog entr(ies)",
        f"  {len(files)} file(s), "
        f"{sum(len(c) for c in files.values())} "
        "byte(s) at the tip",
        f"  {len(repo.store.objects)} object(s) in "
        "the store",
    ]
    if tags is not None:
        lines.append(f"  {len(tags.tags)} tag(s) sealed")
    if count_workshop:
        lines.append(
            f"  {len(roster())} organ(s) on the "
            "registry"
        )
        lines.append(
            f"  {len(registry.WITNESSES)} witness(es) "
            "on the roster"
        )
    lines.append(
        "numbers and nouns only; the reader who "
        "wants adjectives can derive their own, "
        "which is the difference between a factsheet "
        "and a brochure"
    )
    return "\n".join(lines)
