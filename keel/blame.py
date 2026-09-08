"""Blame: every line names the commit that last touched it, walking backward.

Blame starts at a commit and walks toward the root, and the
direction matters: a line is attributed to the newest commit
in which it does not exist in the parent's version of the
file, because "who wrote this" almost always means "who made
it look like this", not "who typed the first draft". The
walk follows one file and carries surviving lines backward
through each diff: lines the parent already had keep
walking, lines it lacked stop and take the child's name.
Renames would break the trail at the boundary, so the walk
consults the rename detector when the path vanishes from a
parent, and the report says the trail crossed a rename,
because an attribution that silently walked through a rename
claims a certainty about identity the similarity score does
not have.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Missing
from keel.renames import detect_renames
from keel.repo import Repo


@dataclass(frozen=True)
class BlameLine:
    line_number: int
    text: str
    commit: str
    message: str


def _file_history(
    repo: Repo, start: str, path: str
) -> list[tuple[str, str, bytes]]:
    trail: list[tuple[str, str, bytes]] = []
    cursor: str | None = start
    current_path = path
    while cursor is not None:
        commit = repo.graph.get(cursor)
        files = repo.files_at(cursor)
        if current_path not in files:
            break
        trail.append(
            (cursor, current_path, files[current_path])
        )
        if not commit.parents:
            break
        parent = commit.parents[0]
        parent_files = repo.files_at(parent)
        if current_path not in parent_files:
            removed = {
                p: c
                for p, c in parent_files.items()
                if p not in files
            }
            renames, _, _ = detect_renames(
                removed=removed,
                added={current_path: files[current_path]},
            )
            if renames:
                current_path = renames[0].old_path
            else:
                break
        cursor = parent
    if not trail:
        raise Missing(
            f"{path} does not exist at {start[:8]}; blame "
            "needs a file to point at"
        )
    return trail


def blame(repo: Repo, start: str, path: str) -> list[BlameLine]:
    trail = _file_history(repo, start, path)
    newest_text = trail[0][2].decode()
    lines = newest_text.splitlines()
    attribution: list[str | None] = [None] * len(lines)
    survivors = list(range(len(lines)))
    for depth in range(len(trail)):
        commit_address = trail[depth][0]
        if depth + 1 < len(trail):
            parent_content = trail[depth + 1][2]
            parent_lines = set(
                parent_content.decode().splitlines()
            )
        else:
            parent_lines = set()
        still_walking: list[int] = []
        for index in survivors:
            if lines[index] in parent_lines:
                still_walking.append(index)
            else:
                attribution[index] = commit_address
        survivors = still_walking
    for index in survivors:
        attribution[index] = trail[-1][0]
    return [
        BlameLine(
            line_number=index + 1,
            text=lines[index],
            commit=attribution[index],
            message=repo.graph.get(attribution[index]).message,
        )
        for index in range(len(lines))
    ]


def render_blame(rows: list[BlameLine]) -> str:
    return "\n".join(
        f"{row.commit[:8]} {row.line_number:>4} "
        f"{row.text}  ({row.message})"
        for row in rows
    )


def crossed_renames(
    repo: Repo, start: str, path: str
) -> list[str]:
    trail = _file_history(repo, start, path)
    crossings = []
    for depth in range(1, len(trail)):
        if trail[depth][1] != trail[depth - 1][1]:
            crossings.append(
                f"the trail crossed a rename: "
                f"{trail[depth][1]} -> {trail[depth - 1][1]} "
                f"at {trail[depth - 1][0][:8]}"
            )
    return crossings


def summarize(rows: list[BlameLine]) -> str:
    by_commit: dict[str, int] = {}
    for row in rows:
        by_commit[row.commit] = by_commit.get(row.commit, 0) + 1
    ranked = sorted(
        by_commit.items(), key=lambda held: -held[1]
    )
    parts = [
        f"{address[:8]} owns {count}"
        for address, count in ranked
    ]
    return f"{len(rows)} line(s): " + ", ".join(parts)
