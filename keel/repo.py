"""The repository: four small machines under one roof, none reaching around.

A repository is the object store, the tree builder, the commit
graph, and the ref table, wired so that each layer talks only
to its neighbor: commits hold tree addresses but never open
trees, refs hold commit addresses but never read commits, and
the facade methods here are thin on purpose, because a facade
that grows logic becomes a fifth machine nobody designed. The
one rule enforced at this level is the empty-commit refusal:
committing a tree identical to the parent's records that
nothing changed, and a history padded with nothing-changed
entries is a log that lies by volume. Snapshots go in as
plain path-to-bytes maps and come out the same way, since the
working copy is the caller's business and pretending to own
it would drag a filesystem into every test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import Commit, CommitGraph
from keel.errors import Invalid
from keel.objects import BLOB, ObjectStore
from keel.refs import RefStore
from keel.trees import TreeBuilder, diff_trees


@dataclass
class Repo:
    store: ObjectStore = field(default_factory=ObjectStore)
    refs: RefStore = field(default_factory=RefStore)

    def __post_init__(self) -> None:
        self.trees = TreeBuilder(store=self.store)
        self.graph = CommitGraph(store=self.store)

    @classmethod
    def init(cls) -> Repo:
        return cls()

    def snapshot_tree(self, files: dict[str, bytes]) -> str:
        blobs = {
            path: self.store.put(BLOB, content)
            for path, content in files.items()
        }
        return self.trees.write_tree(blobs)

    def commit(
        self, files: dict[str, bytes], message: str
    ) -> Commit:
        tree = self.snapshot_tree(files)
        parents: tuple[str, ...] = ()
        if self.refs.branches or self.refs.detached_at:
            parents = (self.refs.current(),)
        if parents:
            parent_tree = self.graph.get(parents[0]).tree
            if parent_tree == tree:
                raise Invalid(
                    "this snapshot is identical to the parent; "
                    "a history padded with nothing-changed "
                    "entries is a log that lies by volume"
                )
        commit = self.graph.create(
            tree=tree, parents=parents, message=message
        )
        if not self.refs.branches:
            self.refs.create_branch("main", commit.address)
            self.refs.checkout("main")
        else:
            branch = self.refs.current_branch()
            self.refs.move(
                branch, commit.address, reason=message[:40]
            )
        return commit

    def files_at(self, address: str) -> dict[str, bytes]:
        commit = self.graph.get(address)
        blobs = self.trees.read_tree(commit.tree)
        return {
            path: self.store.get(blob)
            for path, blob in blobs.items()
        }

    def head_files(self) -> dict[str, bytes]:
        return self.files_at(self.refs.current())

    def branch_from_head(self, name: str) -> str:
        return self.refs.create_branch(
            name, self.refs.current()
        )

    def changes_between(
        self, old_address: str, new_address: str
    ) -> dict[str, str]:
        return diff_trees(
            self.trees,
            self.graph.get(old_address).tree,
            self.graph.get(new_address).tree,
        )

    def history(self) -> list[str]:
        return [
            f"{commit.address[:8]} {commit.message}"
            for commit in self.graph.log(self.refs.current())
        ]
