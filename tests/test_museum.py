from __future__ import annotations

from keel.museum import exhibits, tour
from keel.repo import Repo
from keel.salvage import dive


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {
            "app.py": b"core\n",
            "legacy.py": b"old but large\n" * 10,
            "tiny.py": b"t\n",
        },
        "the town",
    )
    repo.commit(
        {
            "app.py": b"core\n",
            "legacy.py": b"old but large\n" * 10,
        },
        "retire tiny; nobody imported it",
    )
    repo.commit(
        {"app.py": b"core\n"},
        "retire legacy; the rewrite shipped",
    )
    return repo


class TestTheExhibits:
    def test_each_exhibit_carries_its_dates_and_dive(
        self,
    ):
        repo = build()
        shown = exhibits(repo, repo.refs.current())
        assert [e["path"] for e in shown] == [
            "legacy.py",
            "tiny.py",
        ]
        legacy = shown[0]
        assert legacy["born_seq"] == 0
        assert legacy["buried_seq"] == 2
        assert legacy["size_at_death"] == 140
        assert legacy["reason"] == (
            "retire legacy; the rewrite shipped"
        )

    def test_the_dive_instructions_actually_work(self):
        repo = build()
        shown = exhibits(repo, repo.refs.current())
        legacy = shown[0]
        content, provenance = dive(
            repo,
            str(legacy["dive_address"]),
            "legacy.py",
        )
        assert content == b"old but large\n" * 10
        assert "salvaged legacy.py" in provenance


class TestTheTour:
    def test_the_tour_reads_largest_first(self):
        repo = build()
        page = tour(repo, repo.refs.current())
        assert page.startswith(
            "2 exhibit(s), largest first:"
        )
        lines = page.splitlines()
        assert lines[1].startswith("  legacy.py:")
        assert "stood at 140 byte(s)" in lines[1]
        assert "salvage dives at" in lines[1]
        assert (
            "the visit that ends in a working "
            "recovery"
        ) in page

    def test_the_empty_museum_is_the_good_news(self):
        repo = Repo.init()
        repo.commit({"app.py": b"core\n"}, "alive")
        assert tour(repo, repo.refs.current()) == (
            "nothing retired yet; everything still "
            "working for a living"
        )
