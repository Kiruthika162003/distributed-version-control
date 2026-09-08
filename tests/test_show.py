from __future__ import annotations

from keel.repo import Repo
from keel.show import show


def build() -> Repo:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"one\ntwo\n", "logo.bin": b"\x00" * 10},
        "the root",
    )
    repo.commit(
        {
            "app.py": b"one\nTWO\n",
            "logo.bin": b"\x00" * 14,
        },
        "edit text and binary",
    )
    repo.commit(
        {
            "renamed.py": b"one\nTWO\n",
            "logo.bin": b"\x00" * 14,
        },
        "move the app",
    )
    return repo


class TestTheOnePage:
    def test_hunks_show_the_line_level_story(self):
        repo = build()
        second = repo.graph.log(repo.refs.current())[1]
        page = show(repo, second.address)
        assert page.startswith("commit ")
        assert "message: edit text and binary" in page
        assert "app.py:" in page
        assert "-two" in page
        assert "+TWO" in page

    def test_binaries_are_weighed_not_hunked(self):
        repo = build()
        second = repo.graph.log(repo.refs.current())[1]
        page = show(repo, second.address)
        assert "logo.bin: 10 -> 14 byte(s) (+4)" in page
        assert "binaries do not tell stories" in page

    def test_a_move_reads_as_a_move(self):
        repo = build()
        page = show(repo, repo.refs.current())
        assert (
            "moved app.py -> renamed.py (exact)"
        ) in page
        assert "not a funeral and a birth" in page
        assert "renamed.py:" not in page

    def test_the_root_diffs_against_emptiness(self):
        repo = build()
        root = repo.graph.log(repo.refs.current())[-1]
        page = show(repo, root.address)
        assert "the root; diffed against emptiness" in (
            page
        )
        assert "+one" in page

    def test_merges_decline_their_hunks(self):
        repo = build()
        tip = repo.refs.current()
        side = repo.graph.create(
            tree=repo.graph.get(tip).tree,
            parents=(tip,),
            message="side",
        )
        merged = repo.commit_with_parents(
            {"renamed.py": b"merged\n"},
            "the meeting",
            (tip, side.address),
        )
        page = show(repo, merged.address)
        assert "a merge of" in page
        assert "hunks declined" in page
        assert "slanders the other" in page
