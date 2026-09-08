from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.history import (
    first_parent_line,
    only_on,
    review_summary,
    touching_path,
)
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo

BASE = {"app.py": b"v1", "docs.md": b"start"}


def busy_repo() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.commit(dict(BASE, **{"app.py": b"v2"}), "app v2")
    repo.commit(
        dict(BASE, **{"app.py": b"v2", "docs.md": b"grown"}),
        "docs only",
    )
    repo.commit(dict(BASE, **{"app.py": b"v3", "docs.md": b"grown"}), "app v3")
    return repo


class TestPathHistory:
    def test_only_the_touching_commits_answer(self):
        repo = busy_repo()
        rows = touching_path(
            repo, repo.refs.current(), "app.py"
        )
        assert [commit.message for commit, _ in rows] == [
            "app v3", "app v2", "base",
        ]

    def test_the_trail_follows_a_rename(self):
        repo = Repo.init()
        repo.commit({"old.py": b"a\nb\nc\nd"}, "born")
        repo.commit({"new.py": b"a\nb\nc\nd"}, "moved")
        repo.commit({"new.py": b"a\nb\nc\nEDIT"}, "edited")
        rows = touching_path(
            repo, repo.refs.current(), "new.py"
        )
        messages = [commit.message for commit, _ in rows]
        assert messages == ["edited", "moved", "born"]
        assert rows[-1][1] == "old.py"

    def test_a_pathless_history_is_missing(self):
        repo = busy_repo()
        with pytest.raises(Missing):
            touching_path(repo, repo.refs.current(), "ghost")


class TestFirstParent:
    def test_the_line_reads_as_the_owner_experienced_it(self):
        repo = busy_repo()
        repo.branch_from_head("feature")
        repo.refs.checkout("feature")
        repo.commit(
            dict(
                BASE,
                **{
                    "app.py": b"v3",
                    "docs.md": b"grown",
                    "feat.txt": b"x",
                },
            ),
            "feature work",
        )
        repo.refs.checkout("main")
        outcome = merge_commits(
            repo,
            repo.refs.branches["main"],
            repo.refs.branches["feature"],
        )
        commit_merge(repo, outcome, "merge feature")
        line = first_parent_line(repo, repo.refs.current())
        messages = [commit.message for commit in line]
        assert messages[0] == "merge feature"
        assert "feature work" not in messages


class TestRanges:
    def test_only_on_subtracts_ancestor_sets(self):
        repo = busy_repo()
        repo.branch_from_head("feature")
        repo.refs.checkout("feature")
        repo.commit(
            dict(BASE, **{"f.txt": b"1", "app.py": b"v3", "docs.md": b"grown"}),
            "feature one",
        )
        exclusive = only_on(
            repo,
            repo.refs.branches["feature"],
            repo.refs.branches["main"],
        )
        assert [c.message for c in exclusive] == ["feature one"]

    def test_the_review_opens_with_this_question(self):
        repo = busy_repo()
        repo.branch_from_head("feature")
        summary = review_summary(
            repo,
            repo.refs.branches["feature"],
            repo.refs.branches["main"],
        )
        assert "the review is a handshake" in summary
