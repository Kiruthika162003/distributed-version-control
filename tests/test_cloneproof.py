from __future__ import annotations

from keel.witnesses.cloneproof import run


class TestCloneproof:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_every_address_survives_the_text(self):
        testimony = run()
        assert testimony.numbers["commits_on_the_line"] == 5
        assert testimony.numbers["addresses_survived"] == 5
        assert testimony.numbers["trees_survived"] == 5

    def test_the_tip_seals_the_whole_line(self):
        testimony = run()
        assert testimony.numbers["tip_identical"]

    def test_the_stream_is_finite_and_measured(self):
        testimony = run()
        assert testimony.numbers["stream_lines"] == 31
