from __future__ import annotations

import pytest

from keel.errors import Detached, Invalid, Missing
from keel.refs import RefStore


def refs() -> RefStore:
    store = RefStore()
    store.create_branch("main", "aaaa1111aaaa1111aaaa")
    store.checkout("main")
    return store


class TestBranches:
    def test_names_have_a_grammar(self):
        store = RefStore()
        for name in ("Main", "-lead", "", "a b"):
            with pytest.raises(Invalid):
                store.create_branch(name, "feedface")

    def test_creation_is_not_an_update(self):
        store = refs()
        with pytest.raises(Invalid) as caught:
            store.create_branch("main", "bbbb")
        assert "an update, not a creation" in str(caught.value)

    def test_the_current_branch_cannot_be_deleted(self):
        store = refs()
        with pytest.raises(Invalid) as caught:
            store.delete("main")
        assert "sawing off the branch you sit on" in str(
            caught.value
        )

    def test_other_branches_delete_with_a_memory(self):
        store = refs()
        store.create_branch("feature", "bbbb2222bbbb2222bbbb")
        assert "the reflog remembers" in store.delete("feature")


class TestHead:
    def test_current_resolves_through_the_branch(self):
        assert refs().current() == "aaaa1111aaaa1111aaaa"

    def test_detached_head_is_a_state_with_a_warning(self):
        store = refs()
        verdict = store.detach("cccc3333cccc3333cccc")
        assert "need a branch before they have a name" in verdict
        assert store.current() == "cccc3333cccc3333cccc"
        with pytest.raises(Detached):
            store.current_branch()

    def test_nowhere_is_not_a_place(self):
        with pytest.raises(Detached):
            RefStore().current()

    def test_checkout_requires_an_existing_branch(self):
        with pytest.raises(Missing):
            refs().checkout("ghost")


class TestTheReflog:
    def test_every_move_leaves_a_footprint(self):
        store = refs()
        store.move(
            "main",
            "dddd4444dddd4444dddd",
            reason="commit landed",
        )
        assert store.recent_log()[-1] == (
            "branch main moved aaaa1111 -> dddd4444: "
            "commit landed"
        )

    def test_force_moves_are_legal_but_labeled(self):
        store = refs()
        verdict = store.move(
            "main", "eeee5555eeee5555eeee",
            reason="history rewrite", force=True,
        )
        assert "force-moved" in verdict
        assert "force-moved" in store.recent_log()[-1]

    def test_disappeared_commits_are_answered_by_reading(self):
        store = refs()
        store.move("main", "ffff6666ffff6666ffff", reason="a")
        store.move("main", "abab7777abab7777abab", reason="b")
        trail = store.recent_log(count=2)
        assert len(trail) == 2
        assert all("branch main moved" in line for line in trail)
