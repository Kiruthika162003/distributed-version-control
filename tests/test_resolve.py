from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo
from keel.resolve import ResolutionSession

BASE = {
    "app.py": b"shared\ncore",
    "config.ini": b"debug=false",
}


def conflicted_session() -> tuple[Repo, ResolutionSession]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    left = repo.commit(
        dict(BASE, **{"app.py": b"LEFT\ncore"}), "left"
    ).address
    repo.refs.checkout("feature")
    right = repo.commit(
        dict(BASE, **{"app.py": b"RIGHT\ncore"}), "right"
    ).address
    repo.refs.checkout("main")
    outcome = merge_commits(repo, left, right)
    session = ResolutionSession(
        outcome=outcome,
        left_files=repo.files_at(left),
        right_files=repo.files_at(right),
    )
    return repo, session


class TestSettling:
    def test_taking_a_side_settles_and_journals(self):
        _, session = conflicted_session()
        assert session.open_paths() == ["app.py"]
        session.take_theirs("app.py")
        assert session.open_paths() == []
        assert "app.py: took theirs" in session.story()

    def test_the_unconflicted_path_is_not_theater(self):
        _, session = conflicted_session()
        with pytest.raises(Missing) as caught:
            session.take_ours("config.ini")
        assert "would be theater" in str(caught.value)

    def test_hand_merges_are_screened_for_markers(self):
        _, session = conflicted_session()
        with pytest.raises(Invalid) as caught:
            session.settle_by_hand(
                "app.py", b"<<<<<<< ours\nLEFT\ncore"
            )
        assert "far from their cause" in str(caught.value)
        session.settle_by_hand("app.py", b"BOTH\ncore")
        assert session.open_paths() == []


class TestConcluding:
    def test_the_unchecked_box_blocks_conclusion(self):
        _, session = conflicted_session()
        with pytest.raises(Conflict) as caught:
            session.conclude()
        assert "whatever it feels like" in str(caught.value)

    def test_the_settled_merge_commits_cleanly(self):
        repo, session = conflicted_session()
        session.settle_by_hand("app.py", b"BOTH\ncore")
        session.conclude()
        merged = commit_merge(
            repo, session.outcome, "merge with hand fix"
        )
        assert repo.files_at(merged.address)["app.py"] == (
            b"BOTH\ncore"
        )

    def test_a_deletion_settlement_removes_the_path(self):
        _repo, session = conflicted_session()
        session.settle_deletion("app.py")
        files = session.conclude()
        assert "app.py" not in files
