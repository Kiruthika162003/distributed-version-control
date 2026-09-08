"""The draft: a starting message computed from what actually changed.

The blank message box produces fixed stuff, and the draft
replaces the blank with a start: the changed paths grouped
by directory to propose the subject's territory, the verb
proposed from the shape of the change, adds reading as
add, deletions as remove, pure edits as update, and mixes
as rework, and the body seeded with the file list so the
author edits downward from facts instead of upward from
nothing. The draft is a floor and it says so in its last
line, replace every word that is wrong, because a
generated message committed verbatim is the lint's
subject-noise wearing better clothes, and the drafter's
job is to make the honest message cheaper to write, not
to write it. A changeless draft is refused; there is no
message to start when nothing happened.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo


def draft(
    repo: Repo, proposed: dict[str, bytes]
) -> str:
    head = repo.head_files()
    added = sorted(
        path for path in proposed if path not in head
    )
    removed = sorted(
        path for path in head if path not in proposed
    )
    edited = sorted(
        path
        for path in set(head) & set(proposed)
        if head[path] != proposed[path]
    )
    touched = added + removed + edited
    if not touched:
        raise Invalid(
            "nothing changed; there is no message to "
            "start when nothing happened"
        )
    territories = sorted(
        {
            path.rsplit("/", 1)[0]
            if "/" in path
            else "(root)"
            for path in touched
        }
    )
    territory = (
        territories[0]
        if len(territories) == 1
        else "across " + ", ".join(territories)
    )
    if added and not removed and not edited:
        verb = "Add"
    elif removed and not added and not edited:
        verb = "Remove"
    elif edited and not added and not removed:
        verb = "Update"
    else:
        verb = "Rework"
    lines = [
        f"{verb} {territory}: <say the actual change>",
        "",
    ]
    for path in added:
        lines.append(f"adds {path}")
    for path in removed:
        lines.append(f"removes {path}")
    for path in edited:
        lines.append(f"edits {path}")
    lines.append("")
    lines.append(
        "this draft is a floor; replace every word "
        "that is wrong"
    )
    return "\n".join(lines)
