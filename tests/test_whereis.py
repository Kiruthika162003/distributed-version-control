# The credential-shaped strings in this file are synthetic fixtures. They exist
# to give the scanner something to match and they authenticate against nothing.
# No real password, key, token, or personal data appears anywhere in this file.
from __future__ import annotations

from keel.repo import Repo
from keel.whereis import report, residencies

SECRET = b"API_KEY=hunter2\n"


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"conf.env": SECRET, "app.py": b"core\n"},
        "the leak arrives",
    )
    repo.commit(
        {
            "conf.env": SECRET,
            "backup.env": SECRET,
            "app.py": b"core\n",
        },
        "the leak spreads",
    )
    repo.commit(
        {
            "backup.env": SECRET,
            "app.py": b"core\n",
        },
        "half a cleanup",
    )
    return repo


class TestTheHunt:
    def test_residencies_group_by_path_and_range(self):
        repo = build()
        found = residencies(repo, SECRET)
        assert found == [
            ("backup.env", 1, 2, True),
            ("conf.env", 0, 1, False),
        ]

    def test_the_live_residency_is_marked_leaking(self):
        repo = build()
        page = report(repo, SECRET)
        assert page.startswith(
            "2 residenc(ies) for these 16 byte(s):"
        )
        assert (
            "backup.env: seq 1 to 2; LIVE at a "
            "branch tip"
        ) in page
        assert (
            "conf.env: seq 0 to 1; historical only"
        ) in page

    def test_the_definitive_miss_is_said_flatly(self):
        repo = build()
        page = report(repo, b"never committed\n")
        assert page.startswith(
            "these bytes have never been committed "
            "here"
        )
        assert "unpushed corners" in page
