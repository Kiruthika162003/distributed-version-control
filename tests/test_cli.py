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
