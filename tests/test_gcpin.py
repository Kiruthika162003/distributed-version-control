from __future__ import annotations

from keel.witnesses.gcpin import run


class TestGcpin:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_pin_survives_the_first_collection(self):
        testimony = run()
        assert testimony.numbers["freed_while_pinned"] == 0

    def test_the_reset_entry_pins_what_it_abandoned(self):
        testimony = run()
        assert (
            testimony.numbers["freed_after_bare_trim"] == 0
        )

    def test_movement_plus_trim_frees_the_closure(self):
        testimony = run()
        assert (
            testimony.numbers["freed_after_movement"] == 3
        )
        assert testimony.numbers["survivors"] == 9
