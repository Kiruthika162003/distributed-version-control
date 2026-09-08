from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.upstreams import Tracking

BASE = {"app.py": b"core\n"}


def build() -> tuple[Repo, Tracking]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    repo.branch_from_head("experiment")
    return repo, Tracking(repo=repo)


class TestTheTable:
    def test_following_is_recorded_and_undone(self):
        _repo, tracking = build()
        assert tracking.follow("feature", "main") == (
            "feature now follows main"
        )
        assert tracking.unfollow("feature") == (
            "feature no longer follows main"
        )
        with pytest.raises(Missing):
            tracking.unfollow("feature")

    def test_the_mirror_is_refused(self):
        _repo, tracking = build()
        with pytest.raises(Invalid) as caught:
            tracking.follow("main", "main")
        assert "mirror admiring itself" in str(
            caught.value
        )

    def test_the_circle_is_refused_with_its_walk(self):
        _repo, tracking = build()
        tracking.follow("feature", "main")
        tracking.follow("experiment", "feature")
        with pytest.raises(Invalid) as caught:
            tracking.follow("main", "experiment")
        message = str(caught.value)
        assert "circle refused" in message
        assert "never comes home" in message

    def test_strangers_cannot_join_the_table(self):
        _repo, tracking = build()
        with pytest.raises(Missing):
            tracking.follow("ghost", "main")


class TestStatus:
    def test_the_four_verbs(self):
        repo, tracking = build()
        tracking.follow("feature", "main")
        assert tracking.status("feature") == (
            "feature: current with main"
        )
        repo.refs.checkout("feature")
        repo.commit(
            dict(BASE, **{"app.py": b"core\nf\n"}),
            "feature work",
        )
        assert tracking.status("feature") == (
            "feature: ahead of main by 1"
        )
        repo.refs.checkout("main")
        repo.commit(
            dict(BASE, **{"app.py": b"core\nm\n"}),
            "main work",
        )
        assert tracking.status("feature") == (
            "feature: diverged from main, ahead 1 "
            "behind 1"
        )
        tracking.follow("experiment", "main")
        assert tracking.status("experiment") == (
            "experiment: behind main by 1"
        )

    def test_following_nobody_is_said_plainly(self):
        _repo, tracking = build()
        assert tracking.status("main") == (
            "main follows nobody; ahead and behind "
            "need a named other"
        )

    def test_the_report_covers_every_branch(self):
        _repo, tracking = build()
        tracking.follow("feature", "main")
        page = tracking.report()
        assert page.startswith("3 branch(es):")
        assert "feature: current with main" in page
        assert "main follows nobody" in page
