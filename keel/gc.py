"""Garbage collection: unreachable is a verdict, and the reflog gets a vote.

Objects become garbage by losing every path from a ref, and
the collector's first job is not deletion but the honest
census: everything reachable from branches, tags, and, this
is the part that saves careers, the reflog, because the
commit a developer reset away an hour ago is unreachable from
every ref and is also exactly the commit they will want back
before lunch. The grace mechanism is structural rather than
temporal: reflog entries pin their addresses until the log is
explicitly trimmed, so nothing the journal remembers can be
collected, and the deletion pass reports what it freed by
kind, since "gc freed space" without an itemized bill is how
collectors earn distrust one mysterious shrink at a time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from keel.errors import Invalid
from keel.repo import Repo
from keel.tags import TagStore

_ADDRESS_PATTERN = re.compile(r"\b[0-9a-f]{8}\b")


@dataclass
class Collector:
    repo: Repo
    tags: TagStore | None = None

    def _tree_closure(self, tree: str, found: set[str]) -> None:
        if tree in found:
            return
        found.add(tree)
        for blob in self.repo.trees.read_tree(tree).values():
            found.add(blob)

    def _commit_closure(self, tip: str, found: set[str]) -> None:
        for address in self.repo.graph.ancestors(tip):
            if address in found:
                continue
            found.add(address)
            self._tree_closure(
                self.repo.graph.get(address).tree, found
            )

    def reachable(self) -> set[str]:
        found: set[str] = set()
        for tip in self.repo.refs.branches.values():
            self._commit_closure(tip, found)
        if self.tags is not None:
            for name in list(self.tags.tags):
                self._commit_closure(
                    self.tags.resolve(name), found
                )
        for entry in self.repo.refs.reflog:
            for prefix in _ADDRESS_PATTERN.findall(entry):
                full = self._expand(prefix)
                if full is not None:
                    self._commit_closure(full, found)
        return found

    def _expand(self, prefix: str) -> str | None:
        matches = [
            address
            for address in self.repo.graph.commits
            if address.startswith(prefix)
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def census(self) -> str:
        held = set(self.repo.store.objects)
        alive = self.reachable() & held
        dead = held - self.reachable()
        return (
            f"{len(held)} object(s) held, {len(alive)} "
            f"reachable, {len(dead)} unreachable; the reflog "
            "pins what the journal remembers"
        )

    def collect(self) -> str:
        alive = self.reachable()
        doomed = [
            address
            for address in self.repo.store.objects
            if address not in alive
        ]
        freed_by_kind: dict[str, int] = {}
        for address in doomed:
            kind = self.repo.store.kind_of(address)
            freed_by_kind[kind] = (
                freed_by_kind.get(kind, 0) + 1
            )
            del self.repo.store.objects[address]
            self.repo.graph.commits.pop(address, None)
        if not doomed:
            return "nothing unreachable; the census was the work"
        bill = ", ".join(
            f"{count} {kind}(s)"
            for kind, count in sorted(freed_by_kind.items())
        )
        return (
            f"freed {len(doomed)} object(s): {bill}; an "
            "itemized bill, because mysterious shrinks earn "
            "distrust"
        )

    def trim_reflog(self, keep_last: int) -> str:
        if keep_last < 1:
            raise Invalid(
                "keeping zero reflog entries deletes the "
                "safety net while standing on it"
            )
        dropped = max(
            0, len(self.repo.refs.reflog) - keep_last
        )
        self.repo.refs.reflog = self.repo.refs.reflog[
            -keep_last:
        ]
        return (
            f"reflog trimmed by {dropped} entrie(s); what the "
            "journal forgets, the next collection may take"
        )
