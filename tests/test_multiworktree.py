from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.multiworktree import WorktreeSet
from keel.repo import Repo


def build() -> tuple[Repo, WorktreeSet]:
    repo = Repo.init()
    repo.commit({"app.py": b"core\n"}, "base")
    repo.branch_from_head("feature")
    repo.branch_from_head("hotfix")
    return repo, WorktreeSet(repo=repo)


class TestSeating:
    def test_desks_seat_branches(self):
        _repo, desks = build()
        assert desks.add("den", "main") == (
            "desk den seats main"
        )
        desks.add("porch", "feature")
        assert "2 desk(s):" in desks.listing()

    def test_one_branch_one_desk(self):
        _repo, desks = build()
        desks.add("den", "main")
        with pytest.raises(Invalid) as caught:
            desks.add("porch", "main")
        assert "one desk lies" in str(caught.value)

    def test_a_stranger_branch_is_refused(self):
        _repo, desks = build()
        with pytest.raises(Missing):
            desks.add("den", "ghost")

    def test_relocation_honors_the_same_rule(self):
        _repo, desks = build()
        desks.add("den", "main")
        desks.add("porch", "feature")
        with pytest.raises(Invalid) as caught:
            desks.relocate("porch", "main")
        assert "does not bend for moves" in str(
            caught.value
        )
        receipt = desks.relocate("porch", "hotfix")
        assert receipt == "desk porch: feature -> hotfix"


class TestLocks:
    def test_a_lock_needs_a_note(self):
        _repo, desks = build()
        desks.add("den", "main")
        with pytest.raises(Invalid) as caught:
            desks.lock("den", "  ")
        assert "January's reason retired" in str(
            caught.value
        )
        desks.lock("den", "mid-bisect, do not sweep")
        assert "[locked: mid-bisect" in desks.listing()

    def test_a_locked_desk_refuses_removal_and_moves(self):
        _repo, desks = build()
        desks.add("den", "main")
        desks.lock("den", "mid-bisect")
        with pytest.raises(Invalid):
            desks.remove("den")
        with pytest.raises(Invalid):
            desks.relocate("den", "feature")
        desks.unlock("den")
        assert desks.remove("den").startswith(
            "desk den cleared"
        )


class TestPruning:
    def test_the_janitor_reads_the_signs(self):
        repo, desks = build()
        desks.add("den", "feature")
        desks.add("porch", "hotfix")
        desks.lock("porch", "half-built release")
        repo.refs.delete("feature")
        repo.refs.delete("hotfix")
        report = desks.prune()
        assert (
            "pruned 1 desk(s), stepped around 1 locked "
            "one(s)"
        ) in report
        assert "swept: den" in report
        assert "spared: porch (locked: half-built" in report
        assert "den" not in desks.desks
        assert "porch" in desks.desks

    def test_an_empty_floor_reports_one_life(self):
        _repo, desks = build()
        assert desks.listing() == (
            "no desks; one directory, one life"
        )
