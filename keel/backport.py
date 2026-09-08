"""Backports: one fix, several release branches, oldest patient first.

A fix that must reach three maintenance branches is one
change and three landings, and the planner treats it that
way: the fix's changes are read once, as a diff against its
parent, then each target branch is examined for whether
those changes apply to the files it actually holds. The
order is oldest release first on purpose, because the
oldest branch has drifted furthest and will fail loudest,
and discovering the hard landing after the easy ones means
revisiting decisions already celebrated. Each verdict is
per-branch and honest: applies cleanly, already there with
the evidence, or diverged with the path named and the
advice that a hand-port is a new change wearing the old
message. Execution lands only the clean verdicts and lands
them as real commits on their branches, each message
naming the original address, since a backport that hides
its origin is a cherry-pick that lies about the tree it
fell from.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid
from keel.repo import Repo

VERDICT_CLEAN = "applies cleanly"
VERDICT_PRESENT = "already there"
VERDICT_DIVERGED = "diverged"


@dataclass(frozen=True)
class BranchVerdict:
    branch: str
    verdict: str
    detail: str

    def line(self) -> str:
        return (
            f"  {self.branch}: {self.verdict} "
            f"({self.detail})"
        )


def _changes_of(
    repo: Repo, address: str
) -> dict[str, bytes | None]:
    commit = repo.graph.get(address)
    if len(commit.parents) != 1:
        raise Invalid(
            f"{address[:8]} has {len(commit.parents)} "
            "parent(s); backports carry single-parent "
            "fixes, and a merge is a meeting, not a fix"
        )
    current = repo.files_at(address)
    parent = repo.files_at(commit.parents[0])
    changes: dict[str, bytes | None] = {}
    for path, content in current.items():
        if parent.get(path) != content:
            changes[path] = content
    for path in parent:
        if path not in current:
            changes[path] = None
    return changes


def _judge(
    repo: Repo,
    fix: str,
    branch: str,
) -> BranchVerdict:
    changes = _changes_of(repo, fix)
    parent_files = repo.files_at(
        repo.graph.get(fix).parents[0]
    )
    held_files = repo.files_at(
        repo.refs.branches[branch]
    )
    already = 0
    diverged: list[str] = []
    for path, content in changes.items():
        held = held_files.get(path)
        if held == content:
            already += 1
            continue
        if held != parent_files.get(path):
            diverged.append(path)
    if diverged:
        return BranchVerdict(
            branch=branch,
            verdict=VERDICT_DIVERGED,
            detail=(
                ", ".join(sorted(diverged))
                + " moved on; a hand-port is a new "
                "change wearing the old message"
            ),
        )
    if already == len(changes):
        return BranchVerdict(
            branch=branch,
            verdict=VERDICT_PRESENT,
            detail=(
                f"all {already} change(s) present; "
                "somebody got here first"
            ),
        )
    return BranchVerdict(
        branch=branch,
        verdict=VERDICT_CLEAN,
        detail=(
            f"{len(changes) - already} change(s) to "
            "carry"
        ),
    )


def plan(
    repo: Repo, fix: str, branches: list[str]
) -> list[BranchVerdict]:
    if not branches:
        raise Invalid(
            "a backport to nowhere is a fix admiring "
            "itself"
        )
    for branch in branches:
        if branch not in repo.refs.branches:
            raise Invalid(
                f"{branch} is not a branch here"
            )
    ordered = sorted(
        branches,
        key=lambda name: repo.graph.get(
            repo.refs.branches[name]
        ).sequence,
    )
    return [
        _judge(repo, fix, branch) for branch in ordered
    ]


def narrate(
    repo: Repo, fix: str, branches: list[str]
) -> str:
    verdicts = plan(repo, fix, branches)
    subject = repo.graph.get(fix).message.splitlines()[0]
    lines = [
        f"backport of {fix[:8]} ({subject!r}), oldest "
        "patient first:"
    ]
    lines.extend(verdict.line() for verdict in verdicts)
    return "\n".join(lines)


def execute(
    repo: Repo, fix: str, branches: list[str]
) -> str:
    verdicts = plan(repo, fix, branches)
    changes = _changes_of(repo, fix)
    subject = repo.graph.get(fix).message.splitlines()[0]
    landed = []
    for verdict in verdicts:
        if verdict.verdict != VERDICT_CLEAN:
            continue
        tip = repo.refs.branches[verdict.branch]
        files = dict(repo.files_at(tip))
        for path, content in changes.items():
            if content is None:
                files.pop(path, None)
            else:
                files[path] = content
        created = repo.commit_with_parents(
            files,
            f"{subject}\n\n(backported from {fix[:8]})",
            (tip,),
        )
        repo.refs.move(
            verdict.branch,
            created.address,
            reason=f"backport {fix[:8]}",
        )
        landed.append(verdict.branch)
    skipped = len(verdicts) - len(landed)
    return (
        f"landed on {len(landed)} branch(es)"
        + (
            ": " + ", ".join(landed)
            if landed
            else ""
        )
        + f"; {skipped} left with their verdicts"
    )
