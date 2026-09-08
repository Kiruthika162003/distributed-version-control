"""Autostash: the shelf used by a machine, with the machine held to receipts.

Operations that demand a clean working copy usually get one
by yelling, and the human responds by shelving, operating,
and unshelving, three commands where one intention lived.
Autostash runs that dance mechanically but keeps every
receipt a human would have gotten: the dirty paths are named
before the operation, the operation runs against a clean
copy, and the shelved work comes back afterward unless the
operation rewrote the same paths, in which case the reapply
refuses with the collision named rather than laying old work
over new ground. The refusal leaves the work on the shelf,
labeled and safe, because an autostash that loses the stash
on its failure path has automated exactly the accident it
existed to prevent. A clean working copy skips the shelf
entirely and says so, since a receipt for shelving nothing
is how tools train people to stop reading receipts.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from keel.errors import Conflict
from keel.repo import Repo
from keel.stash import Stash

Operation = Callable[[], str]


@dataclass(frozen=True)
class AutostashOutcome:
    files: dict[str, bytes]
    receipt: str


def _dirty_paths(
    working: dict[str, bytes], head: dict[str, bytes]
) -> list[str]:
    paths = sorted(set(working) | set(head))
    return [
        path
        for path in paths
        if working.get(path) != head.get(path)
    ]


def with_autostash(
    repo: Repo,
    shelf: Stash,
    working: dict[str, bytes],
    operation: Operation,
) -> AutostashOutcome:
    head_before = repo.head_files()
    dirty = _dirty_paths(working, head_before)
    if not dirty:
        note = operation()
        return AutostashOutcome(
            files=dict(repo.head_files()),
            receipt=(
                f"clean copy, no shelf needed; {note}"
            ),
        )
    branch = repo.refs.current_branch()
    shelved = {
        path: working[path]
        for path in dirty
        if path in working
    }
    if shelved:
        shelf.push(
            shelved,
            branch,
            f"autostash of {len(dirty)} dirty path(s)",
        )
    note = operation()
    head_after = repo.head_files()
    collisions = [
        path
        for path in dirty
        if head_after.get(path) != head_before.get(path)
    ]
    if collisions:
        raise Conflict(
            f"the operation rewrote "
            f"{', '.join(collisions)} under the shelf; "
            "the work stays shelved as "
            f"'autostash of {len(dirty)} dirty path(s)' "
            "because laying old work over new ground is "
            "the accident autostash exists to prevent"
        )
    restored = dict(head_after)
    for path in dirty:
        if path in working:
            restored[path] = working[path]
        else:
            restored.pop(path, None)
    if shelved:
        shelf.pop(branch)
    return AutostashOutcome(
        files=restored,
        receipt=(
            f"shelved {len(dirty)} path(s), ran the "
            f"operation ({note}), and restored the work; "
            "one intention, one receipt"
        ),
    )
