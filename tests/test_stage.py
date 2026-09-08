from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.stage import Stage

HEAD_FILES = {"app.py": b"v1", "docs.md": b"start"}


def staged_repo() -> Stage:
    repo = Repo.init()
    repo.commit(dict(HEAD_FILES), "base")
    return Stage(repo=repo)


class TestComposition:
    def test_the_commit_says_one_thing_the_directory_three(self):
        stage = staged_repo()
        stage.add("app.py", b"v2")
        working = {
            "app.py": b"v2",
            "docs.md": b"start\nmess",
            "scratch.txt": b"notes",
        }
        report = stage.status(working)
        assert report["staged"] == ["app.py (modified)"]
        assert report["unstaged"] == ["docs.md"]
        assert report["untracked"] == ["scratch.txt"]
        commit = stage.commit("only the app change")
        files = stage.repo.files_at(commit.address)
        assert files["app.py"] == b"v2"
        assert files["docs.md"] == b"start"

    def test_the_three_questions_never_blur(self):
        stage = staged_repo()
        stage.add("new.txt", b"fresh")
        working = {"new.txt": b"fresh but edited"}
        report = stage.status(working)
        assert report["staged"] == ["new.txt (added)"]
        assert report["unstaged"] == ["new.txt"]
        assert report["untracked"] == []


class TestDeletions:
    def test_deletions_are_said_never_inferred(self):
        stage = staged_repo()
        verdict = stage.stage_deletion("docs.md")
        assert "never inferred from absence" in verdict
        assert stage.status({})["staged"] == [
            "docs.md (deleted)"
        ]
        commit = stage.commit("drop docs")
        assert "docs.md" not in stage.repo.files_at(
            commit.address
        )

    def test_deleting_the_nonexistent_is_refused(self):
        with pytest.raises(Missing):
            staged_repo().stage_deletion("ghost.py")


class TestUnstaging:
    def test_unstage_leaves_the_working_copy_alone(self):
        stage = staged_repo()
        stage.add("app.py", b"v2")
        verdict = stage.unstage("app.py")
        assert "the working copy is untouched" in verdict
        assert stage.status({})["staged"] == []

    def test_unstaging_the_unstaged_is_refused(self):
        with pytest.raises(Missing):
            staged_repo().unstage("app.py")

    def test_an_empty_stage_has_no_draft(self):
        with pytest.raises(Invalid) as caught:
            staged_repo().commit("nothing")
        assert "no draft to turn into a commit" in str(
            caught.value
        )
