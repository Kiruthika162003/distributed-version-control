from __future__ import annotations

from keel.repo import Repo
from keel.vocabulary import census, report


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    text = b""
    subjects = [
        "fix: the crash on empty input",
        "fix: the slow path in search",
        "add the export command",
        "fix: minor cleanup in the parser",
        (
            "add a very long subject that keeps going "
            "well past any sensible budget line"
        ),
    ]
    for subject in subjects:
        text += b"x\n"
        repo.commit({"app.py": text}, subject)
    return repo, repo.refs.current()


class TestTheCensus:
    def test_leading_verbs_are_ranked(self):
        repo, tip = build()
        counted = census(repo, tip)
        assert counted["subjects"] == 5
        assert counted["verbs"][0] == ("fix", 3)
        assert counted["verbs"][1] == ("add", 2)

    def test_hedges_and_overruns_are_counted(self):
        repo, tip = build()
        counted = census(repo, tip)
        assert counted["hedged"] == 1
        assert counted["over_budget"] == 1


class TestTheMirror:
    def test_the_fingerprint_reads_in_three_numbers(
        self,
    ):
        repo, tip = build()
        page = report(repo, tip)
        assert page.startswith(
            "the voice of 5 subject(s):"
        )
        assert "opens with 'fix' 3 time(s) (60%)" in (
            page
        )
        assert "1 over the budget of 50" in page
        assert (
            "hedges in 1 subject(s) (20%)"
        ) in page

    def test_the_fix_dominated_voice_is_named(self):
        repo, tip = build()
        page = report(repo, tip)
        assert (
            "describing the planning, not the prose"
        ) in page

    def test_the_census_never_prescribes(self):
        repo, tip = build()
        page = report(repo, tip)
        assert "counted, not judged" in page
        assert (
            "the voice belongs to the people who "
            "write in it"
        ) in page
