from __future__ import annotations

import pytest

from keel.aliases import AliasTable
from keel.errors import Invalid, Missing


class TestDefinitions:
    def test_shorthand_expands_with_its_trail(self):
        table = AliasTable()
        table.define("co", "checkout")
        assert table.expand("co feature") == (
            "checkout feature  [co -> checkout]"
        )

    def test_chains_name_every_hop(self):
        table = AliasTable()
        table.define("st", "status --short")
        table.define("s", "st")
        assert table.expand("s") == (
            "status --short  [s -> st -> status]"
        )

    def test_real_verbs_cannot_be_shadowed(self):
        table = AliasTable()
        with pytest.raises(Invalid) as caught:
            table.define("push", "pull")
        assert "muscle memory becomes an incident" in str(
            caught.value
        )

    def test_expanding_to_silence_is_refused(self):
        table = AliasTable()
        with pytest.raises(Invalid):
            table.define("quiet", "   ")


class TestCycles:
    def test_a_two_step_cycle_dies_at_definition(self):
        table = AliasTable()
        table.define("a", "b")
        with pytest.raises(Invalid) as caught:
            table.define("b", "a")
        assert "somebody's joke" in str(caught.value)
        assert "b" not in table.entries

    def test_a_self_cycle_dies_at_definition(self):
        table = AliasTable()
        with pytest.raises(Invalid):
            table.define("loop", "loop --forever")


class TestExpansion:
    def test_plain_commands_pass_untouched(self):
        table = AliasTable()
        table.define("co", "checkout")
        assert table.expand("commit -m done") == (
            "commit -m done"
        )

    def test_arguments_ride_behind_the_expansion(self):
        table = AliasTable()
        table.define("lg", "log --graph --all")
        assert table.expand("lg --limit 5").startswith(
            "log --graph --all --limit 5"
        )


class TestHousekeeping:
    def test_removal_and_its_refusal(self):
        table = AliasTable()
        table.define("co", "checkout")
        assert table.remove("co") == "co forgotten"
        with pytest.raises(Missing):
            table.remove("co")

    def test_the_listing_speaks_standard_when_empty(self):
        table = AliasTable()
        assert table.listing() == (
            "no aliases; everyone speaks standard"
        )
        table.define("co", "checkout")
        assert "co -> checkout" in table.listing()
