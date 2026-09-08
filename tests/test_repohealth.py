from __future__ import annotations

from keel.repo import Repo
from keel.repohealth import health_report

BASE = {"app.py": b"core\n"}


def tidy_repo() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "begin the core")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nserve\n"}),
        "wire the server",
    )
    return repo


def sickly_repo() -> Repo:
    repo = tidy_repo()
    repo.commit(
        dict(BASE, **{"app.py": b"core\nserve\nx\n"}),
        "wip",
    )
    repo.branch_from_head("merged-work")
    for step in range(6):
        repo.commit(
            dict(
                BASE,
                **{
                    "app.py": (
                        f"core\nserve\nx\n{step}\n"
                    ).encode()
                },
            ),
            f"trunk step {step}",
        )
    return repo


class TestCleanBills:
    def test_a_tidy_repo_reads_clean_without_fanfare(
        self,
    ):
        page = health_report(tidy_repo())
        assert page.startswith("health report for main")
        assert "physical clean" in page
        assert (
            "nothing the doctor would say out loud"
        ) in page
        assert "only the trunk; nothing to judge" in page
        assert (
            "no findings; a clean report, said without "
            "fanfare"
        ) in page


class TestLoudReports:
    def test_every_examiner_speaks_in_its_own_words(
        self,
    ):
        page = health_report(sickly_repo())
        assert "physical clean" in page
        assert "[squatter]" in page
        assert "merged-work: merged" in page
        assert "the attic:" in page
        assert "the shape:" in page
        assert "a railway" in page

    def test_the_finding_count_scales_honestly(self):
        page = health_report(sickly_repo())
        assert "finding(s) across the examiners" in page
        assert (
            "drawing them is the point of one page"
        ) in page

    def test_no_grade_is_ever_assigned(self):
        for repo in (tidy_repo(), sickly_repo()):
            page = health_report(repo)
            assert "grade" not in page.lower()
            assert "score" not in page.lower()
