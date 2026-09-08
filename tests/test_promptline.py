from __future__ import annotations

from keel.freeze import FreezeBoard
from keel.promptline import line
from keel.repo import Repo
from keel.upstreams import Tracking

BASE = {"app.py": b"core\n"}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    return repo


class TestTheQuietDay:
    def test_just_the_branch_name(self):
        repo = build()
        assert line(repo) == "feature"

    def test_clean_and_current_show_nothing_extra(self):
        repo = build()
        tracking = Tracking(repo=repo)
        tracking.follow("feature", "main")
        rendered = line(
            repo,
            working=dict(BASE),
            tracking=tracking,
            board=FreezeBoard(),
        )
        assert rendered == "feature"


class TestTheLoudDay:
    def test_worst_news_stacks_into_one_line(self):
        repo = build()
        repo.commit(
            dict(BASE, **{"app.py": b"core\nf\n"}),
            "feature work",
        )
        tracking = Tracking(repo=repo)
        tracking.follow("feature", "main")
        board = FreezeBoard()
        board.freeze(
            "feature", "release cut", "priya"
        )
        working = dict(BASE)
        working["app.py"] = b"core\nf\nwip\n"
        working["notes.md"] = b"n\n"
        rendered = line(
            repo,
            working=working,
            tracking=tracking,
            board=board,
        )
        assert rendered == (
            "feature [ahead of main by 1] *2 FROZEN"
        )

    def test_the_detached_head_is_spelled_out(self):
        repo = build()
        tip = repo.refs.current()
        repo.refs.detach(tip)
        rendered = line(repo)
        assert rendered.startswith(
            f"DETACHED at {tip[:8]}"
        )
        assert "void" in rendered
