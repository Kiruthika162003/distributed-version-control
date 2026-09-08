from __future__ import annotations

from keel.portability import audit, audit_paths
from keel.repo import Repo


class TestCaseCollisions:
    def test_two_cases_of_one_name_are_an_error_here(
        self,
    ):
        findings = audit_paths(
            ["src/App.py", "src/app.py", "src/lib.py"]
        )
        assert len(findings) == 1
        assert (
            "src/App.py and src/app.py" in findings[0]
        )
        assert "loses somebody's work" in findings[0]

    def test_distinct_names_do_not_collide(self):
        assert (
            audit_paths(["src/app.py", "src/apps.py"])
            == []
        )


class TestReservedNames:
    def test_windows_reserved_segments_are_named(self):
        findings = audit_paths(["drivers/con/init.py"])
        assert len(findings) == 1
        assert "cannot exist on Windows" in findings[0]

    def test_the_extension_does_not_launder_the_name(
        self,
    ):
        findings = audit_paths(["logs/aux.txt"])
        assert len(findings) == 1
        assert "aux.txt" in findings[0]

    def test_containing_is_not_being(self):
        assert audit_paths(["src/console.py"]) == []
        assert audit_paths(["auxiliary/tools.py"]) == []


class TestLongPaths:
    def test_the_budget_is_stated_in_the_finding(self):
        deep = "a/" * 95 + "leaf.py"
        findings = audit_paths([deep])
        assert len(findings) == 1
        assert "against the budget of 180" in findings[0]

    def test_a_path_at_the_limit_passes(self):
        exactly = "a/" * 85 + "leaf.puny"
        assert len(exactly) <= 180
        assert audit_paths([exactly]) == []


class TestTheAudit:
    def test_a_clean_tree_travels_well(self):
        repo = Repo.init()
        repo.commit(
            {"src/app.py": b"core\n"}, "clean tree"
        )
        page = audit(repo, repo.refs.current())
        assert page == (
            "1 path(s) audited; this tree travels well"
        )

    def test_all_families_report_in_one_trip(self):
        repo = Repo.init()
        repo.commit(
            {
                "src/App.py": b"a\n",
                "src/app.py": b"b\n",
                "logs/aux.txt": b"c\n",
            },
            "trouble everywhere",
        )
        page = audit(repo, repo.refs.current())
        assert page.startswith(
            "2 portability finding(s) in 3 path(s)"
        )
        assert "case collision" in page
        assert "reserved name" in page
