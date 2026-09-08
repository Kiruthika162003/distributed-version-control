"""Restructuring: the big rename planned on paper, landed in one commit.

Moving forty files one commit at a time makes forty
half-moved states nobody can build, and moving them with
no plan makes collisions discovered midway, so the
restructure runs like the split does, audit first and
motion second. The map is prefix to prefix, and the audit
catches the three accidents before any of them happens: a
destination that collides with a file already living
there, two rules claiming one file, and a rule that moves
nothing, which is usually a typo wearing confidence. The
landing is one commit whose message carries the map, and
every move is byte-identical on purpose, because exact
renames are the ones the detector certifies at similarity
one and the follow walks for free, so a restructure done
this way stays walkable history instead of becoming the
event horizon that blames and follows die at.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid
from keel.repo import Repo


def plan_moves(
    files: dict[str, bytes],
    mapping: dict[str, str],
) -> dict[str, str]:
    if not mapping:
        raise Invalid(
            "an empty map moves nothing on purpose, "
            "which needs no tool"
        )
    moves: dict[str, str] = {}
    claimed_by: dict[str, str] = {}
    for old_prefix in sorted(mapping):
        new_prefix = mapping[old_prefix]
        if not old_prefix.endswith("/") or (
            not new_prefix.endswith("/")
        ):
            raise Invalid(
                f"{old_prefix} -> {new_prefix}: "
                "prefixes are directories and end "
                "with a slash"
            )
        matched = 0
        for path in files:
            if not path.startswith(old_prefix):
                continue
            if path in claimed_by:
                raise Invalid(
                    f"{path} is claimed by both "
                    f"{claimed_by[path]} and "
                    f"{old_prefix}; two rules on one "
                    "file move it nowhere twice"
                )
            claimed_by[path] = old_prefix
            destination = (
                new_prefix + path[len(old_prefix):]
            )
            moves[path] = destination
            matched += 1
        if matched == 0:
            raise Invalid(
                f"{old_prefix} moves nothing; a rule "
                "that matches no file is usually a "
                "typo wearing confidence"
            )
    stationary = set(files) - set(moves)
    for path, destination in moves.items():
        if destination in stationary:
            raise Invalid(
                f"{path} -> {destination}: the "
                "destination is already inhabited; "
                "landing there buries a resident"
            )
        if destination in moves:
            raise Invalid(
                f"{path} -> {destination}: the "
                "destination is itself being moved; "
                "chains land in single file, plan "
                "them as one hop"
            )
    return moves


def restructure(
    repo: Repo, mapping: dict[str, str]
) -> Commit:
    files = repo.head_files()
    moves = plan_moves(files, mapping)
    rebuilt = {
        moves.get(path, path): content
        for path, content in files.items()
    }
    map_lines = "\n".join(
        f"{old} -> {new}"
        for old, new in sorted(mapping.items())
    )
    return repo.commit(
        rebuilt,
        f"restructure: {len(moves)} file(s) moved\n\n"
        + map_lines,
    )


def narrate_plan(
    repo: Repo, mapping: dict[str, str]
) -> str:
    moves = plan_moves(repo.head_files(), mapping)
    lines = [
        f"{len(moves)} move(s) planned, every one "
        "byte-identical so the detector certifies "
        "them at similarity one:"
    ]
    lines.extend(
        f"  {old} -> {moves[old]}"
        for old in sorted(moves)
    )
    lines.append(
        "one commit, walkable history; the "
        "alternative is an event horizon that blames "
        "and follows die at"
    )
    return "\n".join(lines)
