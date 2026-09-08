from __future__ import annotations

from keel.repo import Repo
from keel.twins import near_twins, report, twin_families

LICENSE = b"harbor license v1\nall lines reserved\n"
DRIFTER = (
    b"line 1\nline 2\nline 3\nline 4\nline 5\n"
    b"line 6\nline 7\nline 8\nline 9\nline 10\n"
)
DRIFTED = (
    b"line 1\nline 2\nline 3\nline 4\nline 5\n"
    b"line 6\nline 7\nline 8\nline 9\nline TEN\n"
)


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(
        {
            "LICENSE": LICENSE,
            "vendor/LICENSE": LICENSE,
            "util/helpers.py": DRIFTER,
            "scripts/helpers.py": DRIFTED,
            "app.py": b"unique\n",
        },
        "the town with twins",
    )
    return repo, repo.refs.current()


class TestExactFamilies:
    def test_identical_bytes_group_by_address(self):
        repo, tip = build()
        families = twin_families(repo, tip)
        assert families == [
            ["LICENSE", "vendor/LICENSE"]
        ]

    def test_unique_paths_stay_out_of_families(self):
        repo, tip = build()
        for family in twin_families(repo, tip):
            assert "app.py" not in family


class TestNearTwins:
    def test_a_one_line_drift_is_flagged(self):
        repo, tip = build()
        nears = near_twins(repo, tip)
        assert len(nears) == 1
        left, right, score = nears[0]
        assert left == "scripts/helpers.py"
        assert right == "util/helpers.py"
        assert score == 0.9

    def test_the_report_questions_and_warns(self):
        repo, tip = build()
        page = report(repo, tip)
        assert page.startswith(
            "1 exact famil(ies), 1 near-twin pair(s):"
        )
        assert (
            "identical: LICENSE = vendor/LICENSE"
        ) in page
        assert "comes back with an alibi" in page
        assert (
            "drifting: scripts/helpers.py ~ "
            "util/helpers.py (90%)"
        ) in page
        assert "already picked up speed" in page

    def test_a_town_without_twins_says_so(self):
        repo = Repo.init()
        repo.commit(
            {"a.py": b"a\n", "b.py": b"b\n"}, "plain"
        )
        assert report(repo, repo.refs.current()) == (
            "no twins at the tip; every path speaks "
            "for itself"
        )
