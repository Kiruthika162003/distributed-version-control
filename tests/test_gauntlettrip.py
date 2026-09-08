from __future__ import annotations

from keel.witnesses.gauntlettrip import run


class TestGauntlettrip:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_all_eleven_voices_are_heard(self):
        testimony = run()
        assert testimony.numbers["gates_alive"] == 11
        assert testimony.numbers["voices_heard"] == 11

    def test_three_gauntlets_object_together(self):
        testimony = run()
        assert testimony.numbers["gauntlets_objecting"]

    def test_the_secret_never_reaches_the_paperwork(
        self,
    ):
        testimony = run()
        assert not testimony.numbers["secret_quoted"]
