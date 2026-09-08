from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.gc import Collector
from keel.repo import Repo


def repo_with_abandonment() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit({"a.txt": b"one"}, "keep me")
    abandoned = repo.commit(
        {"a.txt": b"two"}, "reset away"
    ).address
    repo.refs.move(
        "main",
        repo.graph.get(abandoned).parents[0],
        reason="reset --hard",
        force=True,
    )
    return repo, abandoned


class TestTheCensus:
    def test_the_reflog_pins_the_reset_away_commit(self):
        repo, abandoned = repo_with_abandonment()
        collector = Collector(repo=repo)
        assert abandoned in collector.reachable()
        assert "the reflog pins" in collector.census()

    def test_collection_with_the_pin_frees_nothing(self):
        repo, _ = repo_with_abandonment()
        collector = Collector(repo=repo)
        assert collector.collect() == (
            "nothing unreachable; the census was the work"
        )


class TestTheCollection:
    def test_trimming_the_journal_releases_the_pin(self):
        repo, abandoned = repo_with_abandonment()
        repo.refs.checkout("main")
        collector = Collector(repo=repo)
        collector.trim_reflog(keep_last=1)
        verdict = collector.collect()
        assert verdict.startswith("freed ")
        assert "commit(s)" in verdict
        assert "itemized bill" in verdict
        assert abandoned not in repo.store.objects

    def test_the_live_history_survives_collection(self):
        repo, _ = repo_with_abandonment()
        repo.refs.checkout("main")
        collector = Collector(repo=repo)
        collector.trim_reflog(keep_last=1)
        collector.collect()
        assert repo.head_files() == {"a.txt": b"one"}

    def test_the_net_cannot_be_deleted_underfoot(self):
        repo, _ = repo_with_abandonment()
        with pytest.raises(Invalid) as caught:
            Collector(repo=repo).trim_reflog(keep_last=0)
        assert "while standing on it" in str(caught.value)
