from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.stash import Stash

WORK = {"app.py": b"half done", "notes.txt": b"ideas"}


def loaded() -> Stash:
    stash = Stash()
    stash.push(dict(WORK), branch="feature", label="wip parser")
    return stash


class TestTheShelf:
    def test_shelving_names_the_label_and_the_branch(self):
        stash = Stash()
        receipt = stash.push(
            dict(WORK), branch="feature", label="wip parser"
        )
        assert receipt == (
            "shelved 2 file(s) as 'wip parser' from feature"
        )

    def test_the_unlabeled_shelf_is_refused(self):
        with pytest.raises(Invalid) as caught:
            Stash().push(dict(WORK), "main", "  ")
        assert "write-only storage" in str(caught.value)

    def test_an_empty_working_copy_has_nothing_to_shelve(self):
        with pytest.raises(Invalid):
            Stash().push({}, "main", "nothing")


class TestApplyAndPop:
    def test_apply_keeps_and_pop_removes(self):
        stash = loaded()
        files, _ = stash.apply(current_branch="feature")
        assert files == WORK
        assert len(stash.entries) == 1
        files, receipt = stash.pop(current_branch="feature")
        assert files == WORK
        assert receipt.endswith("entry removed")
        assert stash.entries == []

    def test_the_wrong_ground_warns_in_the_receipt(self):
        stash = loaded()
        _, receipt = stash.apply(current_branch="main")
        assert "WARNING: shelved on feature" in receipt
        assert "the ground it stood on" in receipt

    def test_the_empty_shelf_is_missing(self):
        with pytest.raises(Missing):
            Stash().pop("main")


class TestDropAndList:
    def test_dropping_names_what_it_abandons(self):
        stash = loaded()
        verdict = stash.drop(0)
        assert "abandoning 2 file(s)" in verdict
        assert "never loses anything quietly" in verdict

    def test_the_listing_reads_like_a_shelf(self):
        stash = loaded()
        stash.push(
            {"b.txt": b"x"}, branch="main", label="quick fix"
        )
        listing = stash.listing()
        assert listing[0] == (
            "[0] 'wip parser' from feature (2 file(s))"
        )
        assert listing[1].startswith("[1] 'quick fix'")

    def test_off_the_shelf_indices_are_missing(self):
        with pytest.raises(Missing):
            loaded().drop(5)
