from __future__ import annotations

import pytest

from keel.conflictforecast import forecast, render
from keel.errors import Invalid
from keel.repo import Repo

BASE = {"app.py": b"core\n", "docs.md": b"start\n"}


def arena(*claimants: str) -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    for name in claimants:
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        repo.commit(
            dict(
                BASE,
                **{"app.py": f"core\n{name}\n".encode()},
            ),
            f"{name} work",
        )
        repo.refs.checkout("main")
    repo.branch_from_head("docs")
    repo.refs.checkout("docs")
    repo.commit(
        dict(BASE, **{"docs.md": b"start\nmore\n"}),
        "docs work",
    )
    repo.refs.checkout("main")
    return repo


class TestForecasts:
    def test_meetings_sort_into_their_columns(self):
        repo = arena("east", "west")
        meetings = forecast(
            repo, ["east", "west", "docs"]
        )
        by_pair = {
            (left, right): (verdict, detail)
            for left, right, verdict, detail in meetings
        }
        assert by_pair[("east", "west")] == (
            "will fight",
            ("app.py",),
        )
        assert by_pair[("docs", "east")][0] == "clean"
        assert by_pair[("docs", "west")][0] == "clean"

    def test_strangers_cannot_meet_and_say_so(self):
        repo = arena("east")
        stray = repo.graph.create(
            tree=repo.snapshot_tree(
                {"island.txt": b"alone\n"}
            ),
            parents=(),
            message="island root",
        )
        repo.refs.create_branch("island", stray.address)
        meetings = forecast(repo, ["east", "island"])
        assert meetings[0][2] == "cannot meet"
        assert "no ancestor" in meetings[0][3][0]

    def test_one_branch_meets_nobody(self):
        repo = arena("east")
        with pytest.raises(Invalid):
            forecast(repo, ["east"])


class TestAdvice:
    def test_the_town_square_is_named(self):
        repo = arena("east", "west", "north")
        page = render(
            repo, ["east", "west", "north"]
        )
        assert (
            "app.py is the town square, contested in "
            "3 meeting(s)"
        ) in page
        assert "decides by arrival" in page

    def test_a_single_fight_gets_paired_off(self):
        repo = arena("east", "west")
        page = render(repo, ["east", "west", "docs"])
        assert (
            "each fight has exactly two claimants"
        ) in page

    def test_no_weather_is_a_forecast_too(self):
        repo = arena("east")
        page = render(repo, ["east", "docs"])
        assert "no weather in it" in page
