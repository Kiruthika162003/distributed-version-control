from __future__ import annotations

from keel.cli import main
from keel.witnesses import registry
from keel.witnesses.wirebill import run as wirebill_run


class TestWitnesses:
    def test_the_wirebill_holds_on_measurement(self):
        testimony = wirebill_run()
        assert testimony.holds
        assert testimony.numbers["saved"] == 16

    def test_the_registry_reports_zero_broken(self):
        assert registry.broken() == []
        assert "witnesses, 0 broken" in registry.report()


class TestTheCli:
    def test_summary_prints_the_one_line(self, capsys):
        assert main(["summary"]) == 0
        out = capsys.readouterr().out
        assert out.strip().endswith("witnesses (0 broken)")

    def test_check_is_quietly_green(self, capsys):
        assert main(["check"]) == 0
        assert "all witnesses hold" in capsys.readouterr().out

    def test_witnesses_prints_every_line(self, capsys):
        assert main(["witnesses"]) == 0
        out = capsys.readouterr().out
        assert "wirebill: holds" in out

    def test_no_command_prints_help(self, capsys):
        assert main([]) == 2
        assert "usage" in capsys.readouterr().out


class TestSingleWitness:
    def test_one_testimony_with_its_numbers(self, capsys):
        assert main(["witness", "gcpin"]) == 0
        out = capsys.readouterr().out
        assert out.startswith("gcpin: holds")
        assert "claim:" in out
        assert "freed_while_pinned = 0" in out

    def test_a_stranger_gets_the_roster(self, capsys):
        assert main(["witness", "ghost"]) == 2
        out = capsys.readouterr().out
        assert "ghost is not a witness" in out
        assert "wirebill" in out
        assert "diff3matrix" in out


class TestDemos:
    def test_a_demo_runs_end_to_end(self, capsys):
        assert main(["demo", "firstvoyage"]) == 0
        out = capsys.readouterr().out
        assert "log:     2 commit(s) on main" in out

    def test_a_stranger_demo_gets_the_roster(self, capsys):
        assert main(["demo", "ghost"]) == 2
        out = capsys.readouterr().out
        assert "ghost is not a demo" in out
        assert "releaseday" in out


class TestTheTrialVerb:
    def test_the_trial_runs_from_the_lobby(
        self, capsys
    ):
        assert main(["trial"]) == 0
        out = capsys.readouterr().out
        assert out.startswith("sea trial:")
        assert (
            "7 system(s) exercised, all answered"
        ) in out


class TestNumbers:
    def test_every_measurement_is_printed(self, capsys):
        assert main(["numbers"]) == 0
        out = capsys.readouterr().out
        assert "wirebill:" in out
        assert "shallowbill:" in out
        assert "full_cost = 30" in out
