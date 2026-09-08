"""Octopus merge: many branches, one commit, zero tolerance for conflicts.

Merging several branches in one commit keeps integration
history flat when a batch of independent topics lands
together, and the entire legitimacy of the shape rests on
one property: every head must merge cleanly against the
accumulating result, because an octopus with conflicts has
no sane place to record resolutions, eight parents but only
one tree, and the person resolving would be answering
questions no marker can even pose. So the octopus refuses at
the first conflict, names the branch that collided and the
branches already folded, and prescribes the fallback, merge
that one alone first, since the octopus is a convenience for
the easy case and a convenience that struggles has become a
liability. Parent order records fold order, which is the
only narrative an octopus has.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Conflict, Invalid
from keel.merge import merge_commits
from keel.objects import BLOB
from keel.repo import Repo


def octopus_merge(
    repo: Repo, branch_names: list[str], message: str
) -> Commit:
    if len(branch_names) < 2:
        raise Invalid(
            "an octopus needs at least two heads; one head "
            "is a fast-forward wearing a costume"
        )
    tips = []
    for name in branch_names:
        tip = repo.refs.branches.get(name)
        if tip is None:
            raise Invalid(f"{name} is not a branch")
        tips.append(tip)
    current = repo.refs.current()
    accumulated_files = repo.files_at(current)
    folded: list[str] = []
    for name, tip in zip(branch_names, tips, strict=True):
        blobs = {
            path: repo.store.put(BLOB, content)
            for path, content in accumulated_files.items()
        }
        staging_tree = repo.trees.write_tree(blobs)
        staging = repo.graph.create(
            tree=staging_tree,
            parents=(current,),
            message=f"octopus staging after {name}",
        )
        outcome = merge_commits(repo, staging.address, tip)
        if not outcome.is_clean():
            raise Conflict(
                f"the octopus stops at {name}: "
                f"{len(outcome.conflicts)} conflict(s) with "
                f"the fold of [{', '.join(folded) or 'none'}]"
                "; eight parents but one tree leaves no sane "
                f"place for resolutions, so merge {name} "
                "alone first"
            )
        accumulated_files = outcome.merged_files
        folded.append(name)
    blobs = {
        path: repo.store.put(BLOB, content)
        for path, content in accumulated_files.items()
    }
    tree = repo.trees.write_tree(blobs)
    commit = repo.graph.create(
        tree=tree,
        parents=(current, *tips),
        message=message,
    )
    branch = repo.refs.current_branch()
    repo.refs.move(
        branch, commit.address, reason="octopus merge"
    )
    return commit


def describe_octopus(repo: Repo, address: str) -> str:
    commit = repo.graph.get(address)
    if len(commit.parents) < 3:
        return (
            f"{address[:8]} has {len(commit.parents)} "
            "parent(s); not an octopus"
        )
    return (
        f"{address[:8]}: octopus of "
        f"{len(commit.parents)} parents; the order records "
        "the fold, which is the only narrative an octopus has"
    )
