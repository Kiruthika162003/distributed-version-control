"""Show: one commit, the whole story, assembled from the organs that know.

The most-run command in any version control system is the
one that answers what did this commit actually do, and the
answer is assembled rather than stored: the header from the
graph, the stat table from the tree diff, renames folded in
so a move reads as a move instead of a funeral and a birth,
and the hunks themselves from the line diff, binary files
summarized by weight because their hunks would be noise
wearing angle brackets. Merges get the honest short form,
the parents listed and the hunks declined, since a merge
diffed against one parent slanders the other and diffed
against both is two pages pretending to be one; the combined
view is the merge machinery's job and the page says whose.
The root commit diffs against emptiness, which is the one
case where everything being an addition is the truth rather
than a bug.
"""

from __future__ import annotations

from keel.binarydiff import narrate as binary_narrate
from keel.difflines import diff_lines
from keel.diffstat import (
    looks_binary,
    render_stat,
    stat_changes,
)
from keel.renames import detect_renames
from keel.repo import Repo


def _hunk_text(old: bytes, new: bytes) -> list[str]:
    hunks = diff_lines(
        old.decode(errors="replace"),
        new.decode(errors="replace"),
    )
    lines: list[str] = []
    for hunk in hunks:
        lines.append(
            f"    @@ -{hunk.old_start} "
            f"+{hunk.new_start} @@"
        )
        lines.extend(
            f"    -{line}" for line in hunk.old_lines
        )
        lines.extend(
            f"    +{line}" for line in hunk.new_lines
        )
    return lines


def show(repo: Repo, address: str) -> str:
    commit = repo.graph.get(address)
    lines = [
        f"commit {commit.address[:8]} "
        f"(sequence {commit.sequence})",
        f"message: {commit.message.splitlines()[0]}",
    ]
    if len(commit.parents) > 1:
        parents = ", ".join(
            parent[:8] for parent in commit.parents
        )
        lines.append(
            f"a merge of {parents}; hunks declined, "
            "a merge diffed against one parent "
            "slanders the other, and the combined "
            "view is the merge machinery's job"
        )
        return "\n".join(lines)
    current = repo.files_at(address)
    parent_files = (
        repo.files_at(commit.parents[0])
        if commit.parents
        else {}
    )
    if not commit.parents:
        lines.append(
            "the root; diffed against emptiness, "
            "where everything being an addition is "
            "the truth"
        )
    removed = {
        path: parent_files[path]
        for path in parent_files
        if path not in current
    }
    added = {
        path: current[path]
        for path in current
        if path not in parent_files
    }
    renames, _true_removed, _true_added = (
        detect_renames(removed, added)
        if removed and added
        else ([], [], [])
    )
    renamed_old = {r.old_path for r in renames}
    renamed_new = {r.new_path for r in renames}
    stats = stat_changes(parent_files, current)
    stat_rows = [
        stat
        for stat in stats
        if stat.path not in renamed_old
        and stat.path not in renamed_new
    ]
    if stat_rows:
        lines.append(render_stat(stat_rows))
    for rename in renames:
        lines.append(
            f"  moved {rename.describe()}; a move "
            "reads as a move, not a funeral and a "
            "birth"
        )
    for path in sorted(
        set(current) | set(parent_files)
    ):
        if path in renamed_old or path in renamed_new:
            continue
        old = parent_files.get(path, b"")
        new = current.get(path, b"")
        if old == new:
            continue
        if looks_binary(old) or looks_binary(new):
            lines.append(
                "  " + binary_narrate(path, old, new)
            )
            continue
        lines.append(f"  {path}:")
        lines.extend(_hunk_text(old, new))
    return "\n".join(lines)
