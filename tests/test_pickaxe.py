from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.pickaxe import pickaxe, survival_story
from keel.repo import Repo


def api_lifecycle() -> Repo:
    repo = Repo.init()
    repo.commit({"app.py": b"def main(): pass"}, "born")
    repo.commit(
        {
            "app.py": b"def main(): old_api()",
            "lib.py": b"def old_api(): pass",
        },
        "api introduced",
    )
    repo.commit(
        {
            "app.py": b"def main(): old_api()",
            "extra.py": b"old_api()",
            "lib.py": b"def old_api(): pass",
        },
        "second caller",
    )
    repo.commit(
        {
            "app.py": b"def main(): new_api()",
            "extra.py": b"new_api()",
            "lib.py": b"def new_api(): pass",
        },
        "the cleanup",
    )
    return repo


class TestTheHunt:
    def test_introduction_and_removal_are_split(self):
        repo = api_lifecycle()
        hits = pickaxe(repo, repo.refs.current(), b"old_api")
        directions = [hit.direction for hit in hits]
        assert directions == [
            "removed", "introduced", "introduced",
        ]

    def test_the_counts_ride_along(self):
        repo = api_lifecycle()
        hits = pickaxe(repo, repo.refs.current(), b"old_api")
        cleanup = hits[0]
        assert cleanup.count_before == 3
        assert cleanup.count_after == 0
        assert "(3 -> 0)" in cleanup.line()

    def test_a_move_without_count_change_is_invisible(self):
        repo = Repo.init()
        repo.commit({"a.py": b"needle"}, "here")
        repo.commit({"b.py": b"needle"}, "moved")
        hits = pickaxe(repo, repo.refs.current(), b"needle")
        assert [h.message for h in hits] == ["here"]

    def test_the_empty_needle_answers_nothing(self):
        repo = api_lifecycle()
        with pytest.raises(Invalid):
            pickaxe(repo, repo.refs.current(), b"  ")


class TestTheStory:
    def test_the_gone_needle_names_where_cleanup_finished(self):
        repo = api_lifecycle()
        story = survival_story(
            repo, repo.refs.current(), b"old_api"
        )
        assert "0 occurrence(s) today" in story
        assert "where the cleanup finished" in story

    def test_the_never_seen_needle_admits_both_readings(self):
        repo = api_lifecycle()
        story = survival_story(
            repo, repo.refs.current(), b"ghost_api"
        )
        assert "either it was always here or it never was" in (
            story
        )
