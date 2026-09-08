from __future__ import annotations

import pytest

from keel.branchdiff import (
    only_theirs,
    render,
    since_we_parted,
)
from keel.errors import Missing
from keel.repo import Repo

BASE = {"app.py": b"core\n"}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nshared\n"}),
        "shared work",
    )
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    repo.commit(
        dict(
            BASE, **{"app.py": b"core\nshared\nf1\n"}
        ),
        "feature one",
    )
    repo.commit(
        dict(
            BASE,
            **{"app.py": b"core\nshared\nf1\nf2\n"},
        ),
        "feature two",
    )
    repo.refs.checkout("main")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nshared\nm1\n"}),
        "main one",
    )
    return repo


class TestPossession:
    def test_what_theirs_has_that_ours_lacks(self):
        repo = build()
        commits = only_theirs(repo, "main", "feature")
        assert [
            c.message for c in commits
        ] == ["feature two", "feature one"]

    def test_possession_is_directional(self):
        repo = build()
        commits = only_theirs(repo, "feature", "main")
        assert [c.message for c in commits] == [
            "main one"
        ]

    def test_holding_everything_says_so(self):
        repo = build()
        page = render(repo, "main", "main", "only_theirs")
        assert "already holds all of main" in page


class TestDivergence:
    def test_both_sides_since_the_fork(self):
        repo = build()
        ours, theirs, fork = since_we_parted(
            repo, "main", "feature"
        )
        assert [c.message for c in ours] == ["main one"]
        assert [c.message for c in theirs] == [
            "feature two",
            "feature one",
        ]
        assert (
            repo.graph.get(fork).message == "shared work"
        )

    def test_the_page_repeats_its_question(self):
        repo = build()
        page = render(
            repo, "main", "feature", "since_we_parted"
        )
        assert "the review question" in page
        assert "main did:" in page
        assert "feature did:" in page
        assert "feature two" in page

    def test_dots_are_not_a_question(self):
        repo = build()
        with pytest.raises(Missing) as caught:
            render(repo, "main", "feature", "a..b")
        assert "dots are a trap" in str(caught.value)
