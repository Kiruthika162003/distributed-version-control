"""Cherry-pick and revert: one commit's change, moved or unmade, with a receipt.

Both operations are the same machine pointed in opposite
directions: a cherry-pick applies a commit's diff against its
parent onto a new place, and a revert applies that diff
backward onto the commit's own descendants, and both record
where the change came from in the message, because a change
without provenance becomes a mystery the next time it
conflicts with its own original. The conflict rule is
inherited from the merge: if the ground under the change has
moved, the operation stops and names the paths rather than
guessing, and the revert refuses one extra thing, reverting a
merge commit without being told which parent is mainline,
since a merge unmade symmetrically unmakes both sides and
nobody has ever wanted that twice.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Conflict, Invalid
from keel.objects import BLOB
from keel.repo import Repo


def _one_commit_diff(
    repo: Repo, address: str, backward: bool = False
) -> tuple[dict[str, bytes | None], dict[str, bytes | None]]:
    commit = repo.graph.get(address)
    if len(commit.parents) != 1:
        raise Invalid(
            f"{address[:8]} has {len(commit.parents)} "
            "parent(s); this machine moves single-parent "
            "changes"
        )
    parent_files = repo.files_at(commit.parents[0])
    own_files = repo.files_at(address)
    before: dict[str, bytes | None] = {}
    after: dict[str, bytes | None] = {}
    for path in set(parent_files) | set(own_files):
        old = parent_files.get(path)
        new = own_files.get(path)
        if old != new:
            before[path] = new if backward else old
            after[path] = old if backward else new
    return before, after


def _apply_change(
    target_files: dict[str, bytes],
    before: dict[str, bytes | None],
    after: dict[str, bytes | None],
    operation: str,
) -> dict[str, bytes]:
    moved_ground = [
        path
        for path in before
        if target_files.get(path) != before[path]
    ]
    if moved_ground:
        raise Conflict(
            f"{operation} stopped: the ground moved under "
            f"{', '.join(sorted(moved_ground))}; applying "
            "anyway would guess, and this machine does not"
        )
    result = dict(target_files)
    for path, content in after.items():
        if content is None:
            result.pop(path, None)
        else:
            result[path] = content
    return result


def cherry_pick(repo: Repo, address: str) -> Commit:
    before, after = _one_commit_diff(repo, address)
    target_files = repo.head_files()
    merged = _apply_change(
        target_files, before, after, "cherry-pick"
    )
    original = repo.graph.get(address)
    blobs = {
        path: repo.store.put(BLOB, content)
        for path, content in merged.items()
    }
    tree = repo.trees.write_tree(blobs)
    commit = repo.graph.create(
        tree=tree,
        parents=(repo.refs.current(),),
        message=(
            f"{original.message} (cherry-picked from "
            f"{address[:8]})"
        ),
    )
    branch = repo.refs.current_branch()
    repo.refs.move(
        branch, commit.address, reason="cherry-pick"
    )
    return commit


def revert(repo: Repo, address: str) -> Commit:
    original = repo.graph.get(address)
    if len(original.parents) > 1:
        raise Invalid(
            f"{address[:8]} is a merge; a merge unmade "
            "symmetrically unmakes both sides, and nobody has "
            "ever wanted that twice; name the mainline parent "
            "by picking the specific changes instead"
        )
    before, after = _one_commit_diff(
        repo, address, backward=True
    )
    target_files = repo.head_files()
    merged = _apply_change(
        target_files, before, after, "revert"
    )
    blobs = {
        path: repo.store.put(BLOB, content)
        for path, content in merged.items()
    }
    tree = repo.trees.write_tree(blobs)
    commit = repo.graph.create(
        tree=tree,
        parents=(repo.refs.current(),),
        message=(
            f"Revert: {original.message} (unmakes "
            f"{address[:8]})"
        ),
    )
    branch = repo.refs.current_branch()
    repo.refs.move(branch, commit.address, reason="revert")
    return commit
