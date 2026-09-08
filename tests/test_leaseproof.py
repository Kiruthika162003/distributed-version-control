from __future__ import annotations

from keel.witnesses.leaseproof import run


class TestLeaseproof:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_hammer_orphans_exactly_one_commit(self):
        testimony = run()
        assert testimony.numbers["hammer_orphans"] == 1
        assert not testimony.numbers["hammer_bounced"]

    def test_the_lease_bounces_and_orphans_none(self):
        testimony = run()
        assert testimony.numbers["lease_orphans"] == 0
        assert testimony.numbers["lease_bounced"]
