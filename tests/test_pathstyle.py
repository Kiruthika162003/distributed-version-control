from __future__ import annotations

from keel.pathstyle import audit
from keel.repo import Repo


def tidy_repo() -> Repo:
    repo = Repo.init()
    repo.commit(
        {
            "src/parse_input.py": b"p\n",
            "src/emit_output.py": b"e\n",
            "Makefile": b"m\n",
            "docs/user-guide.md": b"g\n",
        },
        "tidy tree",
    )
    return repo


class TestInventory:
    def test_extensions_are_counted_heaviest_first(self):
        repo = tidy_repo()
        page = audit(repo, repo.refs.current())
        lines = page.splitlines()
        assert lines[0] == (
            "naming habits across 4 path(s):"
        )
        assert lines[1] == "  .py: 2"
        assert "  .md: 1" in page

    def test_extensionless_citizens_stand_in_good_standing(
        self,
    ):
        repo = tidy_repo()
        page = audit(repo, repo.refs.current())
        assert (
            "extensionless: 1, citizens in good "
            "standing"
        ) in page

    def test_a_tidy_tree_keeps_its_habits(self):
        repo = tidy_repo()
        page = audit(repo, repo.refs.current())
        assert "the habits are habits" in page


class TestFindings:
    def test_mixed_styles_ask_newcomers_to_guess(self):
        repo = Repo.init()
        repo.commit(
            {
                "src/parse_input.py": b"p\n",
                "src/emitOutput.py": b"e\n",
            },
            "mixed room",
        )
        page = audit(repo, repo.refs.current())
        assert (
            "mixed styles in src: camel and snake"
        ) in page
        assert (
            "asking every newcomer to guess"
        ) in page

    def test_one_style_per_room_is_not_flagged(self):
        repo = Repo.init()
        repo.commit(
            {
                "src/parse_input.py": b"p\n",
                "docs/user-guide.md": b"g\n",
            },
            "different rooms",
        )
        page = audit(repo, repo.refs.current())
        assert "mixed styles" not in page

    def test_invisible_names_are_a_prank(self):
        repo = Repo.init()
        repo.commit(
            {
                "src/app.py": b"a\n",
                "notes .md": b"n\n",
            },
            "the prank arrives",
        )
        page = audit(repo, repo.refs.current())
        assert "invisible:" not in page
        repo.commit(
            {
                "src/app.py": b"a\n",
                "notes .md": b"n\n",
                "trap ": b"t\n",
            },
            "a worse prank",
        )
        page = audit(repo, repo.refs.current())
        assert "invisible: 'trap '" in page
        assert "a prank on every shell" in page
