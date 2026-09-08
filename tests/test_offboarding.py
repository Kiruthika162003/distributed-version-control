from __future__ import annotations

from keel.acl import AccessTable
from keel.filelocks import LockOffice
from keel.offboarding import manifest
from keel.reviewrotation import Wheel


def held_world() -> tuple[LockOffice, AccessTable, Wheel]:
    locks = LockOffice()
    locks.take(
        "design.sketch", "priya", "reworking the header"
    )
    locks.take("schema.bin", "devi", "migration")
    access = AccessTable()
    access.enroll("team-infra", "priya")
    access.grant("infra/", "team-infra")
    access.enroll("team-docs", "priya")
    wheel = Wheel()
    wheel.enroll("team-infra", "priya")
    wheel.enroll("team-infra", "devi")
    wheel.assign("team-infra")
    return locks, access, wheel


class TestTheManifest:
    def test_every_holding_names_its_handover(self):
        locks, access, wheel = held_world()
        page = manifest(
            "priya",
            locks=locks,
            access=access,
            wheel=wheel,
        )
        assert page.startswith(
            "offboarding priya: 4 holding(s)"
        )
        assert (
            "lock on design.sketch (reworking the "
            "header)"
        ) in page
        assert "steals it in capitals" in page
        assert (
            "seat on team-infra guarding infra/"
        ) in page
        assert "seat on team-docs; retire it" in page
        assert (
            "rotation seat on the team-infra wheel "
            "with 1 assignment(s)"
        ) in page
        assert "skips a ghost forever" in page

    def test_other_names_holdings_stay_out(self):
        locks, access, wheel = held_world()
        page = manifest(
            "priya",
            locks=locks,
            access=access,
            wheel=wheel,
        )
        assert "schema.bin" not in page

    def test_the_empty_manifest_is_a_compliment(self):
        locks, access, wheel = held_world()
        page = manifest(
            "dana",
            locks=locks,
            access=access,
            wheel=wheel,
        )
        assert page == (
            "dana leaves nothing jammed; either luck, "
            "or the sign of someone who released as "
            "they went"
        )

    def test_absent_organs_simply_contribute_nothing(
        self,
    ):
        locks, _access, _wheel = held_world()
        page = manifest("priya", locks=locks)
        assert page.startswith(
            "offboarding priya: 1 holding(s)"
        )
