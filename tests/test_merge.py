from __future__ import annotations

import pytest

from keel.errors import Conflict
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo

BASE_FILES = {
    "README": b"docs",
    "app.py": b"one\ntwo\nthree",
    "config.ini": b"debug=false",
}


def forked_repo() -> tuple[Repo, str, str]:
    repo = Repo.init()
    repo.commit(dict(BASE_FILES), "base")
    repo.branch_from_head("feature")
    left = repo.commit(
        dict(BASE_FILES, **{"app.py": b"ONE\ntwo\nthree"}),
        "left edit",
    ).address
    repo.refs.checkout("feature")
    right = repo.commit(
        dict(BASE_FILES, **{"config.ini": b"debug=true"}),
        "right edit",
    ).address
    repo.refs.checkout("main")
    return repo, left, right


class TestFileResolution:
    def test_disjoint_edits_merge_clean(self):
        repo, left, right = forked_repo()
        outcome = merge_commits(repo, left, right)
        assert outcome.is_clean()
        assert outcome.merged_files["app.py"] == (
            b"ONE\ntwo\nthree"
        )
        assert outcome.merged_files["config.ini"] == (
            b"debug=true"
        )

    def test_same_file_different_lines_settles_by_diff3(self):
        repo = Repo.init()
        repo.commit(dict(BASE_FILES), "base")
        repo.branch_from_head("feature")
        left = repo.commit(
            dict(BASE_FILES, **{"app.py": b"ONE\ntwo\nthree"}),
            "left",
        ).address
        repo.refs.checkout("feature")
        right = repo.commit(
            dict(BASE_FILES, **{"app.py": b"one\ntwo\nTHREE"}),
            "right",
        ).address
        outcome = merge_commits(repo, left, right)
        assert outcome.diff3_paths == ["app.py"]
        assert outcome.merged_files["app.py"] == (
            b"ONE\ntwo\nTHREE"
        )

    def test_the_same_line_waits_for_a_person(self):
        repo = Repo.init()
        repo.commit(dict(BASE_FILES), "base")
        repo.branch_from_head("feature")
        left = repo.commit(
            dict(BASE_FILES, **{"app.py": b"LEFT\ntwo\nthree"}),
            "left",
        ).address
        repo.refs.checkout("feature")
        right = repo.commit(
            dict(BASE_FILES, **{"app.py": b"RIGHT\ntwo\nthree"}),
            "right",
        ).address
        outcome = merge_commits(repo, left, right)
        assert "app.py" in outcome.conflicts
        assert "waiting for a person" in outcome.report()

    def test_both_added_differently_has_no_tiebreaker(self):
        repo = Repo.init()
        repo.commit(dict(BASE_FILES), "base")
        repo.branch_from_head("feature")
        left = repo.commit(
            dict(BASE_FILES, **{"new.txt": b"mine"}), "left"
        ).address
        repo.refs.checkout("feature")
        right = repo.commit(
            dict(BASE_FILES, **{"new.txt": b"yours"}), "right"
        ).address
        outcome = merge_commits(repo, left, right)
        assert "no base to break the tie" in outcome.conflicts[
            "new.txt"
        ]


class TestTheMergeCommit:
    def test_the_clean_merge_records_both_parents(self):
        repo, left, right = forked_repo()
        outcome = merge_commits(repo, left, right)
        merged = commit_merge(repo, outcome, "merge feature")
        assert merged.parents == (left, right)
        assert repo.head_files()["config.ini"] == b"debug=true"

    def test_a_merge_over_conflicts_is_a_lie_refused(self):
        repo = Repo.init()
        repo.commit(dict(BASE_FILES), "base")
        repo.branch_from_head("feature")
        left = repo.commit(
            dict(BASE_FILES, **{"app.py": b"L\ntwo\nthree"}),
            "left",
        ).address
        repo.refs.checkout("feature")
        right = repo.commit(
            dict(BASE_FILES, **{"app.py": b"R\ntwo\nthree"}),
            "right",
        ).address
        repo.refs.checkout("main")
        outcome = merge_commits(repo, left, right)
        with pytest.raises(Conflict) as caught:
            commit_merge(repo, outcome, "premature")
        assert "a lie with two parents" in str(caught.value)

    def test_the_report_splits_machine_from_person(self):
        repo, left, right = forked_repo()
        outcome = merge_commits(repo, left, right)
        assert outcome.report().startswith(
            "3 path(s) merged clean, 0 settled by diff3, "
            "0 waiting for a person"
        )
