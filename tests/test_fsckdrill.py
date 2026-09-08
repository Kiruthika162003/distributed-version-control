from __future__ import annotations

from keel.witnesses.fsckdrill import run


class TestFsckdrill:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_both_injuries_are_found(self):
        testimony = run()
        assert testimony.numbers["findings_reported"] == 2

    def test_blast_radius_orders_the_report(self):
        testimony = run()
        assert testimony.numbers["links_listed_first"]

    def test_exhaust_is_not_an_alarm(self):
        testimony = run()
        assert testimony.numbers["healthy_clean"]
        assert testimony.numbers["dangling_reported"]
