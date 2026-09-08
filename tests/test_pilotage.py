from __future__ import annotations

from keel.branchpolicy import NamingPolicy
from keel.codeowners import OwnersFile
from keel.pilotage import rehearse

OWNERS = OwnersFile.parse("src/ team-core\n")


class TestRehearsals:
    def test_a_ready_landing_hears_it_plainly(self):
        page = rehearse(
            "feature/export",
            (
                "Add the export command\n\n"
                "Because users asked for files.\n"
            ),
            ["src/export.py"],
            policy=NamingPolicy(),
            owners=OWNERS,
        )
        assert (
            "naming: feature/export: a labeled jar"
        ) in page
        assert (
            "the 2am reader thanks you in advance"
        ) in page
        assert "review: expect team-core" in page
        assert (
            "the real landing would clear today; "
            "same rules, no surprises"
        ) in page

    def test_coaching_arrives_before_the_attempt(self):
        page = rehearse(
            "mystuff",
            "fixed stuff",
            ["src/export.py", "scripts/run.sh"],
            policy=NamingPolicy(),
            owners=OWNERS,
        )
        assert (
            "naming: this WOULD bounce"
        ) in page
        assert "label your jars" in page
        assert "subject-noise" in page
        assert (
            "scripts/run.sh unclaimed; this WOULD "
            "need an owner"
        ) in page
        assert (
            "3 sentence(s) to fix before the real "
            "attempt"
        ) in page
        assert "a mentor, after it a gate" in page

    def test_absent_organs_relax_the_rehearsal(self):
        page = rehearse(
            "anything-goes",
            "Add a thing\n\nWith reasons.\n",
            ["whatever.py"],
        )
        assert "any name sails today" in page
        assert "ask whoever answers" in page
        assert "would clear today" in page
