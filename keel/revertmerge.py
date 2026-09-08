"""Reverting a merge: undo the arrival without pretending it never docked.

Reverting an ordinary commit inverts one diff; reverting a
merge asks a sharper question first: relative to which
parent? The mainline choice decides which side of history
stays and which side's changes are backed out, and the tool
demands it explicitly because defaulting it silently is how
someone reverts their own trunk while aiming at the feature.
The famous trap is documented in the receipt rather than a
manual nobody reads: after a merge revert, the branch's
commits are still ancestors of the trunk, so merging the
branch again brings back nothing, and the receipt says so
and prescribes the cure, revert the revert first, then
merge. An undo that leaves a landmine without a flag is not
an undo, it is a scheduling decision about when the surprise
goes off.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid
from keel.repo import Repo


def revert_merge(
    repo: Repo, merge_address: str, mainline: int
) -> tuple[Commit, str]:
    merge = repo.graph.get(merge_address)
    if len(merge.parents) < 2:
        raise Invalid(
            f"{merge_address[:8]} has "
            f"{len(merge.parents)} parent(s); reverting an "
            "ordinary commit needs no mainline and a "
            "different tool"
        )
    if not (1 <= mainline <= len(merge.parents)):
        raise Invalid(
            f"mainline {mainline} is not one of this "
            f"merge's {len(merge.parents)} parents; the "
            "choice is demanded explicitly because a silent "
            "default is how someone reverts their own trunk "
            "while aiming at the feature"
        )
    keep = merge.parents[mainline - 1]
    merged_files = repo.files_at(merge_address)
    keep_files = repo.files_at(keep)
    working = dict(repo.head_files())
    for path in set(merged_files) | set(keep_files):
        in_merge = merged_files.get(path)
        in_keep = keep_files.get(path)
        if in_merge == in_keep:
            continue
        if in_keep is None:
            working.pop(path, None)
        else:
            working[path] = in_keep
    commit = repo.commit(
        working,
        f"Revert merge {merge_address[:8]} "
        f"(mainline {mainline})",
    )
    receipt = (
        f"merge reverted relative to parent {mainline}; "
        "FLAG: the branch's commits remain ancestors of "
        "this trunk, so merging that branch again brings "
        "back nothing; the cure is revert the revert first, "
        "then merge"
    )
    return commit, receipt


def remerge_warning(
    repo: Repo, trunk_tip: str, branch_tip: str
) -> str:
    if repo.graph.is_ancestor(branch_tip, trunk_tip):
        return (
            "the branch is already an ancestor of the "
            "trunk; if its changes are missing, a merge "
            "revert ate them, and merging again brings back "
            "nothing"
        )
    return "the branch has new commits; a merge will carry them"
