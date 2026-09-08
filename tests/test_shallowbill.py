from __future__ import annotations

from keel.witnesses.shallowbill import run


class TestShallowbill:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_meter_at_each_stop(self):
        testimony = run()
        assert testimony.numbers["shipped_at_depth_3"] == 9
        assert (
            testimony.numbers["shipped_after_deepen_4"]
            == 21
        )
        assert (
            testimony.numbers["shipped_after_overshoot"]
            == 30
        )

    def test_the_overshoot_caps_at_the_root(self):
        testimony = run()
        assert testimony.numbers["scars_left"] == 0
        assert (
            testimony.numbers["shipped_after_overshoot"]
            == testimony.numbers["full_cost"]
        )

    def test_the_scar_crosses_the_fence(self):
        testimony = run()
        assert testimony.numbers["scar_crossed_the_fence"]
