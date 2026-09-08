from __future__ import annotations

from keel.eras import chronicle
from keel.repo import Repo
from keel.tags import TagStore


def build() -> tuple[Repo, TagStore]:
    repo = Repo.init()
    files = {"engine.py": b"e0\n", "docs.md": b"d0\n"}
    repo.commit(dict(files), "founding work")
    files["engine.py"] = b"e1\n"
    first_era_end = repo.commit(
        dict(files), "engine work"
    )
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", first_era_end.address, "cut one")
    files["docs.md"] = b"d1\n"
    repo.commit(dict(files), "docs work")
    files["docs.md"] = b"d2\n"
    second_era_end = repo.commit(
        dict(files), "more docs work"
    )
    tags.place(
        "v2.0", second_era_end.address, "cut two"
    )
    files["engine.py"] = b"e2\n"
    repo.commit(dict(files), "new era begins")
    return repo, tags


class TestTheChronicle:
    def test_each_era_gets_its_protagonist(self):
        repo, tags = build()
        page = chronicle(repo, tags)
        assert page.startswith(
            "the eras, cut at the seals:"
        )
        assert (
            "the founding -> v1.0: 2 commit(s), "
            "0 merge(s), protagonist engine.py "
            "(2 touch(es))"
        ) in page
        assert (
            "v1.0 -> v2.0: 2 commit(s), 0 merge(s), "
            "protagonist docs.md (2 touch(es))"
        ) in page

    def test_the_unfinished_era_is_still_being_written(
        self,
    ):
        repo, tags = build()
        page = chronicle(repo, tags)
        assert (
            "v2.0 -> now: 1 commit(s), 0 merge(s), "
            "protagonist engine.py (1 touch(es)); "
            "still being written"
        ) in page

    def test_a_finished_history_has_no_unfinished_line(
        self,
    ):
        repo, tags = build()
        tags.place(
            "v3.0", repo.refs.current(), "cut three"
        )
        page = chronicle(repo, tags)
        assert "still being written" not in page

    def test_no_tags_is_one_nameless_era(self):
        repo = Repo.init()
        repo.commit({"a.py": b"a\n"}, "one")
        repo.commit({"a.py": b"a\nb\n"}, "two")
        tags = TagStore(graph=repo.graph)
        page = chronicle(repo, tags)
        assert page.startswith(
            "one nameless era of 2 commit(s)"
        )
        assert "offered once and not pressed" in page
