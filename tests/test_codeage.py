from __future__ import annotations

from keel.codeage import age_census, report
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    files = {
        "config.txt": b"k=v\n",
        "api.py": b"a\nb\n",
        "mixed.py": b"one\ntwo\n",
    }
    repo.commit(dict(files), "founding")
    files["scratch.txt"] = b"s\n"
    repo.commit(dict(files), "scratch born")
    files["scratch.txt"] = b"s\nt\n"
    repo.commit(dict(files), "scratch grows")
    files["scratch.txt"] = b"s\nt\nu\n"
    repo.commit(dict(files), "scratch again")
    files["mixed.py"] = b"one\nTWO NEW\n"
    repo.commit(dict(files), "half rewrite")
    files["api.py"] = b"A\nB\n"
    repo.commit(dict(files), "api repainted")
    return repo, repo.refs.current()


class TestTheCensus:
    def test_ages_read_from_blame_in_sequence_units(
        self,
    ):
        repo, tip = build()
        by_path = {
            held.path: held
            for held in age_census(repo, tip)
        }
        assert by_path["config.txt"].average_age == 5.0
        assert by_path["api.py"].average_age == 0.0
        assert by_path["mixed.py"].average_age == 3.0
        assert by_path["mixed.py"].oldest == 5
        assert by_path["mixed.py"].newest == 1

    def test_the_page_sorts_old_growth_first(self):
        repo, tip = build()
        census = age_census(repo, tip)
        assert census[0].path == "config.txt"
        assert census[-1].path == "api.py"


class TestVerdicts:
    def test_the_three_verdicts_split_on_the_span(self):
        repo, tip = build()
        span = 5
        by_path = {
            held.path: held.verdict(span)
            for held in age_census(repo, tip)
        }
        assert by_path["config.txt"].startswith(
            "old growth"
        )
        assert by_path["api.py"] == "fresh paint"
        assert by_path["mixed.py"] == "settled"

    def test_old_growth_keeps_its_caveat(self):
        repo, tip = build()
        page = report(repo, tip)
        assert "finished or feared" in page
        assert (
            "only the next editor can tell"
        ) in page

    def test_the_denominator_is_the_repos_own_life(self):
        repo, tip = build()
        page = report(repo, tip)
        assert page.startswith(
            "line ages against a span of 5:"
        )
        assert (
            "2 of 8 line(s) live in fresh paint"
        ) in page
