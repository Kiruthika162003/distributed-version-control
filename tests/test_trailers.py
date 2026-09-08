from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.trailers import (
    add_trailer,
    parse_trailers,
    query,
    signoff_chain,
)

SIGNED = (
    "Fix the frame counter\n"
    "\n"
    "The counter skipped on wrap.\n"
    "\n"
    "Signed-off-by: Asha\n"
    "Reviewed-by: Ben\n"
    "Fixes: TICKET-441"
)


class TestParsing:
    def test_the_end_block_parses_as_data(self):
        found = parse_trailers(SIGNED)
        assert found["Signed-Off-By"] == ["Asha"]
        assert found["Fixes"] == ["TICKET-441"]

    def test_prose_mentioning_fixes_is_not_harvested(self):
        message = (
            "Subject line\n\n"
            "This discusses Fixes: TICKET-9 in passing.\n\n"
            "And ends with plain prose."
        )
        assert parse_trailers(message) == {}

    def test_a_message_that_is_all_trailers_is_a_body(self):
        assert parse_trailers("Fixes: TICKET-1") == {}

    def test_keys_normalize_for_querying(self):
        assert query(SIGNED, "signed-off-by") == ["Asha"]
        assert query(SIGNED, "SIGNED-OFF-BY") == ["Asha"]


class TestAdding:
    def test_appending_never_reflows_the_body(self):
        grown = add_trailer(SIGNED, "Acked-by", "Chen")
        assert grown.startswith(SIGNED)
        assert grown.endswith("Acked-By: Chen")

    def test_the_first_trailer_gets_its_blank_line(self):
        message = "Subject\n\nJust a body."
        grown = add_trailer(message, "fixes", "TICKET-2")
        assert grown.endswith("Just a body.\n\nFixes: TICKET-2")
        assert parse_trailers(grown)["Fixes"] == ["TICKET-2"]

    def test_empty_values_assert_nothing(self):
        with pytest.raises(Invalid):
            add_trailer(SIGNED, "Fixes", "  ")

    def test_key_grammar_is_letters_and_hyphens(self):
        with pytest.raises(Invalid):
            add_trailer(SIGNED, "bad key!", "x")


class TestTheChain:
    def test_the_signoff_chain_reads_in_order(self):
        message = add_trailer(
            SIGNED, "Signed-off-by", "Dana"
        )
        assert signoff_chain(message) == (
            "2 signoff(s): Asha -> Dana"
        )

    def test_the_unsigned_message_stands_alone(self):
        assert "stands on its own" in signoff_chain(
            "Subject\n\nBody."
        )
