from __future__ import annotations

from keel.mergeaudit import audit, report
from keel.repo import Repo


def stage() -> tuple[Repo, str, str, str]:
    repo = Repo.init()
    a = repo.commit({"a.py": b"a\n"}, "ground")
    b = repo.commit({"a.py": b"a\nb\n"}, "trunk work")
    feature = repo.graph.create(
        tree=repo.snapshot_tree(
            {"a.py": b"a\n", "f.py": b"f\n"}
        ),
        parents=(a.address,),
        message="feature work",
    )
    return repo, a.address, b.address, feature.address


class TestFindings:
    def test_the_redundant_meeting_is_named(self):
        repo, a, b, _feature = stage()
        merged = repo.commit_with_parents(
            {"a.py": b"a\nb\n"}, "pointless", (b, a)
        )
        _count, findings = audit(repo, merged.address)
        assert [f.kind for f in findings] == [
            "redundant"
        ]
        assert (
            "a fast-forward would have said so"
        ) in findings[0].detail

    def test_the_hollow_meeting_is_worth_a_look(self):
        repo, _a, b, feature = stage()
        merged = repo.commit_with_parents(
            {"a.py": b"a\nb\n"}, "took ours whole",
            (b, feature),
        )
        _count, findings = audit(repo, merged.address)
        assert [f.kind for f in findings] == ["hollow"]
        assert (
            "the second side's work was discarded"
        ) in findings[0].detail

    def test_the_foxtrot_reverses_the_story(self):
        repo, _a, b, feature = stage()
        merged = repo.commit_with_parents(
            {
                "a.py": b"a\nb\n",
                "f.py": b"f\n",
            },
            "backwards landing",
            (feature, b),
        )
        _count, findings = audit(
            repo, merged.address, trunk_tip=b
        )
        assert [f.kind for f in findings] == ["foxtrot"]
        assert (
            "tells the story backwards"
        ) in findings[0].detail


class TestTheReport:
    def test_clean_meetings_are_counted_not_listed(self):
        repo, _a, b, feature = stage()
        merged = repo.commit_with_parents(
            {
                "a.py": b"a\nb\n",
                "f.py": b"f\n",
            },
            "a proper landing",
            (b, feature),
        )
        page = report(
            repo, merged.address, trunk_tip=b
        )
        assert page == (
            "1 meeting(s), all of them earned their "
            "commit; clean merges are counted, not "
            "listed"
        )

    def test_findings_are_itemized(self):
        repo, a, b, _feature = stage()
        merged = repo.commit_with_parents(
            {"a.py": b"a\nb\n"}, "pointless", (b, a)
        )
        page = report(repo, merged.address)
        assert page.startswith(
            "1 meeting(s), 1 finding(s):"
        )
        assert "[redundant]" in page
