"""Refs: branches are movable names, and every move leaves a footprint.

An address is truth but nobody types truth; branches give
commits names that move, HEAD says which name is current, and
the entire mutable surface of the repository is this one small
table, everything else being immutable objects. Because the
table is the only thing that can change, it is the only thing
that needs a journal: every ref move lands in the reflog with
what moved, from where, to where, and why, so "my commits
disappeared" is answered by reading, not by archaeology.
Deletion protects the current branch, force-moves are legal
but logged as force-moves, and a branch name must say
something: the rules are few because the table is small, and
the table is small because that is the design working.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from keel.errors import Detached, Invalid, Missing

_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9/_.-]{0,79}$")


@dataclass
class RefStore:
    branches: dict[str, str] = field(default_factory=dict)
    head: str | None = None
    detached_at: str | None = None
    reflog: list[str] = field(default_factory=list)

    def create_branch(self, name: str, address: str) -> str:
        if not _NAME_PATTERN.match(name):
            raise Invalid(
                f"{name!r} is not a branch name; lowercase, "
                "digits, and separators, starting plain"
            )
        if name in self.branches:
            raise Invalid(
                f"{name} exists; moving it is an update, not a "
                "creation"
            )
        self.branches[name] = address
        self.reflog.append(
            f"branch {name} created at {address[:8]}"
        )
        return f"{name} -> {address[:8]}"

    def move(
        self,
        name: str,
        new_address: str,
        reason: str,
        force: bool = False,
    ) -> str:
        held = self.branches.get(name)
        if held is None:
            raise Missing(f"{name} is not a branch")
        label = "force-moved" if force else "moved"
        self.branches[name] = new_address
        self.reflog.append(
            f"branch {name} {label} {held[:8]} -> "
            f"{new_address[:8]}: {reason}"
        )
        return f"{name} {label} to {new_address[:8]}"

    def delete(self, name: str) -> str:
        if name not in self.branches:
            raise Missing(f"{name} is not a branch")
        if name == self.head:
            raise Invalid(
                f"{name} is the current branch; sawing off the "
                "branch you sit on is refused"
            )
        address = self.branches.pop(name)
        self.reflog.append(
            f"branch {name} deleted at {address[:8]}"
        )
        return f"{name} deleted; the reflog remembers"

    def checkout(self, name: str) -> str:
        if name not in self.branches:
            raise Missing(f"{name} is not a branch")
        self.head = name
        self.detached_at = None
        self.reflog.append(f"HEAD -> {name}")
        return f"on {name}"

    def detach(self, address: str) -> str:
        self.head = None
        self.detached_at = address
        self.reflog.append(f"HEAD detached at {address[:8]}")
        return (
            f"HEAD detached at {address[:8]}; commits made "
            "here need a branch before they have a name"
        )

    def current(self) -> str:
        if self.head is not None:
            return self.branches[self.head]
        if self.detached_at is not None:
            return self.detached_at
        raise Detached("HEAD points nowhere; check out a branch")

    def current_branch(self) -> str:
        if self.head is None:
            raise Detached(
                "the operation needs a branch and HEAD is "
                "not on one"
            )
        return self.head

    def recent_log(self, count: int = 5) -> list[str]:
        return self.reflog[-count:]
