from __future__ import annotations

from keel.cli import main
from keel.organs import page, roster


class TestTheRoster:
    def test_known_organs_carry_their_own_headlines(
        self,
    ):
        table = dict(roster())
        assert table["repo"].startswith(
            "The repository:"
        )
        assert table["rerere"].startswith("Rerere:")
        assert "diff3" in table

    def test_every_organ_is_documented(self):
        for name, headline in roster():
            assert not headline.startswith(
                "UNDOCUMENTED"
            ), name

    def test_the_lobby_does_not_list_itself(self):
        names = [name for name, _headline in roster()]
        assert "cli" not in names
        assert "organs" not in names
        assert "witnesses" not in names


class TestThePage:
    def test_the_headline_counts_and_closes(self):
        text = page()
        first = text.splitlines()[0]
        count = int(first.split(" ")[0])
        assert count >= 60
        assert first.endswith("0 undocumented:")
        assert (
            "there is no list to forget updating"
        ) in text

    def test_the_cli_opens_the_directory(self, capsys):
        assert main(["organs"]) == 0
        out = capsys.readouterr().out
        assert "organ(s), 0 undocumented:" in out
        assert "rebaseplan:" in out
