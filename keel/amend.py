"""Amend and squash: rewriting the recent past, with the reflog as parachute.

Amending replaces the tip with a corrected version, new tree
or new message, and squashing folds the last n commits into
one, and both are the same act morally: published-history
surgery performed while insisting nobody has seen the patient
yet. The machinery makes the safe part automatic, the old tip
lands in the reflog before the new one takes the name, so
undo is a reflog read, and makes the dangerous part loud: a
tip that has been pushed is refused amendment unless the
caller says published_anyway, which is not a flag so much as
a signature on a form. Squash keeps the oldest commit's
place in history and the newest tree, with the combined
message listing what was folded, because a squash whose
message forgets its ingredients is a mystery meat commit.
"""

from __future__ import annotations

from keel.commits import Commit
from keel.errors import Invalid
from keel.objects import BLOB
from keel.repo import Repo


def amend(
    repo: Repo,
    files: dict[str, bytes] | None = None,
    message: str | None = None,
    pushed_tips: set[str] | None = None,
    published_anyway: bool = False,
) -> Commit:
    tip = repo.refs.current()
    old = repo.graph.get(tip)
    if files is None and message is None:
        raise Invalid(
            "an amend that changes nothing is a commit "
            "cosplaying as work"
        )
    if (
        pushed_tips
        and tip in pushed_tips
        and not published_anyway
    ):
        raise Invalid(
            f"{tip[:8]} has been pushed; amending published "
            "history needs published_anyway, which is not a "
            "flag so much as a signature on a form"
        )
    if files is not None:
        blobs = {
            path: repo.store.put(BLOB, content)
            for path, content in files.items()
        }
        tree = repo.trees.write_tree(blobs)
    else:
        tree = old.tree
    commit = repo.graph.create(
        tree=tree,
        parents=old.parents,
        message=message if message is not None else old.message,
    )
    branch = repo.refs.current_branch()
    repo.refs.move(
        branch,
        commit.address,
        reason=f"amend of {tip[:8]}",
        force=True,
    )
    return commit


def squash(
    repo: Repo, count: int, message: str | None = None
) -> Commit:
    if count < 2:
        raise Invalid(
            "squashing fewer than two commits is either a "
            "no-op or an amend; use the right tool"
        )
    tip = repo.refs.current()
    line: list[Commit] = []
    cursor = tip
    for _ in range(count):
        commit = repo.graph.get(cursor)
        if len(commit.parents) > 1:
            raise Invalid(
                f"{cursor[:8]} is a merge; folding a merge "
                "flattens a decision, and rebase already "
                "refused this for the same reason"
            )
        line.append(commit)
        if not commit.parents:
            raise Invalid(
                f"only {len(line)} commit(s) above the root; "
                f"cannot squash {count}"
            )
        cursor = commit.parents[0]
    folded_messages = [c.message for c in reversed(line)]
    combined = message or (
        folded_messages[0]
        + "\n\nfolded: "
        + "; ".join(folded_messages[1:])
    )
    commit = repo.graph.create(
        tree=line[0].tree,
        parents=(cursor,),
        message=combined,
    )
    branch = repo.refs.current_branch()
    repo.refs.move(
        branch,
        commit.address,
        reason=f"squash of {count} commits",
        force=True,
    )
    return commit
