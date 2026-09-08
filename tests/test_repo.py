from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.repo import Repo

V1 = {"README": b"docs", "src/main.py": b"print(1)"}
V2 = {"README": b"docs", "src/main.py": b"print(2)"}


def seeded() -> Repo:
    repo = Repo.init()
    repo.commit(dict(V1), "first light")
    return repo


class TestCommitting:
    def test_the_first_commit_creates_main(self):
        repo = seeded()
        assert repo.refs.current_branch() == "main"
        assert repo.history()[0].endswith("first light")

    def test_the_branch_follows_each_commit(self):
        repo = seeded()
        second = repo.commit(dict(V2), "tweak main.py")
        assert repo.refs.current() == second.address
        assert [
            line.split(" ", 1)[1] for line in repo.history()
        ] == ["tweak main.py", "first light"]

    def test_the_nothing_changed_commit_is_refused(self):
        repo = seeded()
        with pytest.raises(Invalid) as caught:
            repo.commit(dict(V1), "busywork")
        assert "lies by volume" in str(caught.value)

    def test_snapshots_round_trip_bytes(self):
        repo = seeded()
        repo.commit(dict(V2), "second")
        assert repo.head_files() == V2


class TestBranching:
    def test_a_branch_starts_where_head_stands(self):
        repo = seeded()
        repo.branch_from_head("feature")
        repo.refs.checkout("feature")
        repo.commit(
            dict(V1, **{"extra.txt": b"new"}), "feature work"
        )
        repo.refs.checkout("main")
        assert "extra.txt" not in repo.head_files()

    def test_changes_between_names_the_paths(self):
        repo = seeded()
        first = repo.refs.current()
        second = repo.commit(dict(V2), "tweak").address
        assert repo.changes_between(first, second) == {
            "src/main.py": "modified"
        }


class TestSharing:
    def test_unchanged_files_share_storage_across_commits(self):
        repo = seeded()
        writes_before = repo.store.writes
        repo.commit(dict(V2), "tweak")
        fresh_objects = repo.store.writes - writes_before
        assert fresh_objects <= 4
