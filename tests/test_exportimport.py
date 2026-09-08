from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.exportimport import (
    fast_export,
    fast_import,
    round_trip_verdict,
)
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo

BASE = {"a.txt": b"one\ntwo", "sub/b.txt": b"deep"}


def storied() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("side")
    repo.commit(
        dict(BASE, **{"a.txt": b"one\nMAIN"}), "main work"
    )
    repo.refs.checkout("side")
    repo.commit(
        dict(BASE, **{"side.txt": b"branch"}), "side work"
    )
    repo.refs.checkout("main")
    outcome = merge_commits(
        repo,
        repo.refs.branches["main"],
        repo.refs.branches["side"],
    )
    commit_merge(repo, outcome, "merge side")
    return repo


class TestTheStream:
    def test_marks_stand_in_for_addresses(self):
        repo = storied()
        stream = fast_export(repo, repo.refs.current())
        assert "commit mark=1" in stream
        assert "parents 2 3" in stream or (
            "parents 3 2" in stream
        )
        for address in repo.graph.commits:
            assert address not in stream

    def test_newlines_survive_the_escaping(self):
        repo = storied()
        stream = fast_export(repo, repo.refs.current())
        assert "one\\ntwo" in stream


class TestTheRoundTrip:
    def test_the_honesty_test_holds(self):
        repo = storied()
        verdict = round_trip_verdict(
            repo, repo.refs.current()
        )
        assert verdict.startswith("round trip holds")
        assert "4 tree(s) identical" in verdict

    def test_the_rebuilt_repo_reads_the_same_files(self):
        repo = storied()
        rebuilt = fast_import(
            fast_export(repo, repo.refs.current())
        )
        assert rebuilt.head_files()["side.txt"] == b"branch"
        assert rebuilt.head_files()["a.txt"] == b"one\nMAIN"


class TestRefusals:
    def test_marks_used_before_definition_are_orphans(self):
        bad = (
            "commit mark=1\n"
            "parents 9\n"
            "message ghost\n"
            "end"
        )
        with pytest.raises(Invalid) as caught:
            fast_import(bad)
        assert "confident faces" in str(caught.value)

    def test_alien_lines_are_refused(self):
        with pytest.raises(Invalid) as caught:
            fast_import("blob deadbeef")
        assert "this format never emits" in str(caught.value)
