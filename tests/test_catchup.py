from __future__ import annotations

import pytest

from keel.catchup import catch_up
from keel.errors import Missing
from keel.repo import Repo
from keel.tags import TagStore


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    anchor = repo.commit(
        {"src/app.py": b"core\n", "docs.md": b"d\n"},
        "before the holiday",
    )
    repo.commit(
        {
            "src/app.py": b"core\nserve\n",
            "docs.md": b"d\n",
        },
        "wire the server",
    )
    repo.commit(
        {
            "src/app.py": b"core\nserve\nlog\n",
            "docs.md": b"d\n",
        },
        "log the requests",
    )
    return repo, anchor.address


class TestTheCatchUp:
    def test_the_page_triages_in_order(self):
        repo, anchor = build()
        page = catch_up(repo, anchor)
        assert page.startswith(
            f"since {anchor[:8]}: 2 commit(s), sized "
            "for one coffee"
        )
        assert "where the change landed" in page
        assert (
            "recency being relevance after an absence"
        ) in page
        lines = page.splitlines()
        subjects = [
            line
            for line in lines
            if "log the requests" in line
            or "wire the server" in line
        ]
        assert "log the requests" in subjects[0]

    def test_new_branches_and_seals_are_reported(self):
        repo, anchor = build()
        repo.branch_from_head("feature/audit")
        tags = TagStore(graph=repo.graph)
        tags.place(
            "v2.0", repo.refs.current(), "the cut"
        )
        page = catch_up(
            repo,
            anchor,
            known_branches={"main"},
            tags=tags,
        )
        assert (
            "branches that appeared while you were "
            "gone: feature/audit"
        ) in page
        assert "sealed while you were gone: v2.0" in (
            page
        )

    def test_no_new_conversations_says_so(self):
        repo, anchor = build()
        page = catch_up(
            repo, anchor, known_branches={"main"}
        )
        assert (
            "the conversations are the ones you left"
        ) in page

    def test_the_present_gets_the_shortest_page(self):
        repo, _anchor = build()
        page = catch_up(repo, repo.refs.current())
        assert page == (
            "nothing happened; you were never really "
            "gone"
        )

    def test_a_wrong_anchor_is_refused(self):
        repo, _anchor = build()
        with pytest.raises(Missing) as caught:
            catch_up(repo, "0" * 20)
        assert "confidently wrong about everything" in (
            str(caught.value)
        )
