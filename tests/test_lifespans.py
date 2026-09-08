from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.lifespans import biography, census, graveyard
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"core\n", "utils.py": b"helpers\n"},
        "begin",
    )
    repo.commit(
        {"app.py": b"core\nmore\n"},
        "fold utils into app",
    )
    repo.commit(
        {
            "app.py": b"core\nmore\n",
            "utils.py": b"helpers return\n",
        },
        "regret the fold",
    )
    repo.commit(
        {"app.py": b"core\nmore\nfinal\n"},
        "fold utils again, resolved this time",
    )
    return repo, repo.refs.current()


class TestBiographies:
    def test_a_full_life_reads_in_order(self):
        repo, tip = build()
        story = biography(repo, tip, "utils.py")
        assert story.startswith("utils.py: born in ")
        assert "died in " in story
        assert "reborn in " in story
        assert story.index("born") < story.index("died")
        assert story.index("died") < story.index("reborn")
        assert story.endswith("currently dead")

    def test_a_living_path_says_so(self):
        repo, tip = build()
        story = biography(repo, tip, "app.py")
        assert "died" not in story
        assert story.endswith("currently living")

    def test_the_never_born_are_not_given_empty_lives(
        self,
    ):
        repo, tip = build()
        with pytest.raises(Missing) as caught:
            biography(repo, tip, "ghost.py")
        assert "a different claim" in str(caught.value)


class TestTheGraveyard:
    def test_burials_name_the_burying_commit(self):
        repo, tip = build()
        page = graveyard(repo, tip)
        assert page.startswith("1 path(s) at rest:")
        assert "utils.py, buried by" in page
        assert (
            "fold utils again, resolved this time"
        ) in page

    def test_an_empty_graveyard_says_everything_lives(
        self,
    ):
        repo = Repo.init()
        repo.commit({"app.py": b"core\n"}, "begin")
        assert graveyard(repo, repo.refs.current()) == (
            "the graveyard is empty; everything lives"
        )


class TestTheCensus:
    def test_the_counts_tell_the_whole_town(self):
        repo, tip = build()
        assert census(repo, tip) == (
            "2 path(s) ever lived: 1 living, 1 dead, "
            "1 came back at least once"
        )
