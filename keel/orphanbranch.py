"""Orphan branches: a second history under one roof, married only on purpose.

Some work shares a repository without sharing a past, the
documentation site, the deployment manifests, the generated
API reference, and an orphan branch gives it a root of its
own: a commit with no parents, started while other branches
exist, so the two histories are strangers by construction
and the merge machinery says so if anyone asks. The marriage
exists but is ceremonial on purpose: adoption merges two
strangers by declaring an empty base, taking the union of
their files, and refusing the union the moment both sides
claim a path with different bytes, because with no common
ancestor there is no third text to consult and any automatic
choice is a coin flip wearing a robe. The refusal lists
every contested path at once rather than one per attempt,
since a marriage negotiated one argument at a time is how
integrations take a week.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Conflict, Invalid
from keel.repo import Repo


def create_orphan(
    repo: Repo,
    name: str,
    files: dict[str, bytes],
    message: str,
) -> Commit:
    if name in repo.refs.branches:
        raise Invalid(
            f"{name} already exists; an orphan needs a "
            "name nobody answers to"
        )
    if not files:
        raise Invalid(
            "an orphan with no files is a name for "
            "nothing; give it a body"
        )
    tree = repo.snapshot_tree(files)
    commit = repo.graph.create(
        tree=tree, parents=(), message=message
    )
    repo.refs.create_branch(name, commit.address)
    return commit


def are_strangers(
    repo: Repo, left: str, right: str
) -> bool:
    return not (
        repo.graph.ancestors(left)
        & repo.graph.ancestors(right)
    )


def adopt(
    repo: Repo,
    ours: str,
    theirs: str,
    message: str,
) -> Commit:
    ours_tip = repo.refs.branches.get(ours)
    theirs_tip = repo.refs.branches.get(theirs)
    if ours_tip is None or theirs_tip is None:
        raise Invalid(
            "adoption needs two branches that exist"
        )
    if not are_strangers(repo, ours_tip, theirs_tip):
        raise Invalid(
            f"{ours} and {theirs} share an ancestor; "
            "related histories merge through the front "
            "door, adoption is for strangers"
        )
    ours_files = repo.files_at(ours_tip)
    theirs_files = repo.files_at(theirs_tip)
    contested = sorted(
        path
        for path in set(ours_files) & set(theirs_files)
        if ours_files[path] != theirs_files[path]
    )
    if contested:
        raise Conflict(
            f"{len(contested)} path(s) contested with no "
            "common ancestor to consult: "
            + ", ".join(contested)
            + "; any automatic choice is a coin flip "
            "wearing a robe"
        )
    union = {**theirs_files, **ours_files}
    merged = repo.commit_with_parents(
        union, message, (ours_tip, theirs_tip)
    )
    repo.refs.move(
        ours,
        merged.address,
        reason=f"adopted {theirs}",
    )
    return merged
