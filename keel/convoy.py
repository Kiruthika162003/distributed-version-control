"""The convoy: several branches land together or the harbor stays as it was.

The merge queue lands what it can and bounces the rest,
which is right for strangers; the convoy is for branches
that only make sense together, the API change and its three
callers, where landing half is worse than landing none. The
integration is built privately first, each branch merged
onto a growing candidate in the declared order, and any
conflict anywhere abandons the whole attempt with the
colliding pair named, the trunk untouched, because the
convoy's one promise is that the harbor after a failure
looks exactly like the harbor before the attempt. The gate
runs once, on the final combination, since testing the
intermediate states of an all-or-nothing landing is testing
ships that will never exist alone, and the landing itself
is a single pointer move to the finished candidate, atomic
the way the ref transaction taught, with every merged
branch named in the one commit that carries them all.
"""

from __future__ import annotations

from collections.abc import Callable

from keel.errors import Conflict, Invalid
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo

Gate = Callable[[dict[str, bytes]], str | None]


def land_convoy(
    repo: Repo,
    trunk: str,
    branches: list[str],
    gate: Gate,
) -> str:
    if len(branches) < 2:
        raise Invalid(
            "one ship is not a convoy; use the queue"
        )
    for branch in branches:
        if branch not in repo.refs.branches:
            raise Invalid(
                f"{branch} is not a branch here"
            )
    trunk_before = repo.refs.branches[trunk]
    current = repo.refs.current_branch()
    if current != trunk:
        repo.refs.checkout(trunk)
    candidate = trunk_before
    try:
        for branch in branches:
            outcome = merge_commits(
                repo,
                candidate,
                repo.refs.branches[branch],
            )
            if not outcome.is_clean():
                paths = ", ".join(
                    sorted(outcome.conflicts)
                )
                raise Conflict(
                    f"the convoy scatters: {branch} "
                    f"collides on {paths}; nothing "
                    "landed, and the harbor looks "
                    "exactly as it did before the "
                    "attempt"
                )
            merged = commit_merge(
                repo,
                outcome,
                f"convoy leg: {branch}",
            )
            repo.refs.move(
                trunk,
                trunk_before,
                reason="convoy keeps the trunk still",
                force=True,
            )
            candidate = merged.address
        refusal = gate(
            dict(repo.files_at(candidate))
        )
        if refusal is not None:
            raise Conflict(
                f"the convoy is turned away at the "
                f"final combination: {refusal}; "
                "nothing landed"
            )
        repo.refs.move(
            trunk,
            candidate,
            reason=(
                "convoy of " + ", ".join(branches)
            ),
        )
        return (
            f"the convoy lands: {len(branches)} "
            f"branch(es) as one pointer move, "
            f"{trunk} now at {candidate[:8]}; "
            "together or not at all, and today it "
            "was together"
        )
    finally:
        if current != trunk:
            repo.refs.checkout(current)
