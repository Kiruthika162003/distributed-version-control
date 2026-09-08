from __future__ import annotations

from examples import (
    archaeologyday,
    collaborationday,
    featureweek,
    firstvoyage,
    hotfixflow,
)


class TestCollaborationDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert collaborationday.main() == 0
        out = capsys.readouterr().out
        assert "main created on the remote" in out
        assert "main fast-forwarded, 3 object(s)" in out
        assert (
            "a plain push never discards commits someone "
            "may be standing on"
        ) in out
        assert (
            "diverged, ahead 1 behind 1 as of fetch #1; "
            "the verb is a conversation"
        ) in out
        assert "lease broken" in out
        assert (
            "behind 2 as of fetch #2; the verb is merge "
            "or rebase"
        ) in out
        assert (
            'main holds "merge bob\'s coverage" with '
            "2 parents"
        ) in out


class TestArchaeologyDay:
    def test_the_dig_reads_end_to_end(self, capsys):
        assert archaeologyday.main() == 0
        out = capsys.readouterr().out
        assert "blame:   3 line(s):" in out
        assert (
            "pickaxe: 'use_old': 2 count change(s), "
            "0 occurrence(s) today"
        ) in out
        assert "range:   app.py:2-3: 2 event(s)" in out
        assert (
            "bisect:  culprit is 'the migration'"
        ) in out


class TestFeatureWeek:
    def test_the_week_reads_end_to_end(self, capsys):
        assert featureweek.main() == 0
        out = capsys.readouterr().out
        assert "rebase complete: 2 commit(s)" in out
        assert (
            "2 path(s) merged clean, 0 settled by diff3, "
            "1 waiting for a person"
        ) in out
        assert "settle:  app.py: hand-merged" in out
        assert "with 2 parents" in out
        assert "1 commit(s) to review:" in out


class TestHotfixFlow:
    def test_the_flow_reads_end_to_end(self, capsys):
        assert hotfixflow.main() == 0
        out = capsys.readouterr().out
        assert "Revert: enable debug in prod" in out
        assert "cherry-picked from" in out
        assert "tagged:  exactly v1.0.1" in out
        assert (
            "1 landed upstream under other addresses, "
            "2 pending"
        ) in out
        assert "cherry-pick" in out


class TestFirstVoyage:
    def test_the_voyage_reads_end_to_end(self, capsys):
        assert firstvoyage.main() == 0
        out = capsys.readouterr().out
        assert "log:     2 commit(s) on main" in out
        assert (
            "3 path(s) merged clean, 0 settled by diff3, "
            "0 waiting for a person"
        ) in out
        assert "with 2 parents" in out
        assert "readme says 'a small project, documented'" in out
        assert (
            "15 object(s) stored, 7 duplicate write(s) "
            "collapsed"
        ) in out
