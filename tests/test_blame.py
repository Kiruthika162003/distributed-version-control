from __future__ import annotations

import pytest

from keel.blame import blame, crossed_renames, render_blame, summarize
from keel.errors import Missing
from keel.repo import Repo


def storied_repo() -> tuple[Repo, dict[str, str]]:
    repo = Repo.init()
    first = repo.commit(
        {"app.py": b"draft line\nkept line"}, "first draft"
    )
    second = repo.commit(
        {"app.py": b"rewritten line\nkept line"}, "rewrite"
    )
    third = repo.commit(
        {"app.py": b"rewritten line\nkept line\nnew line"},
        "append",
    )
    return repo, {
        "first": first.address,
        "second": second.address,
        "third": third.address,
    }


class TestAttribution:
    def test_who_made_it_look_like_this_not_who_typed_first(self):
        repo, marks = storied_repo()
        rows = blame(repo, marks["third"], "app.py")
        by_text = {row.text: row.commit for row in rows}
        assert by_text["kept line"] == marks["first"]
        assert by_text["rewritten line"] == marks["second"]
        assert by_text["new line"] == marks["third"]

    def test_the_render_carries_numbers_and_messages(self):
        repo, marks = storied_repo()
        page = render_blame(
            blame(repo, marks["third"], "app.py")
        )
        assert "   1 rewritten line  (rewrite)" in page
        assert "   2 kept line  (first draft)" in page

    def test_the_summary_ranks_owners(self):
        repo, marks = storied_repo()
        summary = summarize(
            blame(repo, marks["third"], "app.py")
        )
        assert summary.startswith("3 line(s):")
        assert "owns 1" in summary

    def test_blame_needs_a_file_to_point_at(self):
        repo, marks = storied_repo()
        with pytest.raises(Missing):
            blame(repo, marks["third"], "ghost.py")


class TestRenames:
    def test_the_trail_survives_a_rename_and_says_so(self):
        repo = Repo.init()
        first = repo.commit(
            {"old_name.py": b"alpha\nbeta\ngamma\ndelta"},
            "born",
        )
        repo.commit(
            {"new_name.py": b"alpha\nbeta\ngamma\ndelta"},
            "moved",
        )
        tip = repo.commit(
            {"new_name.py": b"alpha\nbeta\ngamma\nEDITED"},
            "edited after move",
        )
        rows = blame(repo, tip.address, "new_name.py")
        by_text = {row.text: row.commit for row in rows}
        assert by_text["alpha"] == first.address
        crossings = crossed_renames(
            repo, tip.address, "new_name.py"
        )
        assert len(crossings) == 1
        assert "old_name.py -> new_name.py" in crossings[0]
