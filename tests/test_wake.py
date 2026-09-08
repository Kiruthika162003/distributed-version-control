from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.repo import Repo
from keel.wake import report, wake_of

BASE = {"app.py": b"core\n"}


def build() -> tuple[Repo, list[str]]:
    repo = Repo.init()
    root = repo.commit(dict(BASE), "the root")
    middle = repo.commit(
        dict(BASE, **{"app.py": b"core\nmid\n"}),
        "the middle",
    )
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nmid\nf\n"}),
        "feature work",
    )
    repo.refs.checkout("main")
    tip = repo.commit(
        dict(BASE, **{"app.py": b"core\nmid\nm\n"}),
        "main work",
    )
    return repo, [
        root.address,
        middle.address,
        tip.address,
    ]


class TestTheWake:
    def test_the_middle_carries_both_lines(self):
        repo, addresses = build()
        wake = wake_of(repo, addresses[1])
        assert len(wake) == 2
        assert addresses[2] in wake

    def test_the_tip_has_an_empty_wake(self):
        repo, addresses = build()
        page = report(repo, addresses[2])
        assert "0 commit(s)" in page
        assert (
            "safe to rewrite, nobody is standing "
            "downstream"
        ) in page

    def test_riding_branches_are_conversations(self):
        repo, addresses = build()
        page = report(repo, addresses[1])
        assert (
            "branch tips riding in it: feature, main"
        ) in page
        assert (
            "a conversation before any history moves"
        ) in page

    def test_the_root_owns_the_whole_repository(self):
        repo, addresses = build()
        page = report(repo, addresses[0])
        assert "3 commit(s)" in page
        assert (
            "people who enjoy migrations"
        ) in page

    def test_a_stranger_has_no_wake_to_ask_about(self):
        repo, _addresses = build()
        with pytest.raises(Missing):
            wake_of(repo, "0" * 20)
