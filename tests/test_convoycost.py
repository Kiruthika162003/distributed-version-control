from __future__ import annotations

from keel.witnesses.convoycost import run


class TestConvoycost:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_names_stay_untouched(self):
        testimony = run()
        assert testimony.numbers["scattered"]
        assert testimony.numbers["trunk_untouched"]

    def test_the_flotsam_is_one_commit_not_two(self):
        testimony = run()
        assert testimony.numbers["flotsam_objects"] == 1

    def test_the_bytes_take_one_cycle_to_agree(self):
        testimony = run()
        assert (
            testimony.numbers["freed_while_pinned"] == 0
        )
        assert (
            testimony.numbers["freed_after_trim"] == 1
        )
