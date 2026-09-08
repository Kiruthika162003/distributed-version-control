"""Submodules: another repository, pinned by exact commit, updated on purpose.

Depending on another repository is easy; depending on a
moving one is how builds break on Tuesdays for Friday's
reasons, so the submodule record pins an exact commit of the
child inside the parent's tree, and the pin only moves when
someone moves it in a parent commit of its own. The status
report tells the three truths apart by name: in sync, child
checked out behind the pin, and child ahead of the pin, the
last being the dangerous one because work committed in the
child but not pinned in the parent is invisible to every
clone of the parent, finished and unshipped at once. Updating
the pin requires the child commit to exist and be reachable
in the child, since pinning an unreachable address ships a
treasure map to a vault that garbage collection already
emptied.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.repo import Repo


@dataclass
class SubmoduleSet:
    parent: Repo
    children: dict[str, Repo] = field(default_factory=dict)
    pins: dict[str, str] = field(default_factory=dict)

    def add(self, path: str, child: Repo) -> str:
        if path in self.children:
            raise Invalid(f"{path} is already a submodule")
        tip = child.refs.current()
        self.children[path] = child
        self.pins[path] = tip
        return (
            f"{path} pinned at {tip[:8]}; the pin moves only "
            "when someone moves it on purpose"
        )

    def update_pin(self, path: str, address: str) -> str:
        child = self._child(path)
        if address not in child.graph.commits:
            raise Missing(
                f"{address[:8]} is not a commit in {path}; "
                "pinning it ships a treasure map to a vault "
                "that collection already emptied"
            )
        reachable = any(
            address in child.graph.ancestors(tip)
            for tip in child.refs.branches.values()
        )
        if not reachable:
            raise Invalid(
                f"{address[:8]} is unreachable in {path}; "
                "the same treasure map problem wearing a "
                "subtler coat"
            )
        old = self.pins[path]
        self.pins[path] = address
        return f"{path}: pin moved {old[:8]} -> {address[:8]}"

    def _child(self, path: str) -> Repo:
        child = self.children.get(path)
        if child is None:
            raise Missing(f"{path} is not a submodule")
        return child

    def status(self, path: str) -> str:
        child = self._child(path)
        pin = self.pins[path]
        checked_out = child.refs.current()
        if checked_out == pin:
            return f"{path}: in sync at {pin[:8]}"
        if child.graph.is_ancestor(checked_out, pin):
            return (
                f"{path}: checked out behind the pin; an "
                "update in the child fixes it"
            )
        if child.graph.is_ancestor(pin, checked_out):
            return (
                f"{path}: child is AHEAD of the pin; work "
                "committed there is invisible to every clone "
                "of the parent, finished and unshipped at "
                "once"
            )
        return (
            f"{path}: pin and checkout have diverged; "
            "somebody rewrote the child under the parent"
        )

    def report(self) -> str:
        if not self.children:
            return "no submodules; every line is first-party"
        return "\n".join(
            self.status(path)
            for path in sorted(self.children)
        )
