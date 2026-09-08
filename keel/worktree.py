"""Checkout: materializing a commit without stepping on anyone's work.

A checkout replaces the working copy with a snapshot, and its
one non-negotiable is the dirty check: files whose current
content differs from the outgoing commit are uncommitted
work, and switching over them is data loss with a progress
bar. The planner therefore computes three sets before
touching anything: paths to write because the target differs,
paths to delete because the target lacks them, and paths in
danger because the working copy diverges from the outgoing
snapshot where the target also wants a change, and any
member of the third set aborts the whole plan with every
casualty named, because a checkout that saves most of your
work is remembered only for the rest. Untracked files are
left standing unless the target wants their exact path, in
which case they count as danger too: the file you have not
committed yet outranks the one history wants to put there.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Conflict
from keel.repo import Repo


@dataclass(frozen=True)
class CheckoutPlan:
    writes: tuple[str, ...]
    deletions: tuple[str, ...]
    dangers: tuple[str, ...]

    def is_safe(self) -> bool:
        return not self.dangers

    def describe(self) -> str:
        return (
            f"{len(self.writes)} write(s), "
            f"{len(self.deletions)} deletion(s), "
            f"{len(self.dangers)} danger(s)"
        )


def plan_checkout(
    repo: Repo,
    working: dict[str, bytes],
    from_address: str,
    to_address: str,
) -> CheckoutPlan:
    outgoing = repo.files_at(from_address)
    target = repo.files_at(to_address)
    writes: list[str] = []
    deletions: list[str] = []
    dangers: list[str] = []
    for path in sorted(set(outgoing) | set(target)):
        old = outgoing.get(path)
        new = target.get(path)
        current = working.get(path)
        if old == new:
            continue
        dirty = current is not None and current != old
        if dirty and current != new:
            dangers.append(path)
        elif new is None:
            deletions.append(path)
        else:
            writes.append(path)
    for path in sorted(set(working) - set(outgoing)):
        if path in target and working[path] != target[path]:
            dangers.append(path)
    return CheckoutPlan(
        writes=tuple(writes),
        deletions=tuple(sorted(deletions)),
        dangers=tuple(sorted(set(dangers))),
    )


def checkout(
    repo: Repo,
    working: dict[str, bytes],
    branch: str,
) -> tuple[dict[str, bytes], str]:
    from_address = repo.refs.current()
    to_address = repo.refs.branches[branch]
    plan = plan_checkout(
        repo, working, from_address, to_address
    )
    if not plan.is_safe():
        raise Conflict(
            f"checkout aborted, every casualty named: "
            f"{', '.join(plan.dangers)}; a checkout that "
            "saves most of your work is remembered only for "
            "the rest"
        )
    target = repo.files_at(to_address)
    updated = dict(working)
    for path in plan.deletions:
        updated.pop(path, None)
    for path in plan.writes:
        updated[path] = target[path]
    repo.refs.checkout(branch)
    return updated, (
        f"on {branch}: {plan.describe()}; untracked files "
        "left standing"
    )
