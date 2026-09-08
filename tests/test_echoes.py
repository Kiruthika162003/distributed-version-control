from __future__ import annotations

from keel.echoes import find_echoes, report
from keel.repo import Repo

BASE = {"app.py": b"core\n", "conf.ini": b"x=1\n"}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.commit(
        dict(BASE, **{"conf.ini": b"x=2\n"}),
        "raise the limit",
    )
    repo.commit(
        dict(BASE, **{"conf.ini": b"x=2\n",
                      "app.py": b"core\nmore\n"}),
        "unrelated growth",
    )
    repo.commit(
        dict(BASE, **{"app.py": b"core\nmore\n"}),
        "walk the limit back by hand",
    )
    return repo


class TestTheHunt:
    def test_the_hand_made_undo_is_found_by_content(
        self,
    ):
        repo = build()
        echoes = find_echoes(repo, repo.refs.current())
        assert len(echoes) == 1
        early, late, distance = echoes[0]
        assert repo.graph.get(early).message == (
            "raise the limit"
        )
        assert repo.graph.get(late).message == (
            "walk the limit back by hand"
        )
        assert distance == 2

    def test_partial_undos_are_not_echoes(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        repo.commit(
            dict(
                BASE,
                **{
                    "conf.ini": b"x=2\n",
                    "app.py": b"core\n2\n",
                },
            ),
            "two changes",
        )
        repo.commit(
            dict(BASE, **{"app.py": b"core\n2\n"}),
            "one walked back",
        )
        assert (
            find_echoes(repo, repo.refs.current()) == []
        )


class TestTheReport:
    def test_the_pace_is_judged_by_distance(self):
        repo = build()
        page = report(repo, repo.refs.current())
        assert page.startswith(
            "1 echo(es), commits that sum to silence:"
        )
        assert (
            "'raise the limit'" in page
            and "unsaid by" in page
        )
        assert "2 commit(s) apart" in page
        assert "a quick correction" in page
        assert "findings, not errors" in page

    def test_nothing_unsaid_reads_quiet(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        repo.commit(
            dict(BASE, **{"app.py": b"core\n2\n"}),
            "forward only",
        )
        assert report(repo, repo.refs.current()) == (
            "no echoes; nothing here has been unsaid"
        )
