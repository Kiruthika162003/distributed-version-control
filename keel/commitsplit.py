"""Splitting the boulder: one commit becomes several, and the cut proves itself.

The everything-commit is the reviewer's dread and the
doctor's most common finding, and the splitter is the
remedy that does arithmetic instead of surgery by feel. A
split plan names groups, each a message and the paths it
carries, and the plan is audited before anything moves:
every changed path in the boulder must appear in exactly
one group, because a path left out of the plan would
vanish from history silently and a path claimed twice
would land twice with two stories. The groups then become
real commits in plan order, each building on the last, and
the final tree is compared byte for byte against the
boulder's own, the proof that the cut lost nothing and
invented nothing. The branch moves to the new tip and the
boulder survives in the reflog, demoted from history to
memory, which is where everything-commits belong.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass(frozen=True)
class SplitGroup:
    message: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class SplitResult:
    old_boulder: str
    landed: tuple[tuple[str, str], ...]
    new_tip: str

    def narrate(self) -> str:
        lines = [
            f"{len(self.landed)} commit(s) replace "
            f"{self.old_boulder[:8]}:"
        ]
        lines.extend(
            f"  {address[:8]} {message.splitlines()[0]}"
            for message, address in self.landed
        )
        lines.append(
            "the cut proved itself: the last tree "
            "equals the boulder's, byte for byte"
        )
        return "\n".join(lines)


def _boulder_changes(
    repo: Repo, address: str
) -> dict[str, bytes | None]:
    commit = repo.graph.get(address)
    if len(commit.parents) != 1:
        raise Invalid(
            f"{address[:8]} has {len(commit.parents)} "
            "parent(s); splitting needs one parent to "
            "measure the boulder against"
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


def _audit(
    changes: dict[str, bytes | None],
    groups: list[SplitGroup],
) -> None:
    if len(groups) < 2:
        raise Invalid(
            "a split into one piece is a rename of "
            "the problem"
        )
    claimed: dict[str, str] = {}
    for group in groups:
        if not group.message.strip():
            raise Invalid(
                "every piece needs a message; unnamed "
                "pieces are the boulder wearing gravel"
            )
        if not group.paths:
            raise Invalid(
                f"{group.message!r} carries no paths; "
                "an empty piece is a mood, not a commit"
            )
        for path in group.paths:
            if path not in changes:
                raise Missing(
                    f"{path} is not part of the "
                    "boulder; the plan splits what "
                    "changed, not what exists"
                )
            if path in claimed:
                raise Invalid(
                    f"{path} is claimed by both "
                    f"{claimed[path]!r} and "
                    f"{group.message!r}; twice landed "
                    "is twice storied"
                )
            claimed[path] = group.message
    unclaimed = sorted(set(changes) - set(claimed))
    if unclaimed:
        raise Invalid(
            "unclaimed change(s): "
            + ", ".join(unclaimed)
            + "; a path left out of the plan vanishes "
            "silently, so the plan must say every name"
        )


def split(
    repo: Repo,
    branch: str,
    groups: list[SplitGroup],
) -> SplitResult:
    tip = repo.refs.branches.get(branch)
    if tip is None:
        raise Missing(f"{branch} is not a branch here")
    changes = _boulder_changes(repo, tip)
    _audit(changes, groups)
    parent = repo.graph.get(tip).parents[0]
    files = dict(repo.files_at(parent))
    previous = parent
    landed: list[tuple[str, str]] = []
    for group in groups:
        for path in group.paths:
            content = changes[path]
            if content is None:
                files.pop(path, None)
            else:
                files[path] = content
        created = repo.commit_with_parents(
            dict(files), group.message, (previous,)
        )
        previous = created.address
        landed.append((group.message, created.address))
    if repo.files_at(previous) != repo.files_at(tip):
        raise Invalid(
            "the cut failed its own proof; the final "
            "tree differs from the boulder's and "
            "nothing was moved"
        )
    repo.refs.move(
        branch,
        previous,
        reason=f"split {tip[:8]} into {len(groups)}",
        force=True,
    )
    return SplitResult(
        old_boulder=tip,
        landed=tuple(landed),
        new_tip=previous,
    )
