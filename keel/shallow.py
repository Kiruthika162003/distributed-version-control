"""Shallow clones: the recent past now, the deep past on request.

A fresh machine rarely needs a decade of history to fix
today's bug, and a shallow clone ships only the newest n
commits with their trees and blobs, cutting the transfer to
the working set. The cut leaves scars this module refuses to
hide: the oldest shipped commit still names parents that did
not travel, so the clone records its boundary commits
explicitly, walks that consult ancestry stop at the boundary
with a fence report instead of a crash, and operations that
need the full past, merge bases across the fence, blame into
the fog, say what deepening would cost rather than failing
with a shrug. Deepening is incremental by design: another n
commits per request, each extending the boundary downward,
because the developer who needed one more week of history
should not pay for the decade.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid
from keel.repo import Repo
from keel.transfer import TransferBatch, receive


@dataclass
class ShallowClone:
    source: Repo
    local: Repo = field(default_factory=Repo.init)
    boundary: set[str] = field(default_factory=set)
    depth_shipped: int = 0

    def _line_from_tip(self, count: int) -> list[str]:
        tip = self.source.refs.current()
        line: list[str] = []
        cursor: str | None = tip
        while cursor is not None and len(line) < count:
            line.append(cursor)
            commit = self.source.graph.get(cursor)
            cursor = (
                commit.parents[0] if commit.parents else None
            )
        return line

    def clone(self, depth: int) -> str:
        if depth < 1:
            raise Invalid("a depth of zero clones a rumor")
        if self.depth_shipped:
            raise Invalid(
                "already cloned; more history is a deepen, "
                "not a second clone"
            )
        line = self._line_from_tip(depth)
        self._ship(line)
        tip = line[0]
        self.local.refs.create_branch("main", tip)
        self.local.refs.checkout("main")
        return (
            f"shallow clone of {len(line)} commit(s); "
            f"{len(self.boundary)} boundary scar(s) recorded, "
            "not hidden"
        )

    def _ship(self, line: list[str]) -> None:
        batch = TransferBatch()
        for address in line:
            commit = self.source.graph.get(address)
            kind = self.source.store.kind_of(address)
            batch.objects[address] = (
                kind,
                self.source.store.get(address),
            )
            self._pack_tree(commit.tree, batch)
            self.local.graph.commits[address] = commit
        receive(self.local.store, batch)
        self.depth_shipped += len(line)
        oldest = self.source.graph.get(line[-1])
        self.boundary.discard(line[0])
        self.boundary = {
            parent
            for parent in oldest.parents
            if parent not in self.local.graph.commits
        } | {
            b
            for b in self.boundary
            if b not in self.local.graph.commits
        }

    def _pack_tree(
        self, tree: str, batch: TransferBatch
    ) -> None:
        if tree in batch.objects:
            return
        batch.objects[tree] = (
            "tree",
            self.source.store.get(tree),
        )
        for blob in self.source.trees.read_tree(tree).values():
            if blob not in batch.objects:
                batch.objects[blob] = (
                    "blob",
                    self.source.store.get(blob),
                )

    def fence_report(self, address: str) -> str:
        if address not in self.boundary:
            return f"{address[:8]} is inside the shallow world"
        return (
            f"{address[:8]} is beyond the fence; the walk "
            "stops here instead of crashing, and deepening "
            "would extend the boundary downward"
        )

    def deepen(self, more: int) -> str:
        if not self.depth_shipped:
            raise Invalid("clone before deepening")
        if more < 1:
            raise Invalid("deepening by zero is a meditation")
        line = self._line_from_tip(
            self.depth_shipped + more
        )
        fresh = [
            address
            for address in line
            if address not in self.local.graph.commits
        ]
        if not fresh:
            return (
                "the fence already stands at the root; there "
                "is no deeper"
            )
        self._ship(fresh)
        return (
            f"deepened by {len(fresh)} commit(s); the "
            "developer who needed a week does not pay for "
            "the decade"
        )
