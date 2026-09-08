from __future__ import annotations

from keel.freeze import FreezeBoard
from keel.repo import Repo
from keel.turnover import note

BASE = {"app.py": b"core\n"}


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    anchor = repo.commit(dict(BASE), "the anchor")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nnew\n"}),
        "while you were out",
    )
    return repo, anchor.address


class TestTheNote:
    def test_the_sections_arrive_in_watch_order(self):
        repo, anchor = build()
        freezes = FreezeBoard()
        freezes.freeze("main", "cut week", "priya")
        working = dict(repo.head_files())
        working["app.py"] = b"core\nnew\nwip\n"
        page = note(
            repo,
            anchor,
            "priya",
            sentence=(
                "The cache change is half-decided; "
                "read the thread before touching it."
            ),
            working=working,
            freezes=freezes,
        )
        assert page.startswith("turnover from priya:")
        assert "situation: main *1" in page
        assert (
            "main is frozen: cut week (ask priya)"
        ) in page
        assert "while you were out" in page
        assert (
            "in their own words: The cache change is "
            "half-decided"
        ) in page
        assert (
            "only the person leaving knew what was "
            "almost"
        ) in page

    def test_silence_is_recorded_honestly(self):
        repo, anchor = build()
        page = note(repo, anchor, "devi")
        assert (
            "nothing to add, which is sometimes the "
            "honest turnover"
        ) in page

    def test_a_quiet_watch_reads_quiet(self):
        repo, _anchor = build()
        page = note(
            repo, repo.refs.current(), "devi"
        )
        assert "situation: main" in page
        assert "no standing orders" in page
        assert (
            "nothing happened; you were never really "
            "gone"
        ) in page
