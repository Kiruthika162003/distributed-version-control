"""Tree merge: files resolve independently, and the report never rounds up.

Merging two commits starts at their merge base and decides
every path on its own: changed on one side only, take it;
changed identically, take either; changed differently, descend
into diff3 for a line-level answer that may still surface a
conflict; added on both sides with different content, that is
a conflict with no base and the marker says so. The outcome
object keeps three lists, merged clean, merged by diff3, and
conflicted, because "merged with conflicts" as a single flag
throws away the number the reviewer actually wants: how much
of this did the machine settle and how much is waiting for a
person. A merge commit is only cut when the conflict list is
empty, and cutting it records both parents, which is what
makes the next merge base findable and the history honest
about being a graph rather than a rope.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import Commit
from keel.diff3 import conflict_count, is_clean, merge3, render
from keel.errors import Conflict, Invalid
from keel.objects import BLOB
from keel.repo import Repo


@dataclass
class MergeOutcome:
    base: str
    left: str
    right: str
    clean_paths: list[str] = field(default_factory=list)
    diff3_paths: list[str] = field(default_factory=list)
    conflicts: dict[str, str] = field(default_factory=dict)
    merged_files: dict[str, bytes] = field(default_factory=dict)

    def is_clean(self) -> bool:
        return not self.conflicts

    def report(self) -> str:
        line = (
            f"{len(self.clean_paths)} path(s) merged clean, "
            f"{len(self.diff3_paths)} settled by diff3, "
            f"{len(self.conflicts)} waiting for a person"
        )
        for path in sorted(self.conflicts):
            line += f"\n  conflict: {path}"
        return line


def merge_commits(
    repo: Repo, left_address: str, right_address: str
) -> MergeOutcome:
    base_address = repo.graph.merge_base(
        left_address, right_address
    )
    base_files = repo.files_at(base_address)
    left_files = repo.files_at(left_address)
    right_files = repo.files_at(right_address)
    outcome = MergeOutcome(
        base=base_address,
        left=left_address,
        right=right_address,
    )
    for path in sorted(
        set(base_files) | set(left_files) | set(right_files)
    ):
        base = base_files.get(path)
        left = left_files.get(path)
        right = right_files.get(path)
        if left == right:
            if left is not None:
                outcome.merged_files[path] = left
                outcome.clean_paths.append(path)
            continue
        if left == base:
            if right is not None:
                outcome.merged_files[path] = right
            outcome.clean_paths.append(path)
            continue
        if right == base:
            if left is not None:
                outcome.merged_files[path] = left
            outcome.clean_paths.append(path)
            continue
        if base is None or left is None or right is None:
            outcome.conflicts[path] = (
                "both sides created or deleted this path "
                "differently; there is no base to break the tie"
            )
            continue
        regions = merge3(
            base.decode(), left.decode(), right.decode()
        )
        if is_clean(regions):
            outcome.merged_files[path] = render(
                regions
            ).encode()
            outcome.diff3_paths.append(path)
        else:
            outcome.conflicts[path] = (
                f"{conflict_count(regions)} conflicting "
                "region(s); the markers hold all three texts"
            )
    return outcome


def commit_merge(
    repo: Repo, outcome: MergeOutcome, message: str
) -> Commit:
    if not outcome.is_clean():
        raise Conflict(
            f"{len(outcome.conflicts)} path(s) still waiting "
            "for a person; a merge commit cut over conflicts "
            "is a lie with two parents"
        )
    if repo.graph.is_ancestor(outcome.right, outcome.left):
        raise Invalid(
            "the right side is already an ancestor; there is "
            "nothing to merge and no second parent to record"
        )
    blobs = {
        path: repo.store.put(BLOB, content)
        for path, content in outcome.merged_files.items()
    }
    tree = repo.trees.write_tree(blobs)
    commit = repo.graph.create(
        tree=tree,
        parents=(outcome.left, outcome.right),
        message=message,
    )
    branch = repo.refs.current_branch()
    repo.refs.move(branch, commit.address, reason=message[:40])
    return commit
