from __future__ import annotations

from keel.impact import assess
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    files = {
        "api/schema.py": b"v0\n",
        "web/client.py": b"v0\n",
        "core/engine.py": b"x" * 250,
        "docs/notes.md": b"n0\n",
    }
    repo.commit(dict(files), "found")
    files["api/schema.py"] = b"v1\n"
    files["web/client.py"] = b"v1\n"
    repo.commit(dict(files), "round one")
    files["api/schema.py"] = b"v2\n"
    repo.commit(dict(files), "schema alone")
    files["api/schema.py"] = b"v3\n"
    files["web/client.py"] = b"v3\n"
    repo.commit(dict(files), "round two")
    files["web/client.py"] = b"v4\n"
    repo.commit(dict(files), "client alone")
    return repo, repo.refs.current()


class TestAssessments:
    def test_a_half_touched_marriage_is_woken(self):
        repo, tip = build()
        page = assess(repo, tip, ["api/schema.py"])
        assert (
            "woken: api/schema.py is touched but "
            "web/client.py is not"
        ) in page
        assert "(75%)" in page
        assert (
            "the follow-up commit everyone pretends "
            "is unrelated"
        ) in page

    def test_a_marriage_edited_together_is_kept(self):
        repo, tip = build()
        page = assess(
            repo,
            tip,
            ["api/schema.py", "web/client.py"],
        )
        assert "kept:" in page
        assert "woken:" not in page
        assert (
            "which is what the marriage wants"
        ) in page

    def test_hot_ground_carries_its_prescription(self):
        repo, tip = build()
        page = assess(repo, tip, ["core/engine.py"])
        assert (
            "hot ground: core/engine.py"
        ) in page
        assert "prescription" in page

    def test_the_lonely_change_walks_alone(self):
        repo, tip = build()
        page = assess(repo, tip, ["docs/notes.md"])
        assert "1 path(s) wake nothing" in page
        assert "this change walks alone" in page

    def test_findings_size_the_review(self):
        repo, tip = build()
        page = assess(
            repo,
            tip,
            ["api/schema.py", "core/engine.py"],
        )
        assert (
            "hot ground: api/schema.py (4 touch(es)"
        ) in page
        assert (
            "3 finding(s); size the review by the "
            "neighborhood, not the diff"
        ) in page
