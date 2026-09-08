from __future__ import annotations

from keel.cli import main
from keel.voyages import names, page, roster


class TestTheRegistry:
    def test_every_example_is_enumerated(self):
        found = names()
        assert "firstvoyage" in found
        assert "harborday" in found
        assert "archivistday" in found
        assert len(found) >= 11

    def test_every_voyage_carries_its_instruction(self):
        for name, _headline, has_run in roster():
            assert has_run, name

    def test_the_page_boasts_correctly(self):
        text = page()
        assert text.startswith(
            f"{len(names())} voyage(s) on the registry:"
        )
        assert (
            "every voyage carries its run instruction"
        ) in text
        assert "nothing to forget updating" in text


class TestTheLobby:
    def test_the_demo_roster_is_computed(self, capsys):
        assert main(["demo", "ghost"]) == 2
        out = capsys.readouterr().out
        assert "harborday" in out
        assert "policyday" in out

    def test_the_voyages_verb_opens_the_registry(
        self, capsys
    ):
        assert main(["voyages"]) == 0
        out = capsys.readouterr().out
        assert "voyage(s) on the registry:" in out
        assert "messyday:" in out
