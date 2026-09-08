from __future__ import annotations

import pytest

from keel.codeowners import OwnersFile
from keel.errors import Invalid

OWNERS = OwnersFile.parse(
    "# routing\n"
    "src/ team-core\n"
    "src/billing/ team-billing team-core\n"
    "*.md team-docs\n"
)

TREE = [
    "src/app.py",
    "src/billing/invoice.py",
    "README.md",
    "scripts/deploy.sh",
]


class TestRouting:
    def test_later_rules_carve_exceptions(self):
        assert OWNERS.owners_of("src/app.py") == (
            "team-core",
        )
        assert OWNERS.owners_of(
            "src/billing/invoice.py"
        ) == ("team-billing", "team-core")

    def test_a_change_set_routes_to_the_union(self):
        routed = OWNERS.route(
            ["src/app.py", "README.md"]
        )
        assert routed["reviewers"] == (
            "team-core", "team-docs",
        )
        assert routed["unclaimed"] == ()

    def test_unclaimed_paths_are_reported_not_guessed(self):
        routed = OWNERS.route(["scripts/deploy.sh"])
        assert routed["reviewers"] == ()
        assert routed["unclaimed"] == ("scripts/deploy.sh",)


class TestParsing:
    def test_the_claim_everything_rule_says_nothing(self):
        with pytest.raises(Invalid) as caught:
            OwnersFile.parse("* team-everything")
        assert "the file says nothing" in str(caught.value)

    def test_the_ownerless_pattern_claims_nothing(self):
        with pytest.raises(Invalid):
            OwnersFile.parse("src/")


class TestTheAudit:
    def test_orphans_and_dead_rules_are_both_listed(self):
        stale = OwnersFile.parse(
            "src/ team-core\nvendor/ team-ghost\n"
        )
        page = stale.audit(TREE)
        assert "orphan: README.md" in page
        assert "orphan: scripts/deploy.sh" in page
        assert "dead: line 2 (vendor/)" in page
        assert "a map drawn for a different city" in page

    def test_the_true_file_audits_clean(self):
        page = OWNERS.audit(
            ["src/app.py", "README.md"]
        )
        assert page.startswith(
            "0 orphan(s) for adoption"
        )
