"""The prompt line: the whole situation in one line, or it gets ignored.

Status that lives in a prompt earns different rules than
status that lives in a page: one line, worst news first,
and nothing that is fine, because a prompt that always
shows six facts trains eyes to skip all six. The line
opens with the branch, adds the divergence against the
tracked upstream only when there is any, in the tracking
table's own compact verbs, adds the dirty count only when
the working files differ from the head, and appends the
frozen marker only while the freeze stands, so the quiet
day renders as just the branch name, which is the correct
amount of prompt for a quiet day. Detached heads are the
one state spelled out in full, detached at an address
being exactly the situation where a terse prompt gets
someone committing into the void.
"""

from __future__ import annotations

from keel.freeze import FreezeBoard
from keel.repo import Repo
from keel.upstreams import Tracking


def line(
    repo: Repo,
    working: dict[str, bytes] | None = None,
    tracking: Tracking | None = None,
    board: FreezeBoard | None = None,
) -> str:
    if repo.refs.detached_at:
        return (
            f"DETACHED at "
            f"{repo.refs.detached_at[:8]}; commits "
            "here land in the void without a branch"
        )
    branch = repo.refs.current_branch()
    parts = [branch]
    if tracking is not None and (
        branch in tracking.follows
    ):
        status = tracking.status(branch)
        if "current with" not in status:
            compact = status.split(": ", 1)[1]
            parts.append(f"[{compact}]")
    if working is not None:
        head = repo.head_files()
        dirty = sum(
            1
            for path in set(working) | set(head)
            if working.get(path) != head.get(path)
        )
        if dirty:
            parts.append(f"*{dirty}")
    if board is not None and branch in board.freezes:
        parts.append("FROZEN")
    return " ".join(parts)
