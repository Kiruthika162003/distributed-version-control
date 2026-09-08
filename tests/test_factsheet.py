from __future__ import annotations

from keel.factsheet import facts
from keel.repo import Repo
from keel.tags import TagStore
from keel.witnesses import registry


def build() -> tuple[Repo, TagStore]:
    repo = Repo.init()
    repo.commit({"app.py": b"core\n"}, "one")
    repo.commit({"app.py": b"core\nmore\n"}, "two")
    repo.branch_from_head("feature")
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", repo.refs.current(), "cut")
    return repo, tags


class TestTheSheet:
    def test_numbers_and_nouns_only(self):
        repo, tags = build()
        page = facts(repo, tags=tags)
        assert page.startswith(
            "the factsheet, computed on request:"
        )
        assert "2 commit(s), 0 of them merges" in page
        assert "2 branch(es)" in page
        assert "1 file(s), 10 byte(s) at the tip" in (
            page
        )
        assert "1 tag(s) sealed" in page
        assert (
            "the difference between a factsheet and "
            "a brochure"
        ) in page

    def test_the_workshop_counts_its_instruments(self):
        repo, _tags = build()
        page = facts(repo, count_workshop=True)
        assert "organ(s) on the registry" in page
        assert (
            f"{len(registry.WITNESSES)} witness(es) "
            "on the roster"
        ) in page

    def test_the_sheet_recounts_after_changes(self):
        repo, tags = build()
        before = facts(repo, tags=tags)
        repo.commit(
            {"app.py": b"core\nmore\nnew\n"}, "three"
        )
        after = facts(repo, tags=tags)
        assert "2 commit(s)" in before
        assert "3 commit(s)" in after
