"""Commits: history is a DAG of snapshots, and ancestry is arithmetic.

A commit binds a tree address to its parents and a message,
and because the parents are part of the digested bytes, the
past is load-bearing: rewriting any ancestor changes every
descendant's address, which is the entire integrity story told
in one sentence. Commits here carry a sequence number stamped
by the repository rather than a wall clock, because two
machines disagree about time but nobody disagrees about the
order a single repository accepted commits in, and every
"history looks reordered" bug report traces back to trusting
timestamps. The merge base is the lowest common ancestor
found by walking generations backward, and when two candidate
bases are equally low the tie is refused rather than silently
picked, since a criss-cross merge resolved by coin flip is
how the same conflict returns every week wearing new line
numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.objects import COMMIT, ObjectStore


@dataclass(frozen=True)
class Commit:
    address: str
    tree: str
    parents: tuple[str, ...]
    message: str
    sequence: int


@dataclass
class CommitGraph:
    store: ObjectStore
    commits: dict[str, Commit] = field(default_factory=dict)
    next_sequence: int = 0

    def create(
        self,
        tree: str,
        parents: tuple[str, ...],
        message: str,
    ) -> Commit:
        if not message.strip():
            raise Invalid(
                "an empty message records that nothing was "
                "worth saying; say the thing"
            )
        for parent in parents:
            if parent not in self.commits:
                raise Missing(
                    f"parent {parent} is not a commit here"
                )
        payload = (
            f"tree={tree}\n"
            f"parents={','.join(parents)}\n"
            f"seq={self.next_sequence}\n"
            f"message={message}"
        ).encode()
        address = self.store.put(COMMIT, payload)
        commit = Commit(
            address=address,
            tree=tree,
            parents=parents,
            message=message,
            sequence=self.next_sequence,
        )
        self.commits[address] = commit
        self.next_sequence += 1
        return commit

    def get(self, address: str) -> Commit:
        commit = self.commits.get(address)
        if commit is None:
            raise Missing(f"{address} is not a commit here")
        return commit

    def ancestors(self, address: str) -> set[str]:
        seen: set[str] = set()
        frontier = [address]
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(self.get(current).parents)
        return seen

    def is_ancestor(self, older: str, newer: str) -> bool:
        return older in self.ancestors(newer)

    def merge_base(self, left: str, right: str) -> str:
        common = self.ancestors(left) & self.ancestors(right)
        if not common:
            raise Missing(
                "these histories share no ancestor; they are "
                "strangers, not branches"
            )
        best = [
            address
            for address in common
            if not any(
                address in self.get(other).parents
                or (
                    address != other
                    and address in self.ancestors(other)
                )
                for other in common
            )
        ]
        if len(best) > 1:
            names = ", ".join(
                sorted(a[:8] for a in best)
            )
            raise Invalid(
                f"criss-cross history: {names} are equally "
                "good merge bases, and resolving that by coin "
                "flip is how the same conflict returns weekly"
            )
        return best[0]

    def log(self, address: str) -> list[Commit]:
        found = [
            self.get(a) for a in self.ancestors(address)
        ]
        found.sort(key=lambda commit: -commit.sequence)
        return found
