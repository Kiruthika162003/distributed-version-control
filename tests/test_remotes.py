from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.remotes import RemoteSet
from keel.repo import Repo

BASE = {"a.txt": b"shared history"}


def pair() -> tuple[RemoteSet, Repo, Repo]:
    origin = Repo.init()
    origin.commit(dict(BASE), "base")
    local = Repo.init()
    local.commit(dict(BASE), "base")
    remotes = RemoteSet(local=local)
    remotes.add("origin", origin)
    return remotes, local, origin


class TestObservation:
    def test_fetch_caches_an_observation(self):
        remotes, _, origin = pair()
        origin.commit(
            dict(BASE, **{"a.txt": b"v2"}), "their work"
        )
        verdict = remotes.fetch("origin")
        assert "branch(es) observed" in verdict
        assert remotes.remotes["origin"].observed["main"] == (
            origin.refs.branches["main"]
        )

    def test_names_are_one_word_no_slashes(self):
        remotes, _, origin = pair()
        with pytest.raises(Invalid):
            remotes.add("up/stream", origin)

    def test_the_unknown_remote_is_missing(self):
        remotes, _, _ = pair()
        with pytest.raises(Missing):
            remotes.fetch("ghost")


class TestDivergence:
    def test_the_four_shapes_end_in_different_verbs(self):
        remotes, local, origin = pair()
        remotes.fetch("origin")
        assert "current with origin" in remotes.divergence(
            "main", "origin"
        )
        local.commit(dict(BASE, **{"b.txt": b"m"}), "ours")
        assert "the verb is push" in remotes.divergence(
            "main", "origin"
        )
        origin.commit(
            dict(BASE, **{"c.txt": b"t"}), "theirs"
        )
        remotes.fetch("origin")
        verdict = remotes.divergence("main", "origin")
        assert "diverged" in verdict
        assert "a conversation" in verdict

    def test_behind_reads_from_the_cache_not_the_network(self):
        remotes, _local, origin = pair()
        origin.commit(
            dict(BASE, **{"a.txt": b"v2"}), "their move"
        )
        remotes.fetch("origin")
        verdict = remotes.divergence("main", "origin")
        assert "behind 1" in verdict
        assert "merge or rebase" in verdict

    def test_the_honest_tense_is_fetch_counts(self):
        remotes, _, _ = pair()
        remotes.fetch("origin")
        assert "as of fetch #1" in remotes.divergence(
            "main", "origin"
        )

    def test_never_observed_says_fetch_first(self):
        remotes, local, _ = pair()
        local.refs.create_branch(
            "topic", local.refs.current()
        )
        assert "fetch first, then ask again" in (
            remotes.divergence("topic", "origin")
        )
