"""Fsck: the full physical, because trust is a schedule, not a feeling.

The store checks each object at read time, but read-time
checks only audit what gets read, and the object nobody has
opened since March is exactly where rot hides. The physical
walks everything: every object re-digested against its
address, every tree's children present and of the declared
kind, every commit's parents and tree resolvable, and the
findings are sorted by blast radius, because a corrupt blob
breaks one file while a corrupt tree orphans a subtree and a
missing commit amputates history. Dangling objects, reachable
from nothing, are reported as a separate species rather than
an error, since they are usually the harmless exhaust of
normal work, and an fsck that cries wolf over exhaust teaches
people to skip the physical, which is how the March object
stays rotten until September.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.objects import COMMIT, TREE, digest_bytes
from keel.repo import Repo
from keel.trees import _parse_entries


@dataclass
class Physical:
    repo: Repo
    corrupt: list[str] = field(default_factory=list)
    broken_links: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)

    def _check_integrity(self) -> None:
        for address, (kind, payload) in (
            self.repo.store.objects.items()
        ):
            if digest_bytes(kind, payload) != address:
                self.corrupt.append(
                    f"{address[:8]} ({kind}): bytes no longer "
                    "match the address"
                )

    def _check_links(self) -> None:
        for address, (kind, payload) in (
            self.repo.store.objects.items()
        ):
            if kind == TREE:
                self._check_tree_links(address, payload)
            elif kind == COMMIT:
                self._check_commit_links(address)

    def _check_tree_links(
        self, address: str, payload: bytes
    ) -> None:
        for name, kind, child in _parse_entries(payload):
            if child not in self.repo.store.objects:
                self.broken_links.append(
                    f"tree {address[:8]}: entry {name} points "
                    f"at missing {child[:8]}; the subtree is "
                    "orphaned"
                )
            elif self.repo.store.kind_of(child) != kind:
                self.broken_links.append(
                    f"tree {address[:8]}: entry {name} claims "
                    f"{kind} but the store holds a "
                    f"{self.repo.store.kind_of(child)}"
                )

    def _check_commit_links(self, address: str) -> None:
        commit = self.repo.graph.commits.get(address)
        if commit is None:
            return
        if commit.tree not in self.repo.store.objects:
            self.broken_links.append(
                f"commit {address[:8]}: tree {commit.tree[:8]} "
                "is missing; the snapshot is gone"
            )
        for parent in commit.parents:
            if parent not in self.repo.store.objects:
                self.broken_links.append(
                    f"commit {address[:8]}: parent "
                    f"{parent[:8]} is missing; history is "
                    "amputated here"
                )

    def _tree_closure(
        self, tree: str, reachable: set[str]
    ) -> None:
        if tree in reachable:
            return
        reachable.add(tree)
        _, payload = self.repo.store.objects[tree]
        for _name, kind, child in _parse_entries(payload):
            if kind == TREE:
                self._tree_closure(child, reachable)
            else:
                reachable.add(child)

    def _check_dangling(self) -> None:
        reachable: set[str] = set()
        for tip in self.repo.refs.branches.values():
            for commit_address in self.repo.graph.ancestors(
                tip
            ):
                reachable.add(commit_address)
                commit = self.repo.graph.get(commit_address)
                self._tree_closure(commit.tree, reachable)
        for address in self.repo.store.objects:
            if address not in reachable:
                self.dangling.append(address)

    def run(self) -> str:
        self._check_integrity()
        self._check_links()
        if not self.corrupt and not self.broken_links:
            self._check_dangling()
        findings = len(self.corrupt) + len(self.broken_links)
        if findings == 0:
            return (
                f"physical clean: "
                f"{len(self.repo.store.objects)} object(s) "
                f"verified, {len(self.dangling)} dangling "
                "(harmless exhaust, not an error)"
            )
        lines = [
            f"{findings} finding(s), sorted by blast radius:"
        ]
        lines.extend(
            f"  {entry}" for entry in self.broken_links
        )
        lines.extend(f"  {entry}" for entry in self.corrupt)
        return "\n".join(lines)
