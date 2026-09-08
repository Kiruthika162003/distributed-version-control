from __future__ import annotations

from keel.hotspots import census, report
from keel.repo import Repo


def storied() -> Repo:
    repo = Repo.init()
    big = b"x" * 300
    repo.commit(
        {
            "churner.py": b"v0" + big,
            "stable.py": b"s" * 250,
            "small.py": b"tiny",
        },
        "base",
    )
    for number in range(1, 4):
        repo.commit(
            {
                "churner.py": f"v{number}".encode() + big,
                "stable.py": b"s" * 250,
                "small.py": b"tiny",
            },
            f"churn {number}",
        )
    return repo


class TestTheCensus:
    def test_both_axes_multiply_into_the_score(self):
        repo = storied()
        spots, _ = census(repo, repo.refs.current())
        top = spots[0]
        assert top.path == "churner.py"
        assert top.touches == 4
        assert top.score() == 4 * top.size

    def test_prescriptions_split_by_axis(self):
        repo = storied()
        spots, _ = census(repo, repo.refs.current())
        by_path = {spot.path: spot for spot in spots}
        assert by_path["churner.py"].prescription() == (
            "both and a meeting"
        )
        assert by_path["stable.py"].prescription() == (
            "splitting someday"
        )
        assert by_path["small.py"].prescription() == "watch"

    def test_the_vanished_churner_is_a_footnote(self):
        repo = storied()
        repo.commit(
            {"stable.py": b"s" * 250, "small.py": b"tiny"},
            "delete the churner",
        )
        _, ghosts = census(repo, repo.refs.current())
        assert len(ghosts) == 1
        assert "wearing a new path" in ghosts[0]


class TestTheReport:
    def test_the_report_prints_both_factors(self):
        repo = storied()
        page = report(repo, repo.refs.current())
        assert page.startswith("hotspots, both axes printed:")
        assert "4 touch(es) x" in page
        assert "both and a meeting" in page

    def test_no_history_no_hotspots(self):
        repo = Repo.init()
        repo.commit({"a.py": b"x"}, "only")
        repo.commit({"b.py": b"x"}, "drop a add b")
        page = report(repo, repo.refs.current())
        assert "hotspots" in page
