from __future__ import annotations

from keel.historydoctor import checkup, examine
from keel.repo import Repo

BASE = {"app.py": b"core\n"}


def healthy() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "begin the core")
    repo.commit(
        dict(BASE, **{"app.py": b"core\nserve\n"}),
        "wire the server",
    )
    return repo, repo.refs.current()


class TestFindings:
    def test_an_unfolded_fixup_is_flagged(self):
        repo, _tip = healthy()
        repo.commit(
            dict(BASE, **{"app.py": b"core\nserve\nx\n"}),
            "fixup! wire the server",
        )
        symptoms = examine(repo, repo.refs.current())
        kinds = [symptom.kind for symptom in symptoms]
        assert kinds == ["unfolded"]
        assert "outlived its review" in symptoms[0].detail

    def test_a_wip_squatter_is_flagged(self):
        repo, _tip = healthy()
        repo.commit(
            dict(BASE, **{"app.py": b"core\nserve\nx\n"}),
            "WIP: still figuring the cache out",
        )
        symptoms = examine(repo, repo.refs.current())
        assert [s.kind for s in symptoms] == ["squatter"]
        assert "now a resident" in symptoms[0].detail

    def test_a_mute_merge_is_flagged(self):
        repo, tip = healthy()
        side = repo.graph.create(
            tree=repo.graph.get(tip).tree,
            parents=(tip,),
            message="side",
        )
        merged = repo.commit_with_parents(
            dict(BASE, **{"app.py": b"core\nmerged\n"}),
            "Merge branch feature into main",
            (tip, side.address),
        )
        symptoms = examine(repo, merged.address)
        assert [s.kind for s in symptoms] == ["mute-merge"]
        assert "why the lines met" in symptoms[0].remedy

    def test_a_boulder_counts_its_paths(self):
        repo, _tip = healthy()
        wide = dict(BASE)
        for index in range(9):
            wide[f"file{index}.py"] = b"content\n"
        repo.commit(wide, "the everything commit")
        symptoms = examine(repo, repo.refs.current())
        assert [s.kind for s in symptoms] == ["boulder"]
        assert "10 path(s) in one commit" in (
            symptoms[0].detail
        )

    def test_a_stutter_run_is_caught_at_three(self):
        repo, _tip = healthy()
        text = b"core\nserve\n"
        for _step in range(3):
            text += b"again\n"
            repo.commit(
                dict(BASE, **{"app.py": text}),
                "fix the cache",
            )
        symptoms = examine(repo, repo.refs.current())
        assert [s.kind for s in symptoms] == ["stutter"]
        assert "like a video game" in symptoms[0].remedy


class TestTheCheckup:
    def test_a_healthy_story_gets_a_clean_bill(self):
        repo, tip = healthy()
        assert checkup(repo, tip) == (
            "the story checks out; the doctor has "
            "nothing to add"
        )

    def test_the_page_never_blocks(self):
        repo, _tip = healthy()
        repo.commit(
            dict(BASE, **{"app.py": b"core\nserve\nx\n"}),
            "wip",
        )
        page = checkup(repo, repo.refs.current())
        assert "none blocking" in page
        assert (
            "a to-do list for the next rewrite"
        ) in page
