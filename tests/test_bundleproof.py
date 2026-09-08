from __future__ import annotations

from keel.witnesses.bundleproof import run


class TestBundleproof:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_two_trips_are_billed_separately(self):
        testimony = run()
        assert testimony.numbers["full_objects"] == 18
        assert testimony.numbers["thin_objects"] == 6
        assert testimony.numbers["savings"] == 12

    def test_the_stranger_machine_is_turned_away(self):
        testimony = run()
        assert testimony.numbers["stranger_refused"]
