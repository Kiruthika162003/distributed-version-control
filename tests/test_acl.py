from __future__ import annotations

import pytest

from keel.acl import AccessTable
from keel.errors import Invalid, Missing


def build() -> AccessTable:
    table = AccessTable()
    table.enroll("team-infra", "priya")
    table.enroll("team-infra", "devi")
    table.enroll("team-release", "kiruthika")
    table.grant("infra/", "team-infra")
    table.grant("*.pem", "team-infra")
    table.grant("infra/release.cfg", "team-release")
    return table


class TestGovernance:
    def test_keepers_may_write_their_paths(self):
        table = build()
        assert table.may_write(
            "priya", "infra/deploy.sh"
        )
        assert table.may_write("devi", "signing.pem")

    def test_outsiders_are_denied_with_the_fix_named(
        self,
    ):
        table = build()
        with pytest.raises(Invalid) as caught:
            table.check(
                "dana",
                ["infra/deploy.sh", "signing.pem"],
            )
        message = str(caught.value)
        assert "dana denied on 2 path(s)" in message
        assert (
            "infra/deploy.sh: membership in "
            "team-infra would have sufficed"
        ) in message
        assert "an afternoon" in message

    def test_any_guarding_team_suffices(self):
        table = build()
        assert table.may_write(
            "kiruthika", "infra/release.cfg"
        )
        assert not table.may_write(
            "kiruthika", "infra/deploy.sh"
        )

    def test_ungoverned_paths_stay_open(self):
        table = build()
        receipt = table.check(
            "dana", ["docs/guide.md", "src/app.py"]
        )
        assert receipt == (
            "dana may land all 2 path(s)"
        )


class TestRosters:
    def test_double_enrollment_counts_nobody_twice(self):
        table = build()
        with pytest.raises(Invalid):
            table.enroll("team-infra", "priya")

    def test_grants_go_to_teams_never_individuals(self):
        table = build()
        with pytest.raises(Missing) as caught:
            table.grant("keys/", "priya")
        assert "never to individuals" in str(
            caught.value
        )

    def test_retirement_changes_no_rules(self):
        table = build()
        receipt = table.retire("team-infra", "devi")
        assert "nothing else changes" in receipt
        assert not table.may_write(
            "devi", "infra/deploy.sh"
        )
        assert table.may_write(
            "priya", "infra/deploy.sh"
        )


class TestTheReport:
    def test_the_page_ends_default_open(self):
        table = build()
        page = table.report()
        assert page.startswith("2 team(s), 3 grant(s):")
        assert "team-infra: devi, priya" in page
        assert "infra/ guarded by team-infra" in page
        assert "teaches people to work in forks" in page
