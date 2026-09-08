from __future__ import annotations

from keel.fsck import Physical
from keel.objects import BLOB
from keel.repo import Repo

BASE = {"a.txt": b"one", "sub/b.txt": b"two"}


def healthy() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.commit(dict(BASE, **{"a.txt": b"three"}), "grow")
    return repo


class TestTheCleanPhysical:
    def test_a_healthy_store_verifies_everything(self):
        verdict = Physical(repo=healthy()).run()
        assert verdict.startswith("physical clean:")
        assert "0 dangling" in verdict

    def test_exhaust_is_reported_not_condemned(self):
        repo = healthy()
        repo.store.put(BLOB, b"scratch nobody references")
        verdict = Physical(repo=repo).run()
        assert "1 dangling (harmless exhaust, not an error)" in (
            verdict
        )


class TestFindings:
    def test_tampered_bytes_are_named_with_their_kind(self):
        repo = healthy()
        victim = next(
            address
            for address, (kind, _) in (
                repo.store.objects.items()
            )
            if kind == BLOB
        )
        kind, _ = repo.store.objects[victim]
        repo.store.objects[victim] = (kind, b"rotted")
        verdict = Physical(repo=repo).run()
        assert "bytes no longer match the address" in verdict

    def test_a_missing_tree_child_orphans_the_subtree(self):
        repo = healthy()
        blob = repo.trees.entry_at(
            repo.graph.get(repo.refs.current()).tree,
            "sub/b.txt",
        )
        del repo.store.objects[blob]
        verdict = Physical(repo=repo).run()
        assert "the subtree is orphaned" in verdict

    def test_a_missing_parent_amputates_history(self):
        repo = healthy()
        tip = repo.refs.current()
        parent = repo.graph.get(tip).parents[0]
        del repo.store.objects[parent]
        verdict = Physical(repo=repo).run()
        assert "history is amputated here" in verdict
