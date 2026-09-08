from __future__ import annotations

from examples import featureweek, firstvoyage


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
