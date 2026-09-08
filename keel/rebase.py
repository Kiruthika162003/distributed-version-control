"""Rebase: the same changes, a new past, and a narrator who admits it.

A rebase replays each commit's own diff against a new base,
one at a time, in order, and the narration is the product as
much as the commits are: every replayed step reports what it
carried and every stop names the commit that conflicted, which
files, and what remains queued behind it, because the worst
minute of a rebase is not the conflict, it is not knowing how
much rebase is left. The replay computes each step's change
as the diff against its own parent, never against the
original branch point, so a ten-commit rebase carries ten
small stories instead of one tangled one. What a rebase
cannot hide is that the new commits are new: every address
changes, the narrator says so up front, and anyone who
published the old addresses now owns a divergence, which is
the honest price of a tidied past and the narrator declines
to discount it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid
from keel.objects import BLOB
from keel.repo import Repo


@dataclass
class RebaseRun:
    repo: Repo
    onto: str
    steps_done: list[str] = field(default_factory=list)
    queue: list[str] = field(default_factory=list)
    new_tip: str | None = None

    def narrate_start(self, count: int) -> str:
        return (
            f"replaying {count} commit(s) onto "
            f"{self.onto[:8]}; every address will change, and "
            "anyone holding the old ones now owns a divergence"
        )


def _commits_to_replay(
    repo: Repo, branch_tip: str, onto: str
) -> list[str]:
    base = repo.graph.merge_base(branch_tip, onto)
    if base == branch_tip:
        raise Invalid(
            "the branch is behind the target with nothing of "
            "its own; that is a fast-forward, not a rebase"
        )
    line: list[str] = []
    cursor = branch_tip
    while cursor != base:
        commit = repo.graph.get(cursor)
        if len(commit.parents) > 1:
            raise Invalid(
                f"{cursor[:8]} is a merge commit; replaying a "
                "merge flattens a decision someone made, so "
                "rebase stops at merges by design"
            )
        line.append(cursor)
        cursor = commit.parents[0]
    line.reverse()
    return line


def rebase(
    repo: Repo, branch_tip: str, onto: str
) -> tuple[RebaseRun, list[str]]:
    run = RebaseRun(repo=repo, onto=onto)
    run.queue = _commits_to_replay(repo, branch_tip, onto)
    narration = [run.narrate_start(len(run.queue))]
    current_base = onto
    while run.queue:
        step_address = run.queue[0]
        step = repo.graph.get(step_address)
        parent = step.parents[0]
        step_files = repo.files_at(step_address)
        parent_files = repo.files_at(parent)
        base_files = repo.files_at(current_base)
        merged: dict[str, bytes] = dict(base_files)
        conflicts: list[str] = []
        for path in sorted(
            set(step_files) | set(parent_files)
        ):
            before = parent_files.get(path)
            after = step_files.get(path)
            if before == after:
                continue
            ground = base_files.get(path)
            if ground in (before, after):
                if after is None:
                    merged.pop(path, None)
                else:
                    merged[path] = after
            else:
                conflicts.append(path)
        if conflicts:
            narration.append(
                f"stopped at {step_address[:8]} "
                f"({step.message}): conflict in "
                f"{', '.join(conflicts)}; "
                f"{len(run.queue) - 1} commit(s) still queued "
                "behind it"
            )
            raise Conflict("\n".join(narration))
        blobs = {
            path: repo.store.put(BLOB, content)
            for path, content in merged.items()
        }
        tree = repo.trees.write_tree(blobs)
        replayed = repo.graph.create(
            tree=tree,
            parents=(current_base,),
            message=step.message,
        )
        narration.append(
            f"replayed {step_address[:8]} as "
            f"{replayed.address[:8]}: {step.message}"
        )
        run.steps_done.append(replayed.address)
        run.queue.pop(0)
        current_base = replayed.address
    run.new_tip = current_base
    narration.append(
        f"rebase complete: {len(run.steps_done)} commit(s), "
        f"new tip {current_base[:8]}"
    )
    return run, narration


def rebase_branch(
    repo: Repo, branch: str, onto_branch: str
) -> list[str]:
    tip = repo.refs.branches.get(branch)
    onto = repo.refs.branches.get(onto_branch)
    if tip is None or onto is None:
        raise Invalid("both branches must exist to rebase")
    run, narration = rebase(repo, tip, onto)
    repo.refs.move(
        branch,
        run.new_tip,
        reason=f"rebased onto {onto_branch}",
        force=True,
    )
    return narration
