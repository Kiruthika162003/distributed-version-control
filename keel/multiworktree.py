"""Worktree desks: one repository, several desks, no branch seated twice.

A second working copy exists so the long build and the quick
fix stop fighting over one directory, and the bookkeeping
here enforces the rule that makes several desks safe: a
branch sits at one desk or none, because two desks holding
the same branch means the branch's state depends on which
door you walked in through, and one of the desks is lying.
Locks exist for the desk that must not be swept, the one
mid-bisect or holding a half-built release, and a lock
without a note is refused since the person who finds a
locked desk in March deserves to know whether the reason
retired in January. Pruning clears desks whose branches are
gone but steps around locked ones and says so, a janitor
that reads the signs, and relocation moves a desk to a new
branch under the same one-desk rule rather than around it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass
class Desk:
    name: str
    branch: str
    locked: bool = False
    note: str = ""


@dataclass
class WorktreeSet:
    repo: Repo
    desks: dict[str, Desk] = field(default_factory=dict)

    def _seated(self, branch: str) -> Desk | None:
        for desk in self.desks.values():
            if desk.branch == branch:
                return desk
        return None

    def add(self, name: str, branch: str) -> str:
        if name in self.desks:
            raise Invalid(f"desk {name} already exists")
        if branch not in self.repo.refs.branches:
            raise Missing(f"{branch} is not a branch here")
        seated = self._seated(branch)
        if seated is not None:
            raise Invalid(
                f"{branch} already sits at desk "
                f"{seated.name}; the same branch on two "
                "desks means one desk lies"
            )
        self.desks[name] = Desk(name=name, branch=branch)
        return f"desk {name} seats {branch}"

    def remove(self, name: str) -> str:
        desk = self.desks.get(name)
        if desk is None:
            raise Missing(f"desk {name} does not exist")
        if desk.locked:
            raise Invalid(
                f"desk {name} is locked: {desk.note}; "
                "sweep around it"
            )
        del self.desks[name]
        return f"desk {name} cleared; {desk.branch} stands"

    def lock(self, name: str, note: str) -> str:
        desk = self.desks.get(name)
        if desk is None:
            raise Missing(f"desk {name} does not exist")
        if not note.strip():
            raise Invalid(
                "a lock without a note leaves March "
                "wondering whether January's reason "
                "retired"
            )
        desk.locked = True
        desk.note = note
        return f"desk {name} locked: {note}"

    def unlock(self, name: str) -> str:
        desk = self.desks.get(name)
        if desk is None:
            raise Missing(f"desk {name} does not exist")
        if not desk.locked:
            return f"desk {name} was not locked"
        desk.locked = False
        desk.note = ""
        return f"desk {name} unlocked"

    def relocate(self, name: str, branch: str) -> str:
        desk = self.desks.get(name)
        if desk is None:
            raise Missing(f"desk {name} does not exist")
        if desk.locked:
            raise Invalid(
                f"desk {name} is locked: {desk.note}; "
                "relocation waits"
            )
        if branch not in self.repo.refs.branches:
            raise Missing(f"{branch} is not a branch here")
        seated = self._seated(branch)
        if seated is not None and seated.name != name:
            raise Invalid(
                f"{branch} already sits at desk "
                f"{seated.name}; the one-desk rule does "
                "not bend for moves"
            )
        was = desk.branch
        desk.branch = branch
        return f"desk {name}: {was} -> {branch}"

    def prune(self) -> str:
        gone = [
            desk
            for desk in self.desks.values()
            if desk.branch not in self.repo.refs.branches
        ]
        swept = []
        spared = []
        for desk in gone:
            if desk.locked:
                spared.append(
                    f"{desk.name} (locked: {desk.note})"
                )
            else:
                del self.desks[desk.name]
                swept.append(desk.name)
        report = (
            f"pruned {len(swept)} desk(s), stepped around "
            f"{len(spared)} locked one(s)"
        )
        if swept:
            report += "; swept: " + ", ".join(sorted(swept))
        if spared:
            report += "; spared: " + ", ".join(
                sorted(spared)
            )
        return report

    def listing(self) -> str:
        if not self.desks:
            return "no desks; one directory, one life"
        lines = [f"{len(self.desks)} desk(s):"]
        for name in sorted(self.desks):
            desk = self.desks[name]
            state = (
                f" [locked: {desk.note}]"
                if desk.locked
                else ""
            )
            lines.append(
                f"  {name}: {desk.branch}{state}"
            )
        return "\n".join(lines)
