"""History queries: the log answers questions, not scrolls.

A log that prints everything teaches people to grep it, and
grep does not know the graph, so the questions worth asking
live here: which commits touched this path, walked with the
rename trail so the answer does not stop at a move; the
first-parent line, which reads a branch the way its owner
experienced it, merges as single events rather than
interleaved histories; and the range query, what is on this
branch that is not on that one, which is the question every
review opens with. Path filtering compares each commit's tree
entry for the path against its first parent's, because
comparing file bytes would charge a full read per commit for
an answer the tree addresses already hold, and the range
walk subtracts ancestor sets rather than replaying anything,
since set arithmetic on a DAG is the cheapest true answer in
this whole system.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid, Missing
from keel.renames import detect_renames
from keel.repo import Repo


def touching_path(
    repo: Repo, start: str, path: str
) -> list[tuple[Commit, str]]:
    found: list[tuple[Commit, str]] = []
    cursor: str | None = start
    current_path = path
    while cursor is not None:
        commit = repo.graph.get(cursor)
        own_blob = _entry_or_none(
            repo, commit.tree, current_path
        )
        if own_blob is None:
            break
        if commit.parents:
            parent = repo.graph.get(commit.parents[0])
            parent_blob = _entry_or_none(
                repo, parent.tree, current_path
            )
            if parent_blob != own_blob:
                found.append((commit, current_path))
            if parent_blob is None:
                own_files = repo.files_at(cursor)
                parent_files = repo.files_at(
                    commit.parents[0]
                )
                removed = {
                    p: c
                    for p, c in parent_files.items()
                    if p not in own_files
                }
                renames, _, _ = detect_renames(
                    removed=removed,
                    added={
                        current_path: own_files[current_path]
                    },
                )
                if renames:
                    current_path = renames[0].old_path
                else:
                    break
            cursor = commit.parents[0]
        else:
            found.append((commit, current_path))
            cursor = None
    if not found:
        raise Missing(
            f"{path} has no history from {start[:8]}"
        )
    return found


def _entry_or_none(
    repo: Repo, tree: str, path: str
) -> str | None:
    try:
        return repo.trees.entry_at(tree, path)
    except (Missing, Invalid):
        return None


def first_parent_line(repo: Repo, start: str) -> list[Commit]:
    line: list[Commit] = []
    cursor: str | None = start
    while cursor is not None:
        commit = repo.graph.get(cursor)
        line.append(commit)
        cursor = (
            commit.parents[0] if commit.parents else None
        )
    return line


def only_on(
    repo: Repo, branch_tip: str, other_tip: str
) -> list[Commit]:
    ours = repo.graph.ancestors(branch_tip)
    theirs = repo.graph.ancestors(other_tip)
    exclusive = ours - theirs
    found = [repo.graph.get(a) for a in exclusive]
    found.sort(key=lambda commit: -commit.sequence)
    return found


def review_summary(
    repo: Repo, branch_tip: str, other_tip: str
) -> str:
    exclusive = only_on(repo, branch_tip, other_tip)
    if not exclusive:
        return (
            "nothing here that the other side lacks; the "
            "review is a handshake"
        )
    lines = [
        f"{len(exclusive)} commit(s) to review:"
    ]
    lines.extend(
        f"  {commit.address[:8]} {commit.message}"
        for commit in exclusive
    )
    return "\n".join(lines)
