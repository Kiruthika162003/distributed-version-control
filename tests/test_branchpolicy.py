from __future__ import annotations

import pytest

from keel.branchpolicy import NamingPolicy
from keel.errors import Invalid
from keel.repo import Repo


class TestChecks:
    def test_labeled_jars_pass(self):
        policy = NamingPolicy()
        assert policy.check("feature/dark-mode") == (
            "feature/dark-mode: a labeled jar"
        )
        assert policy.check("fix/crash-on-empty") == (
            "fix/crash-on-empty: a labeled jar"
        )
        assert policy.check("release/2.1") == (
            "release/2.1: a labeled jar"
        )

    def test_the_uncategorized_are_sent_to_the_shelf(
        self,
    ):
        policy = NamingPolicy()
        with pytest.raises(Invalid) as caught:
            policy.check("dark-mode")
        assert "label your jars" in str(caught.value)

    def test_a_strange_category_names_the_shelf(self):
        policy = NamingPolicy()
        with pytest.raises(Invalid) as caught:
            policy.check("wip/dark-mode")
        assert "feature, fix, release" in str(
            caught.value
        )

    def test_panic_is_not_a_slug(self):
        policy = NamingPolicy()
        with pytest.raises(Invalid) as caught:
            policy.check("feature/BRANCH_FINAL_v2_REAL")
        assert "documents panic" in str(caught.value)

    def test_a_release_names_a_version(self):
        policy = NamingPolicy()
        with pytest.raises(Invalid) as caught:
            policy.check("release/soon")
        assert "promise wearing a category" in str(
            caught.value
        )

    def test_main_is_exempt_by_charter(self):
        assert NamingPolicy().check("main") == (
            "main: exempt by charter"
        )


class TestGrandfathering:
    def test_the_tolerated_pass_with_a_note(self):
        policy = NamingPolicy()
        receipt = policy.grandfather("old_stuff")
        assert "tolerated, not endorsed" in receipt
        verdict = policy.check("old_stuff")
        assert "not a blessing" in verdict

    def test_the_compliant_cannot_pad_the_list(self):
        policy = NamingPolicy()
        with pytest.raises(Invalid) as caught:
            policy.grandfather("feature/dark-mode")
        assert "should shrink" in str(caught.value)


class TestTheAudit:
    def test_the_three_columns_and_the_reminder(self):
        repo = Repo.init()
        repo.commit({"app.py": b"core\n"}, "base")
        repo.branch_from_head("feature/dark-mode")
        repo.branch_from_head("old_stuff")
        repo.branch_from_head("junkdrawer")
        policy = NamingPolicy()
        policy.grandfather("old_stuff")
        page = policy.audit(repo)
        assert page.startswith(
            "2 labeled, 1 tolerated, 1 unlabeled"
        )
        assert "main: exempt by charter" in page
        assert "old_stuff: grandfathered" in page
        assert "junkdrawer" in page
        assert "the grandfather list should shrink" in (
            page
        )
