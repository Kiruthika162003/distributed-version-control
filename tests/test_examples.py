from __future__ import annotations

from examples import (
    archaeologyday,
    archivistday,
    collaborationday,
    featureweek,
    firstvoyage,
    fleetweek,
    harborday,
    hotfixflow,
    maintenanceday,
    messyday,
    policyday,
    releaseday,
)


class TestFleetWeek:
    def test_the_week_reads_end_to_end(self, capsys):
        assert fleetweek.main() == 0
        out = capsys.readouterr().out
        assert "the last accord:" in out
        assert "caller-two sails farthest" in out
        assert "6 commit(s)" in out
        assert (
            "each one a conversation before any "
            "history moves"
        ) in out
        assert (
            "the convoy lands: 3 branch(es) as one "
            "pointer move"
        ) in out
        assert (
            "applied 3 move(s) as one decision:"
        ) in out
        assert (
            "carried by main, 9 commit(s) below the "
            "tip"
        ) in out


class TestHarborDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert harborday.main() == 0
        out = capsys.readouterr().out
        assert (
            "the harbor holds this landing: 3 of 3 "
            "gauntlet(s) object"
        ) in out
        assert (
            "gates objecting: 5; the secret quoted: "
            "False"
        ) in out
        assert "the sign comes down" in out
        assert "the turn is over" in out
        assert (
            "the harbor clears this landing: three "
            "gauntlets, one visit"
        ) in out
        assert (
            "one desk, three buildings saved"
        ) in out


class TestArchivistDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert archivistday.main() == 0
        out = capsys.readouterr().out
        assert "welcome; main stands at" in out
        assert (
            "toolbox.py has answered to 2 name(s): "
            "toolbox.py <- utils.py"
        ) in out
        assert "renamed from utils.py (exact content)" in out
        assert (
            "config.txt: 1 line(s), average age 3.0 "
            "of 3"
        ) in out
        assert "old growth" in out
        assert (
            "no findings; a clean report, said "
            "without fanfare"
        ) in out


class TestPolicyDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert policyday.main() == 0
        out = capsys.readouterr().out
        assert "push of main by dana: ACCEPTED" in out
        assert (
            "push of main by dana: REFUSED, 2 hard "
            "failure(s)"
        ) in out
        assert "closed for the release cut" in out
        assert "0 review trailer(s) against 2" in out
        assert (
            "OVERRIDE: dana landed on main during "
            "'the release cut', approved by priya, "
            "ticket HOT-99"
        ) in out
        assert (
            "1 branch(es) frozen, 1 landing(s) stopped, "
            "1 override(s)"
        ) in out
        assert "2 landed, 1 bounced" in out
        assert (
            "bounced (conflicts with what landed ahead "
            "on src/app.py)"
        ) in out


class TestReleaseDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert releaseday.main() == 0
        out = capsys.readouterr().out
        assert (
            "8 changelog line(s) drafted for v1.1"
        ) in out
        assert "- rename the entry points" in out
        assert "where:   v1.0+3" in out
        assert "tag:     exactly v1.1" in out
        assert "2 entrie(s) verified against the sealed" in out
        assert (
            "full bundle: 13 object(s), 4 commit(s)"
        ) in out
        assert "same address, no network involved" in out


class TestMessyDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert messyday.main() == 0
        out = capsys.readouterr().out
        assert (
            "shelved 1 file(s) as 'half-done app rewrite' "
            "from feature"
        ) in out
        assert "entry removed" in out
        assert (
            out.count(
                "1 path(s) merged clean, 0 settled by "
                "diff3, 1 waiting for a person"
            )
            == 2
        )
        assert "recorded under" in out
        assert "REPLAYED recording" in out
        assert (
            "1 recording(s), 1 replay(s); every replay is "
            "a hand-resolution not retyped"
        ) in out
        assert (
            "WARNING: shelved on feature, applied on main"
        ) in out
        assert (
            "the shelf never loses anything quietly"
        ) in out


class TestMaintenanceDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert maintenanceday.main() == 0
        out = capsys.readouterr().out
        assert out.count("physical clean") == 2
        assert (
            "the reflog pins what the journal remembers"
        ) in out
        assert (
            "nothing unreachable; the census was the work"
        ) in out
        assert "reflog trimmed by 8 entrie(s)" in out
        assert (
            "freed 3 object(s): 1 blob(s), 1 commit(s), "
            "1 tree(s)"
        ) in out
        assert (
            "maintenance complete, receipts reconciled:"
        ) in out


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
