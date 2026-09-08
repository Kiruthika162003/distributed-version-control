from __future__ import annotations

import pytest

from keel.errors import Missing
from keel.remoteprune import audit, prune, report
from keel.remotes import RemoteSet
from keel.repo import Repo


def build() -> tuple[Repo, RemoteSet]:
    upstream = Repo.init()
    upstream.commit({"app.py": b"core\n"}, "base")
    upstream.branch_from_head("doomed")
    upstream.branch_from_head("kept")
    local = Repo.init()
    remotes = RemoteSet(local=local)
    remotes.add("origin", upstream)
    remotes.fetch("origin")
    upstream.refs.checkout("main")
    upstream.refs.delete("doomed")
    upstream.branch_from_head("newborn")
    return upstream, remotes


class TestTheAudit:
    def test_ghosts_and_strangers_are_sorted(self):
        _upstream, remotes = build()
        sorted_out = audit(remotes, "origin")
        assert sorted_out["ghosts"] == ["doomed"]
        assert sorted_out["strangers"] == ["newborn"]
        assert "kept" in sorted_out["standing"]

    def test_the_report_reads_both_columns(self):
        _upstream, remotes = build()
        page = report(remotes, "origin")
        assert (
            "2 standing, 1 ghost(s), 1 stranger(s)"
        ) in page
        assert (
            "ghost: doomed; gone upstream, still "
            "quoted here with good posture"
        ) in page
        assert (
            "stranger: newborn; the next fetch will "
            "make the introduction"
        ) in page

    def test_agreement_leans_on_the_broom(self):
        _upstream, remotes = build()
        prune(remotes, "origin")
        remotes.fetch("origin")
        page = report(remotes, "origin")
        assert "leans on the broom" in page

    def test_a_stranger_remote_is_refused(self):
        _upstream, remotes = build()
        with pytest.raises(Missing):
            audit(remotes, "upstream")


class TestPruning:
    def test_each_retirement_gets_its_note(self):
        _upstream, remotes = build()
        page = prune(remotes, "origin")
        assert page.startswith(
            "pruned 1 ghost(s) from origin:"
        )
        assert (
            "retired the observation of doomed"
        ) in page
        assert "the note saying why" in page
        assert (
            "doomed"
            not in remotes.remotes["origin"].observed
        )

    def test_pruning_without_ghosts_says_so(self):
        _upstream, remotes = build()
        prune(remotes, "origin")
        assert prune(remotes, "origin") == (
            "nothing to prune on origin; no ghosts "
            "among the observations"
        )
