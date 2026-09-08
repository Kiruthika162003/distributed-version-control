from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.followpath import follow
from keel.repo import Repo
from keel.restructure import (
    narrate_plan,
    plan_moves,
    restructure,
)

FILES = {
    "lib/parse.py": b"parse\n",
    "lib/emit.py": b"emit\n",
    "scripts/run.sh": b"run\n",
    "README.md": b"hello\n",
}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(FILES), "base")
    return repo


class TestThePlan:
    def test_prefix_moves_map_every_file_once(self):
        moves = plan_moves(
            dict(FILES), {"lib/": "src/core/"}
        )
        assert moves == {
            "lib/parse.py": "src/core/parse.py",
            "lib/emit.py": "src/core/emit.py",
        }

    def test_a_typo_wearing_confidence_is_refused(self):
        with pytest.raises(Invalid) as caught:
            plan_moves(dict(FILES), {"libs/": "src/"})
        assert "typo wearing confidence" in str(
            caught.value
        )

    def test_an_inhabited_destination_is_refused(self):
        files = dict(
            FILES, **{"src/core/parse.py": b"squat\n"}
        )
        with pytest.raises(Invalid) as caught:
            plan_moves(files, {"lib/": "src/core/"})
        assert "buries a resident" in str(caught.value)

    def test_two_rules_on_one_file_are_refused(self):
        with pytest.raises(Invalid) as caught:
            plan_moves(
                dict(FILES),
                {"lib/": "src/", "lib/parse": "old/"},
            )
        assert "slash" in str(caught.value)

    def test_overlapping_prefixes_claim_once_only(self):
        files = {
            "lib/deep/a.py": b"a\n",
            "lib/b.py": b"b\n",
        }
        with pytest.raises(Invalid) as caught:
            plan_moves(
                files,
                {"lib/": "src/", "lib/deep/": "deep/"},
            )
        assert "move it nowhere twice" in str(
            caught.value
        )


class TestTheLanding:
    def test_one_commit_carries_the_map(self):
        repo = build()
        commit = restructure(
            repo, {"lib/": "src/core/"}
        )
        assert commit.message.startswith(
            "restructure: 2 file(s) moved"
        )
        assert "lib/ -> src/core/" in commit.message
        files = repo.head_files()
        assert files["src/core/parse.py"] == b"parse\n"
        assert "lib/parse.py" not in files
        assert files["README.md"] == b"hello\n"

    def test_the_moves_stay_walkable_by_follow(self):
        repo = build()
        restructure(repo, {"lib/": "src/core/"})
        trail = follow(
            repo,
            repo.refs.current(),
            "src/core/parse.py",
        )
        assert trail[0].note == (
            "renamed from lib/parse.py (exact content)"
        )

    def test_the_narration_promises_similarity_one(self):
        repo = build()
        page = narrate_plan(repo, {"lib/": "src/core/"})
        assert page.startswith("2 move(s) planned")
        assert "similarity one" in page
        assert "event horizon" in page
